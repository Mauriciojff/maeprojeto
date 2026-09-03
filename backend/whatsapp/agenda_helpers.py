# ============================================
# WHATSAPP/AGENDA_HELPERS.PY — Lógica de agendamento p/ WhatsApp
# ============================================

import logging
from datetime import datetime, date, timedelta

from ..database import db
from ..database.models import Servico, Agendamento, Cliente
from ..utils.helpers import gerar_horarios, get_config, formatar_moeda, \
    formatar_data_br

logger = logging.getLogger('agenda_mae')


def lista_servicos_ativos():
    """Retorna serviços ativos ordenados por nome."""
    return Servico.query.filter_by(ativo=True).order_by(Servico.nome).all()


def servicos_para_mensagem():
    """
    Monta uma mensagem legível com os serviços disponíveis,
    preço e duração.
    """
    servicos = lista_servicos_ativos()
    if not servicos:
        return 'Nenhum serviço cadastrado no momento.'
    linhas = ['*Serviços disponíveis:*\n']
    for s in servicos:
        linhas.append(f"{s.id} - {s.nome}\n"
                      f"   💰 {formatar_moeda(s.preco)} | ⏱ {s.duracao_min} min")
    linhas.append('\nResponda com o *número* do serviço desejado.')
    return '\n'.join(linhas)


def formatar_servico(s):
    """Formata um serviço para exibição."""
    return f"{s.nome} | {formatar_moeda(s.preco)} | {s.duracao_min} min"


def horarios_livres(data, servico_id=None):
    """
    Retorna os horários livres para uma data, considerando os
    conflitos de horário (com duração dos serviços).
    """
    from ..routes.agendamentos import verificar_conflito

    config = {
        'hora_abertura': get_config('hora_abertura', '08:00'),
        'hora_fechamento': get_config('hora_fechamento', '20:00'),
        'intervalo_min': int(get_config('intervalo_min', '60')),
    }
    todos = gerar_horarios(config['hora_abertura'],
                           config['hora_fechamento'],
                           config['intervalo_min'])

    livres = []
    for h in todos:
        if servico_id:
            conflito = verificar_conflito(data, h, servico_id)
            if conflito:
                continue
        livres.append(h)

    # Se for hoje, remove horários já passados
    if data == date.today():
        agora = datetime.now().strftime('%H:%M')
        livres = [h for h in livres if h > agora]

    return livres


def proximas_datas_disponiveis(servico_id=None, dias=14, ignorar_fim_de_semana=True):
    """
    Retorna uma lista de datas (date) disponíveis para agendamento
    dentro dos próximos N dias. Se ignorar_fim_de_semana for True,
    considera apenas dias úteis (seg-sex).
    """
    hoje = date.today()
    datas = []
    dia = hoje + timedelta(days=1)  # começa amanhã
    contador = 0
    while len(datas) < 7 and contador < dias:
        if not (ignorar_fim_de_semana and dia.weekday() >= 5):
            if horarios_livres(dia, servico_id):
                datas.append(dia)
        dia += timedelta(days=1)
        contador += 1
    return datas


def datas_para_mensagem(servico_id=None):
    """Monta mensagem com as próximas datas disponíveis."""
    datas = proximas_datas_disponiveis(servico_id)
    if not datas:
        return 'Não há datas disponíveis nos próximos dias.'
    linhas = ['*Escolha uma data (responda com o número):*\n']
    for i, d in enumerate(datas, start=1):
        dias = (d - date.today()).days
        rotulo = ('Amanhã' if dias == 1 else formatar_data_br(d))
        linhas.append(f"{i} - {rotulo} ({formatar_data_br(d)})")
    linhas.append('\nResponda com o *número* da data desejada.')
    return '\n'.join(linhas)


def interpretar_data_escolhida(servico_id, indice):
    """Retorna a data correspondente ao índice escolhido (1-based)."""
    datas = proximas_datas_disponiveis(servico_id)
    if 1 <= indice <= len(datas):
        return datas[indice - 1]
    return None


def horarios_para_mensagem(data, servico_id=None):
    """Monta mensagem com horários livres de uma data."""
    livres = horarios_livres(data, servico_id)
    if not livres:
        return 'Não há horários livres nesta data. Escolha outra data.'
    linhas = [f"*Horários livres em {formatar_data_br(data)}:*\n"]
    for i, h in enumerate(livres, start=1):
        linhas.append(f"{i} - {h}")
    linhas.append('\nResponda com o *número* do horário desejado.')
    return '\n'.join(linhas)


def formatar_resumo_agendamento(ag):
    """Formata o resumo de um agendamento para envio ao cliente."""
    servico = ag.servico
    nume = servico.nome if servico else 'Serviço'
    preco = formatar_moeda(ag.preco) if ag.preco else \
        (formatar_moeda(servico.preco) if servico else '-')
    return (
        "*Resumo do agendamento:*\n"
        f"• Serviço: {nume}\n"
        f"• Data: {formatar_data_br(ag.data)}\n"
        f"• Horário: {ag.horario}\n"
        f"• Preço: {preco}\n"
        f"• Status: {ag.status.capitalize()}"
    )


def criar_agendamento(telefone, cliente, servico_id, data, horario, origem='whatsapp'):
    """
    Cria um agendamento com prevenção de conflito de horário,
    dentro de uma transação. Retorna o agendamento ou None se
    houver conflito.
    """
    from ..routes.agendamentos import verificar_conflito

    servico = Servico.query.get(servico_id)
    if not servico or not servico.ativo:
        return None, 'Serviço não encontrado.'

    # Conflito de horário
    conflito = verificar_conflito(data, horario, servico_id)
    if conflito:
        return None, 'Horário já reservado. Escolha outro horário.'

    try:
        ag = Agendamento(
            cliente_id=cliente.id,
            servico_id=servico_id,
            data=data,
            horario=horario,
            status='pendente',
            preco=servico.preco,
            whatsapp_confirmado=True,
            obs=f'Criado via WhatsApp ({origem})'
        )
        db.session.add(ag)
        db.session.commit()
        logger.info(f"Agendamento criado via WhatsApp: id={ag.id}, tel={telefone}")
        return ag, None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar agendamento via WhatsApp: {str(e)[:200]}")
        return None, 'Erro ao criar o agendamento. Tente novamente.'


def agendamentos_do_cliente_ativos(cliente_id):
    """Agendamentos futuros do cliente que ainda estão ativos."""
    return Agendamento.query.filter(
        Agendamento.cliente_id == cliente_id,
        Agendamento.data >= date.today(),
        Agendamento.status.in_(['pendente', 'confirmada'])
    ).order_by(Agendamento.data, Agendamento.horario).all()


def agendamentos_formatados(agendamentos):
    """Formata a lista de agendamentos para mensagem."""
    if not agendamentos:
        return 'Você não tem agendamentos futuros.'
    linhas = ['*Seus agendamentos:*\n']
    for i, ag in enumerate(agendamentos, start=1):
        servico = ag.servico.nome if ag.servico else 'Serviço'
        linhas.append(
            f"{i} - {servico}\n"
            f"   📅 {formatar_data_br(ag.data)} às {ag.horario}\n"
            f"   Status: {ag.status.capitalize()}"
        )
    return '\n'.join(linhas)

