# ============================================
# WHATSAPP/API_CLIENT.PY — Cliente da WhatsApp Business Cloud API
# ============================================

import logging
import requests
from flask import current_app

from ..database import db
from ..database.wpp_models import MensagemEnviada

logger = logging.getLogger('agenda_mae')


def _config():
    """Lê as configurações da API do app (sem expor segredos em logs)."""
    return {
        'token': current_app.config.get('WHATSAPP_TOKEN', ''),
        'phone_number_id': current_app.config.get('WHATSAPP_PHONE_NUMBER_ID', ''),
        'graph_api': current_app.config.get('WHATSAPP_GRAPH_API',
                                            'https://graph.facebook.com/v19.0'),
        'dry_run': current_app.config.get('WHATSAPP_DRY_RUN', False),
    }


def esta_configurado():
    """Verifica se o token e o phone number ID estão configurados."""
    cfg = _config()
    return bool(cfg['token'] and cfg['phone_number_id'])


def enviar_texto(telefone, texto, persistir=True):
    """
    Envia uma mensagem de texto via WhatsApp Business Cloud API.

    Usa a endpoint /{phone_number_id}/messages do Graph API.
    Em modo dry-run (testes/dev), apenas registra e retorna sucesso.

    Retorna (sucesso: bool, mensagem_id: str|None, erro: str|None).
    """
    cfg = _config()
    if not cfg['token'] or not cfg['phone_number_id']:
        if persistir:
            _persistir_mensagem(telefone, texto, tipo='text',
                                status='erro', erro='API não configurada')
        return False, None, 'API não configurada'

    url = f"{cfg['graph_api']}/{cfg['phone_number_id']}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "text",
        "text": {"body": texto},
    }
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Content-Type": "application/json",
    }

    if cfg['dry_run']:
        logger.info(f"WHATSAPP (dry-run) -> {telefone}: {texto[:60]}")
        message_id = f"dryrun-{abs(hash(telefone + texto))}"
        if persistir:
            _persistir_mensagem(telefone, texto, tipo='text',
                                status='enviada', message_id=message_id)
        return True, message_id, None

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code == 200:
            dados = resp.json()
            mensagens = dados.get('messages') or []
            message_id = mensagens[0].get('id') if mensagens else None
            if persistir:
                _persistir_mensagem(telefone, texto, tipo='text',
                                    status='enviada', message_id=message_id)
            return True, message_id, None
        # Erro vindo da API
        erro = resp.text[:500]
        logger.error(f"WhatsApp API erro {resp.status_code}: {erro[:200]}")
        if persistir:
            _persistir_mensagem(telefone, texto, tipo='text',
                                status='erro', erro=erro[:255])
        return False, None, erro
    except requests.RequestException as e:
        logger.error(f"Falha ao enviar mensagem WhatsApp: {str(e)[:200]}")
        if persistir:
            _persistir_mensagem(telefone, texto, tipo='text',
                                status='erro', erro=str(e)[:255])
        return False, None, str(e)


def _persistir_mensagem(telefone, texto, tipo='text',
                        status='enviada', message_id=None, erro=None):
    """Persiste registro de mensagem enviada no banco."""
    try:
        msg = MensagemEnviada(
            whatsapp_message_id=message_id,
            telefone=telefone,
            corpo=texto,
            tipo=tipo,
            status=status,
            erro=erro
        )
        db.session.add(msg)
        db.session.commit()
    except Exception as e:  # pragma: no cover - defensivo
        logger.error(f"Falha ao persistir mensagem enviada: {str(e)[:200]}")
        db.session.rollback()
