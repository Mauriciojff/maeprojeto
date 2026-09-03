# ============================================
# WHATSAPP/SESSION_STATE.PY — Gestão de sessões de conversa
# ============================================

import json
import logging
from datetime import datetime

from ..database import db
from ..database.wpp_models import SessaoConversa

logger = logging.getLogger('agenda_mae')

# Estados possíveis do fluxo da conversa
ESTADO_MENU = 'menu'
ESTADO_CADASTRO_NOME = 'cadastro_nome'
ESTADO_CADASTRO_EMAIL = 'cadastro_email'
ESTADO_CADASTRO_CONFIRMAR = 'cadastro_confirmar'
ESTADO_CADASTRO_CONFIRMAR_DADOS = 'cadastro_confirmar_dados'
ESTADO_AGENDAR_SERVICO = 'agendar_servico'
ESTADO_AGENDAR_DATA = 'agendar_data'
ESTADO_AGENDAR_HORARIO = 'agendar_horario'
ESTADO_AGENDAR_CONFIRMAR = 'agendar_confirmar'
ESTADO_REMARCAR_SELECAO = 'remarcar_selecao'
ESTADO_REMARCAR_SERVICO = 'remarcar_servico'
ESTADO_REMARCAR_DATA = 'remarcar_data'
ESTADO_REMARCAR_HORARIO = 'remarcar_horario'
ESTADO_REMARCAR_CONFIRMAR = 'remarcar_confirmar'
ESTADO_CANCELAR_SELECAO = 'cancelar_selecao'
ESTADO_CANCELAR_CONFIRMAR = 'cancelar_confirmar'
ESTADO_ADMIN_AGENDA = 'admin_agenda'
ESTADO_ADMIN_CLIENTES = 'admin_clientes'
ESTADO_CONSULTAR_AGENDA = 'consultar_agenda'


def obter_sessao(telefone, criar=True):
    """Obtém a sessão de conversa do telefone, criando se necessário."""
    sessao = SessaoConversa.query.filter_by(telefone=telefone).first()
    if not sessao and criar:
        sessao = SessaoConversa(telefone=telefone, estado=ESTADO_MENU,
                                contexto='{}')
        db.session.add(sessao)
        db.session.commit()
    return sessao


def definir_estado(telefone, estado, contexto=None):
    """Define o estado da conversa, resetando ou mesclando contexto."""
    sessao = obter_sessao(telefone)
    if not sessao:
        return None

    if contexto is not None:
        sessao.contexto = json.dumps(contexto, ensure_ascii=False)
    sessao.estado = estado
    sessao.ultima_atividade = datetime.utcnow()
    sessao.qtd_mensagens = sessao.qtd_mensagens + 1
    db.session.commit()
    return sessao


def obter_contexto(telefone):
    """Retorna o contexto (dict) da sessão atual."""
    sessao = obter_sessao(telefone, criar=False)
    if not sessao or not sessao.contexto:
        return {}
    try:
        return json.loads(sessao.contexto)
    except (ValueError, TypeError):
        return {}


def atualizar_contexto(telefone, **campos):
    """Atualiza campos do contexto mantendo os demais."""
    contexto = obter_contexto(telefone)
    contexto.update(campos)
    sessao = obter_sessao(telefone)
    if sessao:
        sessao.contexto = json.dumps(contexto, ensure_ascii=False)
        sessao.ultima_atividade = datetime.utcnow()
        db.session.commit()
    return contexto


def obter_estado(telefone):
    """Retorna o estado atual da conversa (padrão: menu)."""
    sessao = obter_sessao(telefone, criar=False)
    return sessao.estado if sessao else ESTADO_MENU


def voltar_ao_menu(telefone):
    """Reseta a sessão para o menu inicial."""
    definir_estado(telefone, ESTADO_MENU, contexto={})
