# ============================================
# WHATSAPP/WEBHOOK.PY — Webhook da WhatsApp Business Cloud API
# ============================================
#
# Rotas:
#   GET  /api/whatsapp/webhook  → validação do token de verificação (handshake)
#   POST /api/whatsapp/webhook  → recebe notificações de mensagens recebidas
#
# A segurança é feita em duas camadas:
#   1. Handshake GET com WHATSAPP_VERIFY_TOKEN
#   2. Assinatura X-Hub-Signature-256 (HMAC-SHA256) no POST

import logging

from flask import Blueprint, request, jsonify

from . import security
from . import rate_limiter
from .conversation import processar_mensagem

logger = logging.getLogger('agenda_mae')

# Blueprint registrado via import em backend/__init__.py
webhook_bp = Blueprint('webhook_whatsapp', __name__, url_prefix='/api/whatsapp')


@webhook_bp.route('/webhook', methods=['GET'])
def verificar_webhook():
    """
    Handshake de verificação solicitado pela Meta ao configurar o webhook.

    A Meta envia os parâmetros hub.mode, hub.verify_token e hub.challenge.
    Devemos responder com o hub.challenge apenas se o verify_token bater
    com WHATSAPP_VERIFY_TOKEN configurado.
    """
    from flask import current_app

    modo = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    desafio = request.args.get('hub.challenge')

    esperado = current_app.config.get('WHATSAPP_VERIFY_TOKEN', '')
    if not esperado:
        logger.warning('WHATSAPP_VERIFY_TOKEN não configurado.')
        return 'Configuração incompleta', 500

    if modo == 'subscribe' and token == esperado:
        logger.info('Webhook do WhatsApp verificado com sucesso.')
        return desafio, 200
    return 'Token de verificação inválido', 403


@webhook_bp.route('/webhook', methods=['POST'])
def receber_webhook():
    """
    Recebe notificações de mensagens da Meta.

    Fluxo:
      1. Lê o corpo bruto (bytes) para validar a assinatura.
      2. Valida X-Hub-Signature-256 (HMAC-SHA256) quando configurado.
      3. Aplica rate limit por remetente.
      4. Processa cada mensagem recebida.

    Sempre responde 200 para a Meta (mesmo em caso de erro interno),
    para evitar retries desnecessários, exceto em falhas de validação
    de segurança (403) que precisam ser investigadas.
    """
    from flask import current_app

    # 1) Assinatura (se estiver configurada)
    segredo = current_app.config.get('WHATSAPP_WEBHOOK_SECRET', '')
    if segredo:
        assinatura = request.headers.get('X-Hub-Signature-256', '')
        if not security.validar_assinatura_webhook(request.data, assinatura):
            logger.warning('Assinatura de webhook inválida.')
            return jsonify({'erro': 'Assinatura inválida'}), 403

    # 2) Parse do corpo
    try:
        dados = request.get_json(silent=True) or {}
    except Exception:  # pragma: no cover - defensivo
        dados = {}

    # 3) Processar mensagens recebidas
    tentativas = dados.get('entry', [])
    if not tentativas:
        # Resposta vazia de confirmação (ex.: mensagens de status)
        return 'ok', 200

    for entrada in tentativas:
        mudancas = entrada.get('changes') or []
        for mudanca in mudancas:
            valor = mudanca.get('value') or {}
            mensagens = valor.get('messages') or []

            if not mensagens:
                # Pode ser um evento de status, leitura ou configuração
                _tratar_outros_eventos(valor)
                continue

            nome_contato = _obter_nome_contato(valor)

            for msg in mensagens:
                _processar_mensagem_unica(msg, nome_contato)

    return 'ok', 200


def _processar_mensagem_unica(msg, nome_contato):
    """
    Extrai telefone e texto de uma mensagem e chama o processador
    da conversa, respeitando o rate limit individual.
    """
    telefone = security.vetar_telefone(msg)
    if not telefone:
        logger.info('Mensagem sem telefone válido; ignorada.')
        return

    # Rate limit por remetente
    limiter = rate_limiter.get_rate_limiter()
    if not limiter.permitido(telefone):
        logger.warning(f"Mensagem ignorada por rate limit: tel={telefone}")
        return

    tipo = msg.get('type', '')
    texto = security.ler_corpo_msg(msg)
    mensagem_id = msg.get('id')

    try:
        processar_mensagem(
            telefone=telefone,
            texto_bruto=texto,
            mensagem_id=mensagem_id,
            nome_contato=nome_contato,
            tipo=tipo,
        )
    except Exception as e:  # pragma: no cover - defensivo
        # Erro na lógica não deve derrubar o processamento das demais mensagens
        logger.error(f"Erro ao processar mensagem {telefone}: {str(e)[:300]}",
                     exc_info=True)


def _obter_nome_contato(valor):
    """Extrai o nome do contato (perfil do remetente) do payload."""
    try:
        contatos = valor.get('contacts') or []
        if contatos:
            perfil = contatos[0].get('profile') or {}
            return perfil.get('name')
    except (AttributeError, TypeError, IndexError):
        pass
    return None


def _tratar_outros_eventos(valor):
    """
    Eventos que não são mensagens de texto (ex.: status de entrega,
    presença/recebimento, mudanças de configuração). Apenas logamos.
    """
    statuses = (valor.get('statuses') or [])
    if statuses:
        for st in statuses:
            logger.info(f"Evento de status WhatsApp: {st.get('status')}")
    return
