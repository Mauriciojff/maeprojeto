# ============================================
# WHATSAPP/CONVERSATION.PY — Fluxo automatizado da conversa
# ============================================

import json
import logging
import re
from datetime import date, timedelta

from ..database import db
from ..database.models import Cliente, Servico, Agendamento, Faturamento
from ..database.wpp_models import (
    MensagemRecebida, LogAuditoria
)
from ..utils.helpers import telefone_limpo, formatar_moeda, formatar_data_br
from ..utils.security import is_valid_email, sanitize_input

from . import api_client, session_state as sess, notifier
from .agenda_helpers import (
    servicos_para_mensagem, horarios_para_mensagem, datas_para_mensagem,
    interpretar_data_escolhida, formatar_resumo_agendamento,
    criar_agendamento, agendamentos_do_cliente_ativos,
    agendamentos_formatados, lista_servicos_ativos
)

logger = logging.getLogger('agenda_mae')

# ============================================
# MENSAGENS DO MENU
# ============================================

MENU_INICIAL = (
    "Olá! 👋 Bem-vindo(a) à *Agenda da Mãe* 💅\n\n"
    "Como posso ajudar?\n\n"
    "1️⃣ *Cadastro* — Criar ou atualizar seu cadastro\n"
    "2️⃣ *Agendar* — Agendar um atendimento\n"
    "3️⃣ *Consultar* — Ver meus agendamentos\n"
    "4️⃣ *Remarcar* — Remarcar um atendimento\n"
    "5️⃣ *Cancelar* — Cancelar um atendimento\n"
    "6️⃣ *Serviços* — Ver serviços e preços\n"
    "7️⃣ *Falar com a adm* — Chamar a administradora\n\n"
    "Responda com o *número* da opção desejada."
)

MENU_ADMIN = (
    "*MENU ADMINISTRADORA* 🛠\n\n"
    "A1️⃣ Agenda do dia\n"
    "A2️⃣ Próximos agendamentos\n"
    "A3️⃣ Agen. pendentes (confirmar)\n"
    "A4️⃣ Concluir atendimento\n"
    "A5️⃣ Consultar clientes\n"
    "A6️⃣ Faturamento\n"
    "A7️⃣ Listar serviços\n"
    "A8️⃣ Cadastrar serviço\n"
    "A9️⃣ Editar serviço\n"
    "A0️⃣ Desativar serviço\n"
    "🔙 *voltar* para o menu principal"
)


OPCOES_MENU = {
    '1': 'cadastro',
    '2': 'agendar',
    '3': 'consultar',
    '4': 'remarcar',
    '5': 'cancelar',
    '6': 'servicos',
    '7': 'falar_admin',
}


# ============================================
# NORMALIZAÇÃO E PERSISTÊNCIA
# ============================================

def _normalizar(texto):
    """Normaliza texto para comparação (minúsculas, sem acentos)."""
    if not texto:
        return ''
    mapa = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u', 'ç': 'c', 'ñ': 'n',
    }
    t = texto.lower()
    t = t.translate(str.maketrans(mapa))
    return re.sub(r'\s+', ' ', t).strip()[:200]


def _persistir_recebida(telefone, texto, mensagem_id, nome_contato, tipo):
    """Persiste mensagem recebida (LGPD: sanitizada, apenas o necessário)."""
    try:
        if mensagem_id:
            existente = MensagemRecebida.query.filter_by(
                whatsapp_id=mensagem_id).first()
            if existente:
                return
        corpo = sanitize_input(texto or '', 1000)
        msg = MensagemRecebida(
            whatsapp_id=mensagem_id,
            telefone=telefone,
            nome_contato=sanitize_input(nome_contato or '', 150),
            corpo=corpo or None,
            tipo=tipo or 'text',
            texto_normalizado=_normalizar(corpo) or None,
        )
        db.session.add(msg)
        sess.obter_sessao(telefone, criar=True)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao persistir mensagem recebida: {str(e)[:200]}")


def _enviar(telefone, mensagem):
    """Envia mensagem via API WhatsApp."""
    api_client.enviar_texto(telefone, mensagem)



# ============================================
# PROCESSAMENTO PRINCIPAL (entrada do webhook)
# ============================================

def processar_mensagem(telefone, texto_bruto, mensagem_id=None,
                       nome_contato=None, tipo='text'):
    """
    Processa uma mensagem recebida do WhatsApp (ponto de entrada do webhook).
    Persiste a mensagem, sanitiza e roteia conforme o estado da conversa.
    """
    _persistir_recebida(telefone, texto_bruto, mensagem_id, nome_contato, tipo)

    texto = (texto_bruto or '').strip()
    normalizado = _normalizar(texto)
    estado = sess.obter_estado(telefone)

    # Tratamentos globais (voltar / menu)
    if normalizado in ('menu', 'inicio', 'voltar', 'sair', 'comecar'):
        _enviar(telefone, MENU_INICIAL)
        sess.voltar_ao_menu(telefone)
        return

    # Acesso ao painel administrativo (apenas para números autorizados)
    if normalizado in ('admin', 'adm', 'gestao', 'painel'):
        _entrar_admin(telefone)
        return

    # Roteia pelo estado atual da conversa
    if estado == sess.ESTADO_MENU:
        _rotear_menu(telefone, normalizado)
    elif estado == sess.ESTADO_CADASTRO_NOME:
        _fluxo_cadastro_nome(telefone, texto)
    elif estado == sess.ESTADO_CADASTRO_EMAIL:
        _fluxo_cadastro_email(telefone, texto)
    elif estado == sess.ESTADO_CADASTRO_CONFIRMAR_DADOS:
        _fluxo_cadastro_confirmar(telefone, normalizado)
    elif estado == sess.ESTADO_AGENDAR_SERVICO:
        _fluxo_agendar_servico(telefone, normalizado)
    elif estado == sess.ESTADO_AGENDAR_DATA:
        _fluxo_agendar_data(telefone, normalizado)
    elif estado == sess.ESTADO_AGENDAR_HORARIO:
        _fluxo_agendar_horario(telefone, normalizado)
    elif estado == sess.ESTADO_AGENDAR_CONFIRMAR:
        _fluxo_agendar_confirmar(telefone, normalizado)
    elif estado == sess.ESTADO_CONSULTAR_AGENDA:
        _fluxo_consultar(telefone)
    elif estado == sess.ESTADO_CANCELAR_SELECAO:
        _fluxo_cancelar_selecao(telefone, normalizado)
    elif estado == sess.ESTADO_CANCELAR_CONFIRMAR:
        _fluxo_cancelar_confirmar(telefone, normalizado)
    elif estado == sess.ESTADO_REMARCAR_SELECAO:
        _fluxo_remarcar_selecao(telefone, normalizado)
    elif estado == sess.ESTADO_REMARCAR_SERVICO:
        _fluxo_remarcar_servico(telefone, normalizado)
    elif estado == sess.ESTADO_REMARCAR_DATA:
        _fluxo_remarcar_data(telefone, normalizado)
    elif estado == sess.ESTADO_REMARCAR_HORARIO:
        _fluxo_remarcar_horario(telefone, normalizado)
    elif estado == sess.ESTADO_REMARCAR_CONFIRMAR:
        _fluxo_remarcar_confirmar(telefone, normalizado)
    elif estado == 'admin':
        _tratar_admin(telefone, normalizado, estado)
    elif estado == 'admin_confirmar_pendente':
        _admin_confirmar_pendente(telefone, normalizado)
    elif estado == 'admin_concluir_selecao':
        _admin_concluir_selecao(telefone, normalizado)
    elif estado == 'admin_desativar_servico':
        _admin_desativar_servico_confirma(telefone, normalizado)
    else:
        _enviar(telefone, MENU_INICIAL)
        sess.voltar_ao_menu(telefone)



# ============================================
# HELPERS DE CLIENTE
# ============================================

def _cliente_por_telefone(telefone):
    """Busca cliente pelo telefone (formato limpo)."""
    limpo = telefone_limpo(telefone)
    if not limpo:
        return None
    return Cliente.query.filter(
        Cliente.telefone == limpo
    ).filter_by(ativo=True).first()


def _cliente_por_telefone_ou_criar(telefone, nome=None):
    """
    Busca cliente pelo telefone ou cria um novo. Evita cadastro duplicado.
    """
    limpo = telefone_limpo(telefone)
    cliente = _cliente_por_telefone(limpo)
    if cliente:
        return cliente
    cliente = Cliente(
        nome=sanitize_input((nome or 'Cliente WhatsApp').strip()[:150]) or 'Cliente WhatsApp',
        telefone=limpo or None,
    )
    db.session.add(cliente)
    db.session.commit()
    logger.info(f"Cliente criado automaticamente via WhatsApp: tel={limpo}")
    return cliente


def _registrar_log(telefone, acao, detalhe='', ip=None):
    """Registra um log de auditoria (sem dados sensíveis)."""
    try:
        db.session.add(LogAuditoria(
            telefone=telefone,
            acao=acao,
            detalhe=sanitize_input(detalhe or '', 500) or None,
            ip=ip
        ))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao registrar log: {str(e)[:200]}")


# ============================================
# ROTEAMENTO DO MENU
# ============================================

def _rotear_menu(telefone, normalizado):
    """Roteia a escolha do menu principal."""
    if normalizado in ('adm', 'gestao', 'painel'):
        _entrar_admin(telefone)
        return

    acao = OPCOES_MENU.get(normalizado)
    if acao == 'cadastro':
        _iniciar_cadastro(telefone)
    elif acao == 'agendar':
        _iniciar_agendamento(telefone)
    elif acao == 'consultar':
        _fluxo_consultar(telefone)
    elif acao == 'remarcar':
        _fluxo_remarcar_selecao(telefone, None)
    elif acao == 'cancelar':
        _fluxo_cancelar_selecao(telefone, None)
    elif acao == 'servicos' or normalizado in ('servicos', 'servico', 'precos', 'preco', 'catalogo'):
        _enviar(telefone, servicos_para_mensagem())
    elif acao == 'falar_admin' or normalizado in ('falar', 'humano'):
        _fluxo_falar_admin(telefone)
    else:
        _enviar(telefone,
                "Desculpe, não entendi. Responda com o *número* da opção desejada:\n\n"
                + MENU_INICIAL)



# ============================================
# FLUXO DE CADASTRO
# ============================================

def _iniciar_cadastro(telefone):
    """Inicia o fluxo de cadastro/atualização de dados."""
    cliente = _cliente_por_telefone(telefone)
    if cliente:
        _enviar(
            telefone,
            f"Você já está cadastrado(a) como *{cliente.nome}*.\n"
            "Vamos atualizar seus dados, ok?\n\n"
            "Para começar, digite seu *nome completo*:"
        )
    else:
        _enviar(
            telefone,
            "Vamos fazer seu *cadastro*! 📝\n\n"
            "Primeiro, digite seu *nome completo*:"
        )
    sess.definir_estado(telefone, sess.ESTADO_CADASTRO_NOME,
                        contexto={'cadastro': {}})


def _fluxo_cadastro_nome(telefone, texto):
    """Recebe o nome completo do cliente."""
    nome = (texto or '').strip()
    if len(nome) < 2:
        _enviar(telefone,
                "Esse nome parece muito curto. Digite seu *nome completo*, por favor:")
        return

    nome_limpo = sanitize_input(nome, 150)
    contexto = sess.obter_contexto(telefone)
    contexto.setdefault('cadastro', {})['nome'] = nome_limpo
    sessao = sess.obter_sessao(telefone)
    sessao.contexto = json.dumps(contexto, ensure_ascii=False)
    db.session.commit()

    _enviar(
        telefone,
        f"Prazer, *{nome_limpo}*! 😊\n\n"
        "Seu *telefone* já foi identificado automaticamente na conversa.\n\n"
        "Agora, se quiser, informe seu *e-mail* (opcional).\n"
        "Ou responda *pular* para continuar sem e-mail:"
    )
    sess.definir_estado(telefone, sess.ESTADO_CADASTRO_EMAIL)


def _fluxo_cadastro_email(telefone, texto):
    """Recebe o e-mail opcional do cliente."""
    texto = (texto or '').strip()
    email = None

    if texto.lower() in ('pular', 'skip', 'nao', 'nao quero', 'sem email', '0'):
        email = None
    else:
        email_bruto = sanitize_input(texto, 150)
        if not email_bruto or not is_valid_email(email_bruto):
            _enviar(telefone,
                    "E-mail inválido. Digite um e-mail válido ou responda *pular*:")
            return
        email = email_bruto.lower()

    contexto = sess.obter_contexto(telefone)
    contexto.setdefault('cadastro', {})['email'] = email
    contexto['cadastro']['telefone'] = telefone_limpo(telefone)
    sessao = sess.obter_sessao(telefone)
    sessao.contexto = json.dumps(contexto, ensure_ascii=False)
    db.session.commit()

    _confirmar_dados_cadastro(telefone, contexto['cadastro'])


def _confirmar_dados_cadastro(telefone, dados):
    """Mostra os dados para confirmação antes de salvar."""
    email = dados.get('email') or 'não informado'
    _enviar(
        telefone,
        "*Confirme seus dados:*\n\n"
        f"👤 Nome: *{dados.get('nome', '')}*\n"
        f"📱 Telefone: *{dados.get('telefone', '')}*\n"
        f"📧 E-mail: *{email}*\n\n"
        "Digite *1* para confirmar, ou *2* para corrigir:"
    )
    sess.definir_estado(telefone, sess.ESTADO_CADASTRO_CONFIRMAR_DADOS)


def _fluxo_cadastro_confirmar(telefone, normalizado):
    """Confirma/recusa o cadastro e salva no banco."""
    contexto = sess.obter_contexto(telefone)
    dados = contexto.get('cadastro', {})
    nome = dados.get('nome', '')
    email = dados.get('email')

    if normalizado in ('1', 'sim', 'confirmar', 'ok', 'confirmo'):
        cliente = _cliente_por_telefone(telefone)
        if not cliente:
            cliente = Cliente(
                nome=nome or 'Cliente WhatsApp',
                telefone=telefone_limpo(telefone),
                email=email or None,
            )
            db.session.add(cliente)
        else:
            cliente.nome = nome or cliente.nome
            cliente.email = email or cliente.email
            cliente.ativo = True
        db.session.commit()

        _registrar_log(telefone, 'cadastro_confirmado')
        _enviar(
            telefone,
            f"✅ Cadastro *confirmado*! Bem-vindo(a), *{cliente.nome}*!\n\n"
            "Como posso ajudar?\n\n" + MENU_INICIAL
        )
        sess.voltar_ao_menu(telefone)
    elif normalizado in ('2', 'corrigir', 'nao', 'editar'):
        _enviar(telefone,
                "Tudo bem! Digite novamente seu *nome completo*:")
        sess.definir_estado(telefone, sess.ESTADO_CADASTRO_NOME,
                            contexto={'cadastro': {}})
    else:
        _enviar(telefone,
                "Responda *1* para confirmar ou *2* para corrigir:")



# ============================================
# FLUXO DE AGENDAMENTO
# ============================================

def _iniciar_agendamento(telefone):
    """Inicia o fluxo de agendamento de atendimento."""
    cliente = _cliente_por_telefone(telefone)
    if not cliente:
        _enviar(
            telefone,
            "Para agendar, primeiro preciso do seu *cadastro*. 📝\n\n"
            "Vamos fazer agora.\nDigite seu *nome completo*:"
        )
        sess.definir_estado(telefone, sess.ESTADO_CADASTRO_NOME,
                            contexto={'cadastro': {}})
        return

    _enviar(telefone, servicos_para_mensagem())
    sess.definir_estado(telefone, sess.ESTADO_AGENDAR_SERVICO,
                        contexto={'agendamento': {}})


def _parse_int(texto):
    """Converte texto em inteiro, retornando None se inválido."""
    try:
        return int(texto)
    except (ValueError, TypeError):
        return None


def _fluxo_agendar_servico(telefone, normalizado):
    """Recebe a escolha do serviço e mostra as datas disponíveis."""
    servicos = lista_servicos_ativos()
    servico = None
    for i, s in enumerate(servicos, start=1):
        if normalizado == str(i) or normalizado == str(s.id):
            servico = s
            break

    if not servico:
        _enviar(telefone, "Escolha um serviço válido. " + servicos_para_mensagem())
        return

    contexto = sess.obter_contexto(telefone)
    contexto.setdefault('agendamento', {})['servico_id'] = servico.id
    sessao = sess.obter_sessao(telefone)
    sessao.contexto = json.dumps(contexto, ensure_ascii=False)
    db.session.commit()

    _enviar(telefone, datas_para_mensagem(servico.id))
    sess.definir_estado(telefone, sess.ESTADO_AGENDAR_DATA)


def _fluxo_agendar_data(telefone, normalizado):
    """Recebe a data escolhida e mostra os horários livres."""
    indice = _parse_int(normalizado)
    contexto = sess.obter_contexto(telefone)
    servico_id = contexto.get('agendamento', {}).get('servico_id')

    data = interpretar_data_escolhida(servico_id, indice) if indice else None
    if not data:
        _enviar(telefone, "Escolha uma data válida. " +
                datas_para_mensagem(servico_id))
        return

    contexto['agendamento']['data'] = data.isoformat()
    sessao = sess.obter_sessao(telefone)
    sessao.contexto = json.dumps(contexto, ensure_ascii=False)
    db.session.commit()

    _enviar(telefone, horarios_para_mensagem(data, servico_id))
    sess.definir_estado(telefone, sess.ESTADO_AGENDAR_HORARIO)



def _fluxo_agendar_horario(telefone, normalizado):
    """Recebe o horário escolhido e pede confirmação."""
    indice = _parse_int(normalizado)
    contexto = sess.obter_contexto(telefone)
    ag = contexto.get('agendamento', {})
    servico_id = ag.get('servico_id')
    data_iso = ag.get('data')

    try:
        data = date.fromisoformat(data_iso)
    except (ValueError, TypeError):
        _enviar(telefone, "Houve um erro. Vamos recomeçar o agendamento.")
        sess.voltar_ao_menu(telefone)
        return

    from .agenda_helpers import horarios_livres
    livres = horarios_livres(data, servico_id)
    if not indice or not (1 <= indice <= len(livres)):
        _enviar(telefone, "Escolha um horário válido. " +
                horarios_para_mensagem(data, servico_id))
        return

    horario = livres[indice - 1]
    contexto['agendamento']['horario'] = horario

    servico = Servico.query.get(servico_id)
    preco = formatar_moeda(servico.preco) if servico else '-'
    sessao = sess.obter_sessao(telefone)
    sessao.contexto = json.dumps(contexto, ensure_ascii=False)
    db.session.commit()

    _enviar(
        telefone,
        "*Confirme seu agendamento:*\n\n"
        f"💅 Serviço: *{servico.nome if servico else 'Serviço'}*\n"
        f"📅 Data: *{formatar_data_br(data)}*\n"
        f"⏰ Horário: *{horario}*\n"
        f"💰 Preço: *{preco}*\n\n"
        "Digite *1* para confirmar ou *2* para cancelar:"
    )
    sess.definir_estado(telefone, sess.ESTADO_AGENDAR_CONFIRMAR)


def _fluxo_agendar_confirmar(telefone, normalizado):
    """Confirma ou cancela o agendamento criado."""
    cliente = _cliente_por_telefone(telefone)
    if not cliente:
        _enviar(telefone, "Cliente não encontrado. Faça o cadastro primeiro.")
        sess.voltar_ao_menu(telefone)
        return

    if normalizado in ('1', 'sim', 'confirmar', 'ok', 'confirmo'):
        contexto = sess.obter_contexto(telefone)
        ag = contexto.get('agendamento', {})
        servico_id = ag.get('servico_id')
        horario = ag.get('horario')
        try:
            data = date.fromisoformat(ag.get('data'))
        except (ValueError, TypeError):
            _enviar(telefone, "Dados do agendamento inválidos. Tente novamente.")
            sess.voltar_ao_menu(telefone)
            return

        novo, erro = criar_agendamento(
            telefone, cliente, servico_id, data, horario, origem='whatsapp'
        )
        if novo:
            _registrar_log(telefone, 'agendamento_criado')
            _enviar(telefone, "✅ *Agendamento confirmado!*\n\n" +
                    formatar_resumo_agendamento(novo) +
                    "\n\nA administradora foi notificada.")
            notifier.notificar_admin(
                f"📌 *Novo agendamento*\n{formatar_resumo_agendamento(novo)}"
            )
        else:
            _enviar(telefone, f"❌ Não foi possível agendar: {erro}\n\n" +
                    "Escolha outro horário/dia. Digite *menu* para recomeçar.")
        sess.voltar_ao_menu(telefone)
    elif normalizado in ('2', 'nao', 'cancelar'):
        _enviar(telefone,
                "Agendamento *cancelado* sem efeito. 🙂\n\n" + MENU_INICIAL)
        sess.voltar_ao_menu(telefone)
    else:
        _enviar(telefone, "Responda *1* para confirmar ou *2* para cancelar:")



# ============================================
# CONSULTAR AGENDAMENTOS
# ============================================

def _fluxo_consultar(telefone):
    """Mostra os agendamentos futuros do cliente."""
    cliente = _cliente_por_telefone(telefone)
    if not cliente:
        _enviar(telefone,
                "Você ainda não tem cadastro. Faça o *cadastro* para ver seus agendamentos.")
        sess.voltar_ao_menu(telefone)
        return

    ags = agendamentos_do_cliente_ativos(cliente.id)
    _enviar(telefone, agendamentos_formatados(ags) +
            "\n\nDigite *menu* para voltar.")
    sess.voltar_ao_menu(telefone)


# ============================================
# CANCELAR AGENDAMENTO
# ============================================

def _fluxo_cancelar_selecao(telefone, normalizado):
    """Mostra os agendamentos do cliente para escolher o que cancelar."""
    cliente = _cliente_por_telefone(telefone)
    if not cliente:
        _enviar(telefone, "Você ainda não tem cadastro. Faça o *cadastro* primeiro.")
        sess.voltar_ao_menu(telefone)
        return

    ags = agendamentos_do_cliente_ativos(cliente.id)
    if not ags:
        _enviar(telefone, "Você não tem agendamentos futuros para cancelar.\n\n" +
                MENU_INICIAL)
        sess.voltar_ao_menu(telefone)
        return

    # Se o usuário já escolheu um número, armazena e pede confirmação
    indice = _parse_int(normalizado)
    if indice and 1 <= indice <= len(ags):
        ag_escolhido = ags[indice - 1]
        contexto = sess.obter_contexto(telefone)
        contexto.setdefault('cancelar', {})['agendamento_id'] = ag_escolhido.id
        sessao = sess.obter_sessao(telefone)
        sessao.contexto = json.dumps(contexto, ensure_ascii=False)
        sessao.estado = sess.ESTADO_CANCELAR_CONFIRMAR
        db.session.commit()
        servico = ag_escolhido.servico.nome if ag_escolhido.servico else 'Serviço'
        _enviar(
            telefone,
            f"Confirmar cancelamento de:\n"
            f"*{servico}* em {formatar_data_br(ag_escolhido.data)} às {ag_escolhido.horario}?\n\n"
            "Digite *1* para confirmar ou *2* para não cancelar:"
        )
        return

    linhas = ['*Qual agendamento você quer cancelar?*\n']
    for i, ag in enumerate(ags, start=1):
        servico = ag.servico.nome if ag.servico else 'Serviço'
        linhas.append(f"{i} - {servico} ({formatar_data_br(ag.data)} às {ag.horario})")
    linhas.append('\nResponda com o *número*, ou *menu* para cancelar.')
    _enviar(telefone, '\n'.join(linhas))

    sess.definir_estado(telefone, sess.ESTADO_CANCELAR_SELECAO,
                        contexto={'cancelar': {}})


def _fluxo_cancelar_confirmar(telefone, normalizado):
    """Confirma o cancelamento do agendamento escolhido."""
    contexto = sess.obter_contexto(telefone)
    ag_id = contexto.get('cancelar', {}).get('agendamento_id')

    if not ag_id:
        _enviar(telefone, "Erro ao identificar o agendamento. Tente de novo.")
        sess.voltar_ao_menu(telefone)
        return

    ag = Agendamento.query.get(ag_id)

    if normalizado in ('1', 'sim', 'sim cancelar', 'cancelar', 'ok', 'confirmar'):
        if ag and ag.status in ('pendente', 'confirmada'):
            ag.status = 'cancelada'
            db.session.commit()
            _registrar_log(telefone, 'agendamento_cancelado', f'id={ag_id}')
            _enviar(telefone,
                    "✅ Agendamento *cancelado* com sucesso!\n\n" + MENU_INICIAL)
            notifier.notificar_admin(
                f"❌ *Agendamento cancelado*\n{formatar_resumo_agendamento(ag)}"
            )
        else:
            _enviar(telefone,
                    "Esse agendamento não pode ser cancelado (já foi concluído ou cancelado).")
        sess.voltar_ao_menu(telefone)
    elif normalizado in ('2', 'nao', 'voltar'):
        _enviar(telefone, "Cancelamento *desfeito*. 🙂\n\n" + MENU_INICIAL)
        sess.voltar_ao_menu(telefone)
    else:
        _enviar(telefone,
                "Responda *1* para confirmar cancelamento ou *2* para não cancelar:")


def _fluxo_falar_admin(telefone):
    """Informa o cliente que a administradora foi avisada."""
    _enviar(
        telefone,
        "📣 A *administradora* foi avisada!\n"
        "Em breve ela entrará em contato com você por aqui. 🙂\n\n" +
        MENU_INICIAL
    )
    notifier.notificar_admin(
        f"📣 Um cliente quer falar com você: *{telefone}*"
    )
    _registrar_log(telefone, 'solicitou_falar_admin')
    sess.voltar_ao_menu(telefone)



# ============================================
# REMARCAR AGENDAMENTO
# ============================================

def _fluxo_remarcar_selecao(telefone, normalizado):
    """Lista agendamentos do cliente para escolher o que remarcar."""
    cliente = _cliente_por_telefone(telefone)
    if not cliente:
        _enviar(telefone, "Você ainda não tem cadastro. Faça o *cadastro* primeiro.")
        sess.voltar_ao_menu(telefone)
        return

    ags = agendamentos_do_cliente_ativos(cliente.id)
    if not ags:
        _enviar(telefone, "Você não tem agendamentos futuros para remarcar.\n\n" +
                MENU_INICIAL)
        sess.voltar_ao_menu(telefone)
        return

    # Se já escolheu um número, guarda o agendamento a remarcar
    indice = _parse_int(normalizado)
    if indice and 1 <= indice <= len(ags):
        ag_escolhido = ags[indice - 1]
        contexto = sess.obter_contexto(telefone)
        contexto.setdefault('remarcar', {})['agendamento_id'] = ag_escolhido.id
        contexto['remarcar']['servico_id'] = ag_escolhido.servico_id
        sessao = sess.obter_sessao(telefone)
        sessao.contexto = json.dumps(contexto, ensure_ascii=False)
        db.session.commit()

        _enviar(telefone, datas_para_mensagem(ag_escolhido.servico_id))
        sess.definir_estado(telefone, sess.ESTADO_REMARCAR_DATA)
        return

    linhas = ['*Qual agendamento você quer remarcar?*\n']
    for i, ag in enumerate(ags, start=1):
        servico = ag.servico.nome if ag.servico else 'Serviço'
        linhas.append(f"{i} - {servico} ({formatar_data_br(ag.data)} às {ag.horario})")
    linhas.append('\nResponda com o *número*, ou *menu* para voltar.')
    _enviar(telefone, '\n'.join(linhas))
    sess.definir_estado(telefone, sess.ESTADO_REMARCAR_SELECAO,
                        contexto={'remarcar': {}})


def _fluxo_remarcar_servico(telefone, normalizado):
    """Recebe o novo serviço para remarcação."""
    servicos = lista_servicos_ativos()
    servico = None
    for i, s in enumerate(servicos, start=1):
        if normalizado == str(i) or normalizado == str(s.id):
            servico = s
            break
    if not servico:
        _enviar(telefone, "Escolha um serviço válido. " + servicos_para_mensagem())
        return
    contexto = sess.obter_contexto(telefone)
    contexto.setdefault('remarcar', {})['servico_id'] = servico.id
    sessao = sess.obter_sessao(telefone)
    sessao.contexto = json.dumps(contexto, ensure_ascii=False)
    db.session.commit()
    _enviar(telefone, datas_para_mensagem(servico.id))
    sess.definir_estado(telefone, sess.ESTADO_REMARCAR_DATA)


def _fluxo_remarcar_data(telefone, normalizado):
    """Recebe nova data e mostra horários."""
    indice = _parse_int(normalizado)
    contexto = sess.obter_contexto(telefone)
    servico_id = contexto.get('remarcar', {}).get('servico_id')

    data = interpretar_data_escolhida(servico_id, indice) if indice else None
    if not data:
        _enviar(telefone, "Escolha uma data válida. " +
                datas_para_mensagem(servico_id))
        return

    contexto['remarcar']['data'] = data.isoformat()
    sessao = sess.obter_sessao(telefone)
    sessao.contexto = json.dumps(contexto, ensure_ascii=False)
    db.session.commit()

    _enviar(telefone, horarios_para_mensagem(data, servico_id))
    sess.definir_estado(telefone, sess.ESTADO_REMARCAR_HORARIO)



def _fluxo_remarcar_horario(telefone, normalizado):
    """Recebe novo horário e pede confirmação da remarcação."""
    indice = _parse_int(normalizado)
    contexto = sess.obter_contexto(telefone)
    rem = contexto.get('remarcar', {})
    servico_id = rem.get('servico_id')
    try:
        data = date.fromisoformat(rem.get('data'))
    except (ValueError, TypeError):
        _enviar(telefone, "Dados inválidos. Vamos recomeçar.")
        sess.voltar_ao_menu(telefone)
        return

    from .agenda_helpers import horarios_livres
    livres = horarios_livres(data, servico_id)
    if not indice or not (1 <= indice <= len(livres)):
        _enviar(telefone, "Escolha um horário válido. " +
                horarios_para_mensagem(data, servico_id))
        return

    horario = livres[indice - 1]
    contexto['remarcar']['horario'] = horario
    sessao = sess.obter_sessao(telefone)
    sessao.contexto = json.dumps(contexto, ensure_ascii=False)
    db.session.commit()

    servico = Servico.query.get(servico_id)
    _enviar(
        telefone,
        "*Confirme a remarcação:*\n\n"
        f"💅 Serviço: *{servico.nome if servico else 'Serviço'}*\n"
        f"📅 Nova data: *{formatar_data_br(data)}*\n"
        f"⏰ Novo horário: *{horario}*\n\n"
        "Digite *1* para confirmar ou *2* para cancelar:"
    )
    sess.definir_estado(telefone, sess.ESTADO_REMARCAR_CONFIRMAR)


def _fluxo_remarcar_confirmar(telefone, normalizado):
    """Confirma a remarcação, cancelando o antigo e criando o novo."""
    if normalizado not in ('1', 'sim', 'confirmar', 'ok', 'confirmo'):
        _enviar(telefone, "Remarcação *cancelada*. 🙂\n\n" + MENU_INICIAL)
        sess.voltar_ao_menu(telefone)
        return

    contexto = sess.obter_contexto(telefone)
    rem = contexto.get('remarcar', {})
    ag_id = rem.get('agendamento_id')
    servico_id = rem.get('servico_id')
    horario = rem.get('horario')
    try:
        data = date.fromisoformat(rem.get('data'))
    except (ValueError, TypeError):
        _enviar(telefone, "Dados inválidos. Remarcação não concluída.")
        sess.voltar_ao_menu(telefone)
        return

    cliente = _cliente_por_telefone(telefone)
    if not cliente:
        _enviar(telefone, "Cliente não encontrado.")
        sess.voltar_ao_menu(telefone)
        return

    # Cria o novo agendamento (com prevenção de conflito)
    novo, erro = criar_agendamento(
        telefone, cliente, servico_id, data, horario, origem='remarcacao'
    )
    if not novo:
        _enviar(telefone, f"❌ Não foi possível remarcar: {erro}")
        sess.voltar_ao_menu(telefone)
        return

    # Cancela o agendamento antigo
    antigo = Agendamento.query.get(ag_id)
    if antigo and antigo.status in ('pendente', 'confirmada'):
        antigo.status = 'cancelada'
        db.session.commit()

    _registrar_log(telefone, 'agendamento_remarcado',
                   f'de_id={antigo.id if antigo else None} para_id={novo.id}')
    _enviar(telefone,
            "✅ *Remarcação concluída!*\n\n" +
            formatar_resumo_agendamento(novo) +
            "\n\nA administradora foi notificada.")
    notifier.notificar_admin(
        f"🔄 *Atendimento remarcado*\n{formatar_resumo_agendamento(novo)}"
    )
    sess.voltar_ao_menu(telefone)



# ============================================
# FLUXO ADMINISTRADORA
# ============================================

def _entrar_admin(telefone):
    """Abre o menu administrativo, apenas para números autorizados."""
    if not notifier.eh_admin(telefone):
        _enviar(telefone,
                "⛔ Você não está autorizado a usar comandos administrativos.")
        _registrar_log(telefone, 'admin_acesso_negado')
        sess.voltar_ao_menu(telefone)
        return

    _registrar_log(telefone, 'admin_menu_aberto')
    _enviar(telefone, MENU_ADMIN)
    sess.definir_estado(telefone, 'admin')


def _tratar_admin(telefone, normalizado, estado):
    """
    Processa comandos administrativos quando o usuário está no
    modo admin (estado começa com 'admin').
    """
    if not notifier.eh_admin(telefone):
        _enviar(telefone,
                "⛔ Você não está autorizado a usar comandos administrativos.")
        sess.voltar_ao_menu(telefone)
        return

    cmd = normalizado.replace('a', '').strip()

    if normalizado == 'a1' or cmd == '1':
        _admin_agenda_dia(telefone)
    elif normalizado == 'a2' or cmd == '2':
        _admin_proximos(telefone)
    elif normalizado == 'a3' or cmd == '3':
        _admin_pendentes(telefone)
    elif normalizado == 'a4' or cmd == '4':
        _admin_concluir(telefone)
    elif normalizado == 'a5' or cmd == '5':
        _admin_clientes(telefone)
    elif normalizado == 'a6' or cmd == '6':
        _admin_faturamento(telefone)
    elif normalizado == 'a7' or cmd == '7':
        _admin_listar_servicos(telefone)
    elif normalizado == 'a8' or cmd == '8':
        _enviar(telefone, "Comando de cadastro de serviço em desenvolvimento.")
    elif normalizado == 'a9' or cmd == '9':
        _enviar(telefone, "Comando de edição de serviço em desenvolvimento.")
    elif normalizado == 'a0' or cmd == '0':
        _admin_desativar_servico(telefone)
    else:
        _enviar(telefone, "Comando administrativo não reconhecido.\n\n" + MENU_ADMIN)



# ============================================
# IMPLEMENTAÇÕES DOS COMANDOS ADMIN
# ============================================

def _agendamentos_do_dia(data=None):
    """Retorna agendamentos de um dia, ordenados por horário."""
    dia = data or date.today()
    return Agendamento.query.filter_by(data=dia).order_by(
        Agendamento.horario).all()


def _admin_agenda_dia(telefone):
    """Mostra a agenda do dia à administradora."""
    hoje = date.today()
    ags = _agendamentos_do_dia(hoje)
    if not ags:
        _enviar(telefone, f"📅 *Agenda de hoje ({formatar_data_br(hoje)}):*\n"
                          "Nenhum agendamento.")
    else:
        linhas = [f"📅 *Agenda de hoje ({formatar_data_br(hoje)}):*\n"]
        for ag in ags:
            cliente = ag.cliente.nome if ag.cliente else 'Cliente'
            servico = ag.servico.nome if ag.servico else 'Serviço'
            linhas.append(f"• {ag.horario} - {cliente} ({servico}) "
                          f"[{ag.status}]")
        _enviar(telefone, '\n'.join(linhas[:15]))
    _registrar_log(telefone, 'admin_agenda_dia')


def _admin_proximos(telefone):
    """Lista os próximos agendamentos (pendentes/confirmadas)."""
    hoje = date.today()
    ags = Agendamento.query.filter(
        Agendamento.data >= hoje,
        Agendamento.status.in_(['pendente', 'confirmada'])
    ).order_by(Agendamento.data, Agendamento.horario).limit(10).all()

    if not ags:
        _enviar(telefone, "📋 *Próximos agendamentos:*\nNenhum encontrado.")
    else:
        linhas = ['📋 *Próximos agendamentos:*\n']
        for ag in ags:
            cliente = ag.cliente.nome if ag.cliente else 'Cliente'
            servico = ag.servico.nome if ag.servico else 'Serviço'
            linhas.append(
                f"• {formatar_data_br(ag.data)} {ag.horario} - {cliente}"
                f" ({servico}) [{ag.status}]")
        _enviar(telefone, '\n'.join(linhas))
    _registrar_log(telefone, 'admin_proximos')


def _admin_pendentes(telefone):
    """Lista agendamentos pendentes para a administradora confirmar."""
    ags = Agendamento.query.filter_by(status='pendente').order_by(
        Agendamento.data, Agendamento.horario).limit(10).all()
    if not ags:
        _enviar(telefone, "✅ Nenhum agendamento pendente de confirmação.")
        return
    linhas = ['🕓 *Agendamentos pendentes (responda com o número para confirmar):*\n']
    for i, ag in enumerate(ags, start=1):
        cliente = ag.cliente.nome if ag.cliente else 'Cliente'
        servico = ag.servico.nome if ag.servico else 'Serviço'
        linhas.append(
            f"{i} - {formatar_data_br(ag.data)} {ag.horario} - {cliente}"
            f" ({servico})")
    linhas.append('\nDigite o *número* do que deseja confirmar.')
    _enviar(telefone, '\n'.join(linhas))
    # Salva a lista de pendentes no contexto para a confirmação
    ids = [ag.id for ag in ags]
    sess.definir_estado(telefone, 'admin_confirmar_pendente',
                        contexto={'admin_pendentes': ids})
    _registrar_log(telefone, 'admin_pendentes_lista')


def _admin_concluir(telefone):
    """Lista agendamentos confirmados do dia para concluir."""
    hoje = date.today()
    ags = Agendamento.query.filter(
        Agendamento.data == hoje,
        Agendamento.status == 'confirmada'
    ).order_by(Agendamento.horario).limit(10).all()
    if not ags:
        _enviar(telefone, "✅ Nenhum atendimento confirmado para hoje concluir.")
        return
    linhas = ['✅ *Atendimentos para concluir hoje (responda o número):*\n']
    for i, ag in enumerate(ags, start=1):
        cliente = ag.cliente.nome if ag.cliente else 'Cliente'
        servico = ag.servico.nome if ag.servico else 'Serviço'
        linhas.append(f"{i} - {ag.horario} - {cliente} ({servico})")
    _enviar(telefone, '\n'.join(linhas))
    ids = [ag.id for ag in ags]
    sess.definir_estado(telefone, 'admin_concluir_selecao',
                        contexto={'admin_concluir': ids})
    _registrar_log(telefone, 'admin_concluir_lista')



def _admin_clientes(telefone):
    """Lista os clientes cadastrados."""
    clientes = Cliente.query.order_by(Cliente.nome).limit(20).all()
    if not clientes:
        _enviar(telefone, "👤 *Nenhum cliente cadastrado ainda.*")
    else:
        linhas = ['👤 *Clientes cadastrados:*\n']
        for c in clientes:
            telefone_fmt = c.telefone or '-'
            ag_count = Agendamento.query.filter_by(cliente_id=c.id).count()
            linhas.append(f"• {c.nome} ({telefone_fmt}) — {ag_count} agendamento(s)")
        _enviar(telefone, '\n'.join(linhas))
    _registrar_log(telefone, 'admin_clientes')


def _admin_faturamento(telefone):
    """Mostra o faturamento do mês corrente."""
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)
    ags = Agendamento.query.filter(
        Agendamento.data >= primeiro_dia,
        Agendamento.data <= hoje,
        Agendamento.status.in_(['confirmada', 'realizada'])
    ).all()

    total = sum(ag.servico.preco if ag.servico else 0 for ag in ags)
    linhas = [
        f"💰 *Faturamento de {hoje.strftime('%B/%Y').title()}:*\n",
        f"Total de atendimentos: *{len(ags)}*",
        f"Valor total: *{formatar_moeda(total)}*\n"
    ]

    if ags:
        por_servico = {}
        for ag in ags:
            nome = ag.servico.nome if ag.servico else 'Serviço'
            por_servico[nome] = por_servico.get(nome, 0) + (ag.servico.preco if ag.servico else 0)
        linhas.append("Por serviço:")
        for nome, val in sorted(por_servico.items(), key=lambda x: -x[1]):
            linhas.append(f"  • {nome}: {formatar_moeda(val)}")

    _enviar(telefone, '\n'.join(linhas))
    _registrar_log(telefone, 'admin_faturamento')


def _admin_listar_servicos(telefone):
    """Lista os serviços ativos e inativos."""
    servicos = Servico.query.order_by(Servico.nome).all()
    if not servicos:
        _enviar(telefone, "💅 *Nenhum serviço cadastrado.*")
        return
    linhas = ['💅 *Serviços:*\n']
    for s in servicos:
        status = "✅" if s.ativo else "❌"
        linhas.append(
            f"{status} ID {s.id} — {s.nome} ({formatar_moeda(s.preco)}) — {s.duracao_min} min"
        )
    _enviar(telefone, '\n'.join(linhas))
    _registrar_log(telefone, 'admin_listar_servicos')


def _admin_desativar_servico(telefone):
    """Lista serviços ativos para desativar (o admin escolhe por ID)."""
    servicos = Servico.query.filter_by(ativo=True).order_by(Servico.nome).all()
    if not servicos:
        _enviar(telefone, "Nenhum serviço ativo para desativar.")
        return
    linhas = ['*Serviço para desativar (responda o ID):*\n']
    for s in servicos:
        linhas.append(f"ID {s.id} — {s.nome} ({formatar_moeda(s.preco)})")
    _enviar(telefone, '\n'.join(linhas))
    ids = [s.id for s in servicos]
    sess.definir_estado(telefone, 'admin_desativar_servico',
                        contexto={'admin_desativar_ids': ids})
    _registrar_log(telefone, 'admin_desativar_servico_lista')



# ============================================
# CONFIRMAÇÃO/CONCLUSÃO ADMIN (sub-estados)
# ============================================

def _admin_confirmar_pendente(telefone, normalizado):
    """Confirma um agendamento pendente escolhido pelo admin."""
    contexto = sess.obter_contexto(telefone)
    ids = contexto.get('admin_pendentes', [])
    indice = _parse_int(normalizado)

    if not indice or not (1 <= indice <= len(ids)):
        _enviar(telefone, "Número inválido. Tente novamente ou digite *menu*.")
        return

    ag_id = ids[indice - 1]
    ag = Agendamento.query.get(ag_id)
    if ag and ag.status == 'pendente':
        ag.status = 'confirmada'
        db.session.commit()
        _registrar_log(telefone, 'admin_confirmou_pendente', f'id={ag_id}')
        _enviar(telefone,
                f"✅ Agendamento de *{ag.cliente.nome if ag.cliente else '?'}* confirmado!\n" +
                formatar_resumo_agendamento(ag))
        # Notifica o cliente
        if ag.cliente and ag.cliente.telefone:
            api_client.enviar_texto(
                ag.cliente.telefone,
                f"✅ Olá {ag.cliente.nome}! Seu agendamento foi *confirmado*.\n\n" +
                formatar_resumo_agendamento(ag)
            )
    else:
        _enviar(telefone, "Esse agendamento não está mais pendente.")
    sess.voltar_ao_menu(telefone)


def _admin_concluir_selecao(telefone, normalizado):
    """Conclui um atendimento do dia escolhido pelo admin."""
    contexto = sess.obter_contexto(telefone)
    ids = contexto.get('admin_concluir', [])
    indice = _parse_int(normalizado)

    if not indice or not (1 <= indice <= len(ids)):
        _enviar(telefone, "Número inválido. Tente novamente ou digite *menu*.")
        return

    ag_id = ids[indice - 1]
    ag = Agendamento.query.get(ag_id)
    if ag and ag.status == 'confirmada':
        ag.status = 'realizada'
        db.session.commit()
        _registrar_log(telefone, 'admin_concluiu_atendimento', f'id={ag_id}')
        _enviar(telefone,
                f"✅ Atendimento de *{ag.cliente.nome if ag.cliente else '?'}* concluído!\n" +
                formatar_resumo_agendamento(ag))
    else:
        _enviar(telefone, "Esse atendimento não está mais confirmado.")
    sess.voltar_ao_menu(telefone)


def _admin_desativar_servico_confirma(telefone, normalizado):
    """Desativa um serviço escolhido pelo admin."""
    contexto = sess.obter_contexto(telefone)
    ids = contexto.get('admin_desativar_ids', [])

    # O admin pode digitar o ID do serviço
    servico_id = _parse_int(normalizado)

    if not servico_id or servico_id not in ids:
        _enviar(telefone, "ID inválido. Tente novamente ou digite *menu*.")
        return

    servico = Servico.query.get(servico_id)
    if servico and servico.ativo:
        servico.ativo = False
        db.session.commit()
        _registrar_log(telefone, 'admin_desativou_servico', f'id={servico_id}')
        _enviar(telefone,
                f"❌ Serviço *{servico.nome}* desativado com sucesso.")
    else:
        _enviar(telefone, "Esse serviço não está mais ativo.")
    sess.voltar_ao_menu(telefone)

