# ============================================
# UTILS/HELPERS.PY — Funções utilitárias
# ============================================

import re
import logging
from datetime import datetime, timedelta
from flask import current_app

from ..database.models import Configuracao
from ..database import db

logger = logging.getLogger('agenda_mae')


# ============================================
# FORMATAÇÃO
# ============================================

def formatar_moeda(valor):
    """Formata valor como moeda brasileira."""
    try:
        valor_f = float(valor or 0)
        return f'R$ {valor_f:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return 'R$ 0,00'


def formatar_data_br(data):
    """Formata data ISO (YYYY-MM-DD) ou date para DD/MM/AAAA."""
    if not data:
        return ''
    if isinstance(data, str):
        try:
            data = datetime.strptime(data, '%Y-%m-%d').date()
        except ValueError:
            return data
    return data.strftime('%d/%m/%Y')


# ============================================
# HORÁRIOS
# ============================================

def gerar_horarios(abertura='08:00', fechamento='20:00', intervalo=60):
    """Gera a lista de horários disponíveis baseado em abertura/fechamento/intervalo."""
    try:
        h_a, m_a = map(int, abertura.split(':'))
        h_f, m_f = map(int, fechamento.split(':'))
        inicio = h_a * 60 + m_a
        fim = h_f * 60 + m_f
        horarios = []
        atual = inicio
        while atual < fim:
            h, m = divmod(atual, 60)
            horarios.append(f'{h:02d}:{m:02d}')
            atual += intervalo
        return horarios
    except (ValueError, AttributeError):
        return [f'{h:02d}:00' for h in range(8, 20)]


# ============================================
# TELEFONE / WHATSAPP
# ============================================

def telefone_limpo(telefone):
    """Remove tudo que não é dígito."""
    if not telefone:
        return ''
    return re.sub(r'\D', '', telefone)


def whatsapp_url(telefone, mensagem=''):
    """
    Gera URL do WhatsApp (wa.me) para abrir conversa.
    """
    tel = telefone_limpo(telefone)
    if not tel:
        return '#'
    ddi = current_app.config.get('WHATSAPP_DDI', '55')
    base = current_app.config.get('WHATSAPP_BASE', 'https://wa.me')
    import urllib.parse
    url = f'{base}/{ddi}{tel}'
    if mensagem:
        url += f'?text={urllib.parse.quote(mensagem)}'
    return url


# ============================================
# CONFIGURAÇÕES
# ============================================

def get_config(chave, padrao=None):
    """Obtém valor de configuração do banco."""
    config = Configuracao.query.filter_by(chave=chave).first()
    return config.valor if config else padrao


def set_config(chave, valor):
    """Define valor de configuração no banco."""
    config = Configuracao.query.filter_by(chave=chave).first()
    if config:
        config.valor = valor
    else:
        config = Configuracao(chave=chave, valor=valor)
        db.session.add(config)
    db.session.commit()
    return config


# ============================================
# LOGGING HELPERS
# ============================================

def log_evento(evento, **detalhes):
    """Registra evento de auditoria."""
    logger.info(f'AUDITORIA: {evento}', extra={'detalhes': detalhes})
