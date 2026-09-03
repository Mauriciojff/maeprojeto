# ============================================
# WHATSAPP/NOTIFIER.PY — Notificações para a administradora
# ============================================

import logging
from flask import current_app

from . import api_client

logger = logging.getLogger('agenda_mae')


def numeros_admin():
    """
    Retorna a lista de números de WhatsApp autorizados como
    administradores, a partir da variável de ambiente
    ADMIN_WHATSAPP_NUMBERS (separados por vírgula).
    """
    raw = current_app.config.get('ADMIN_WHATSAPP_NUMBERS', '')
    if not raw:
        return []
    numeros = []
    for item in raw.split(','):
        item = item.strip()
        if item:
            numeros.append(item)
    return numeros


def eh_admin(telefone):
    """Verifica se um telefone é administrador autorizado."""
    return telefone in numeros_admin()


def notificar_admin(mensagem):
    """
    Envia uma notificação para todos os números de administradores
    configurados (ex.: novo agendamento, cancelamento).
    """
    for numero in numeros_admin():
        api_client.enviar_texto(numero, mensagem)
