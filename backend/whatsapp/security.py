# ============================================
# WHATSAPP/SECURITY.PY — Validação e sanitização de webhooks
# ============================================

import hashlib
import hmac
import logging
import re
from flask import current_app

logger = logging.getLogger('agenda_mae')


def validar_assinatura_webhook(corpo_bytes, assinatura_recebida):
    """
    Valida a assinatura X-Hub-Signature-256 enviada pela Meta no webhook.

    A Meta assina o corpo bruto da requisição (bytes) com o
    WHATSAPP_WEBHOOK_SECRET usando HMAC-SHA256. Compara em tempo
    constante para evitar ataques de timing.

    Retorna True se a assinatura é válida, False caso contrário.
    """
    segredo = current_app.config.get('WHATSAPP_WEBHOOK_SECRET', '')
    if not segredo:
        logger.warning('WHATSAPP_WEBHOOK_SECRET não configurado.')
        return False

    if not assinatura_recebida:
        return False

    # Formato esperado: sha256=<hex>
    prefixo = 'sha256='
    if not assinatura_recebida.startswith(prefixo):
        return False
    assinatura_hex = assinatura_recebida[len(prefixo):]

    assinatura_esperada = hmac.new(
        segredo.encode('utf-8'),
        corpo_bytes,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(assinatura_esperada, assinatura_hex)


def vetar_telefone(mensagem):
    """
    Extrai e normaliza o telefone do remetente.
    Normaliza para o formato internacional (apenas dígitos), ex.: 5511999999999.
    Retorna None se não houver telefone válido.
    """
    try:
        objeto = mensagem.get('from', '')
    except AttributeError:
        return None
    digitos = re.sub(r'\D', '', objeto or '')
    return digitos if digitos else None


def normalizar_texto(texto):
    """
    Normaliza o texto recebido: remove acentos, coloca minúsculas,
    remove espaços extras e caracteres de controle. Usado para
    interpretar comandos de forma tolerante.
    """
    if not texto:
        return ''
    if not isinstance(texto, str):
        texto = str(texto)
    # Remove acentos
    mapa = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
    }
    texto = texto.lower()
    texto = texto.translate(str.maketrans(mapa))
    # Remove caracteres não alfanuméricos e espaços
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto[:200]


def ler_corpo_msg(mensagem):
    """
    Extrai o texto de uma mensagem do payload do WhatsApp,
    tratando os diferentes formatos (text, interactive).
    Retorna o texto em string (vazio se não for texto).
    """
    try:
        tipo = mensagem.get('type', '')
        if tipo == 'text':
            return mensagem.get('text', {}).get('body', '') or ''
        if tipo == 'interactive':
            inter = mensagem.get('interactive', {})
            tipo_inter = inter.get('type', '')
            if tipo_inter == 'button_reply':
                return inter.get('button_reply', {}).get('title', '') or ''
            if tipo_inter == 'list_reply':
                return inter.get('list_reply', {}).get('title', '') or ''
        return ''
    except (AttributeError, TypeError):
        return ''
