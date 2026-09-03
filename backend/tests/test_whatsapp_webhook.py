"""
Testes do webhook da WhatsApp Business Cloud API.

Cobrem o handshake de verificação (GET) e o recebimento de
mensagens (POST), incluindo validação de assinatura HMAC-SHA256
e compatibilidade com o CSRF (que deve estar eximido).
"""
import hashlib
import hmac
import json

import pytest


def _configurar_webhook(app, verify='meu-verify-token', segredo='meu-segredo'):
    """Configura as variáveis do webhook na aplicação para os testes."""
    app.config['WHATSAPP_VERIFY_TOKEN'] = verify
    app.config['WHATSAPP_WEBHOOK_SECRET'] = segredo
    app.config['WHATSAPP_DRY_RUN'] = True
    # Garante que o rate limit não bloqueie os testes
    app.config['WHATSAPP_RATE_LIMIT_MAX'] = 1000
    from backend.whatsapp import rate_limiter
    rate_limiter.resetar_rate_limiter()


def _post_payload(texto='menu', telefone='5511999999999', tipo='text'):
    """Monta o payload JSON de uma mensagem de texto do WhatsApp."""
    corpo = {
        'object': 'whatsapp_business_account',
        'entry': [{
            'changes': [{
                'value': {
                    'messaging_product': 'whatsapp',
                    'contacts': [{'profile': {'name': 'Maria Teste'}}],
                    'messages': [{
                        'from': telefone,
                        'id': 'wamid-teste-1',
                        'type': tipo,
                        'text': {'body': texto},
                    }],
                }
            }]
        }]
    }
    return json.dumps(corpo)


def _assinatura(segredo, corpo):
    """Gera o header X-Hub-Signature-256 para o corpo (bytes/str)."""
    if isinstance(corpo, str):
        corpo = corpo.encode('utf-8')
    digest = hmac.new(segredo.encode('utf-8'), corpo, hashlib.sha256).hexdigest()
    return f'sha256={digest}'


class TestHandshake:
    """Validação do token de verificação (GET)."""

    def test_verify_token_correto(self, app, client):
        _configurar_webhook(app)
        resp = client.get(
            '/api/whatsapp/webhook?hub.mode=subscribe'
            '&hub.verify_token=meu-verify-token&hub.challenge=12345'
        )
        assert resp.status_code == 200
        assert resp.data == b'12345'

    def test_verify_token_errado(self, app, client):
        _configurar_webhook(app)
        resp = client.get(
            '/api/whatsapp/webhook?hub.mode=subscribe'
            '&hub.verify_token=errado&hub.challenge=12345'
        )
        assert resp.status_code == 403

    def test_mode_incorreto(self, app, client):
        _configurar_webhook(app)
        resp = client.get(
            '/api/whatsapp/webhook?hub.mode=nada'
            '&hub.verify_token=meu-verify-token&hub.challenge=12345'
        )
        assert resp.status_code == 403

    def test_sem_verify_configurado(self, app, client):
        _configurar_webhook(app, verify='', segredo='')
        resp = client.get(
            '/api/whatsapp/webhook?hub.mode=subscribe'
            '&hub.verify_token=x&hub.challenge=12345'
        )
        assert resp.status_code == 500


class TestReceberMensagem:
    """Recebimento e validação de mensagens (POST)."""

    def test_post_assinatura_valida(self, app, client):
        _configurar_webhook(app)
        corpo = _post_payload('menu')
        resp = client.post(
            '/api/whatsapp/webhook',
            data=corpo,
            content_type='application/json',
            headers={'X-Hub-Signature-256': _assinatura('meu-segredo', corpo)},
        )
        assert resp.status_code == 200
        assert resp.data == b'ok'

    def test_post_assinatura_invalida(self, app, client):
        _configurar_webhook(app)
        corpo = _post_payload('menu')
        resp = client.post(
            '/api/whatsapp/webhook',
            data=corpo,
            content_type='application/json',
            headers={'X-Hub-Signature-256': 'sha256=0000deadbeef'},
        )
        assert resp.status_code == 403

    def test_post_sem_assinatura_rejeita(self, app, client):
        _configurar_webhook(app)
        corpo = _post_payload('menu')
        resp = client.post(
            '/api/whatsapp/webhook',
            data=corpo,
            content_type='application/json',
        )
        assert resp.status_code == 403

    def test_post_sem_segredo_configurado_aceita(self, app, client):
        # Sem segredo configurado, a validação de assinatura é ignorada
        _configurar_webhook(app, segredo='')
        corpo = _post_payload('menu')
        resp = client.post(
            '/api/whatsapp/webhook',
            data=corpo,
            content_type='application/json',
        )
        assert resp.status_code == 200

    def test_post_evento_de_status(self, app, client):
        _configurar_webhook(app)
        # Evento sem 'messages' (ex.: status de entrega) deve responder ok
        corpo = json.dumps({
            'object': 'whatsapp_business_account',
            'entry': [{
                'changes': [{
                    'value': {
                        'messaging_product': 'whatsapp',
                        'statuses': [{'id': 'wamid-x', 'status': 'delivered'}],
                    }
                }]
            }]
        })
        resp = client.post(
            '/api/whatsapp/webhook',
            data=corpo,
            content_type='application/json',
            headers={'X-Hub-Signature-256': _assinatura('meu-segredo', corpo)},
        )
        assert resp.status_code == 200

    def test_post_payload_vazio(self, app, client):
        _configurar_webhook(app)
        corpo = json.dumps({})
        resp = client.post(
            '/api/whatsapp/webhook',
            data=corpo,
            content_type='application/json',
            headers={'X-Hub-Signature-256': _assinatura('meu-segredo', corpo)},
        )
        assert resp.status_code == 200

    def test_post_com_csrf_eximido(self, app, client):
        # Garante que o CSRF não bloqueia o webhook (a rota deve estar eximida)
        _configurar_webhook(app, segredo='')
        corpo = _post_payload('menu')
        resp = client.post(
            '/api/whatsapp/webhook',
            data=corpo,
            content_type='application/json',
        )
        # Sem segredo e sem CSRF ativo no TestingConfig, deve passar
        assert resp.status_code == 200
