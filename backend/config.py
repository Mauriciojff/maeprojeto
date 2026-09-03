# ============================================
# CONFIG.PY — Configurações da aplicação
# ============================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / '.env')


class Config:
    """Configurações base."""
    # Segurança
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave-secreta-padrao-mude-em-producao')
    WTF_CSRF_ENABLED = os.getenv('CSRF_ENABLED', 'true').lower() == 'true'

    # Banco de dados
    DB_PATH = os.getenv('DB_PATH', str(BASE_DIR / 'data' / 'agenda.db'))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Logs
    LOG_DIR = os.getenv('LOG_DIR', str(BASE_DIR / 'logs'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Sessão
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7 dias

    # Ambiente
    ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    TESTING = os.getenv('FLASK_TESTING', 'false').lower() == 'true'

    # Validação de senha
    MIN_SENHA_LENGTH = 8

    # Horário padrão
    HORA_ABERTURA = os.getenv('HORA_ABERTURA', '08:00')
    HORA_FECHAMENTO = os.getenv('HORA_FECHAMENTO', '20:00')
    INTERVALO_MIN = int(os.getenv('INTERVALO_MIN', '60'))

    # WhatsApp (integração por link wa.me - legado)
    WHATSAPP_BASE = os.getenv('WHATSAPP_BASE', 'https://wa.me')
    WHATSAPP_DDI = os.getenv('WHATSAPP_DDI', '55')

    # ----------------------------------------------------------
    # WhatsApp Business Cloud API (integração oficial)
    # ----------------------------------------------------------
    # Token de acesso permanente do app Meta (System User / WhatsApp)
    WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN', '')
    # ID do número de telefone da empresa (Phone Number ID)
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
    # Token de verificação para o handshake do webhook (GET)
    WHATSAPP_VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN', '')
    # Segredo usado para validar a assinatura X-Hub-Signature-256 dos webhooks
    WHATSAPP_WEBHOOK_SECRET = os.getenv('WHATSAPP_WEBHOOK_SECRET', '')
    # Números de WhatsApp autorizados a usar comandos administrativos
    # (separados por vírgula, no formato 5511999999999)
    ADMIN_WHATSAPP_NUMBERS = os.getenv('ADMIN_WHATSAPP_NUMBERS', '')
    # URL base da Graph API
    WHATSAPP_GRAPH_API = os.getenv(
        'WHATSAPP_GRAPH_API',
        'https://graph.facebook.com/v19.0'
    )
    # Versão da API (usada nas URLs)
    WHATSAPP_API_VERSION = os.getenv('WHATSAPP_API_VERSION', 'v19.0')
    # Habilitar/desabilitar o envio real de mensagens (útil em dev/testes)
    WHATSAPP_DRY_RUN = os.getenv('WHATSAPP_DRY_RUN', 'false').lower() == 'true'

    # Rate limiting do webhook do WhatsApp
    WHATSAPP_RATE_LIMIT_WINDOW = int(os.getenv('WHATSAPP_RATE_LIMIT_WINDOW', '60'))
    WHATSAPP_RATE_LIMIT_MAX = int(os.getenv('WHATSAPP_RATE_LIMIT_MAX', '60'))

    # Máximo de tentativas de login
    MAX_LOGIN_ATTEMPTS = 5


class DevelopmentConfig(Config):
    """Configuração de desenvolvimento."""
    DEBUG = True


class ProductionConfig(Config):
    """Configuração de produção."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configuração de testes."""
    TESTING = True
    DB_PATH = str(BASE_DIR / 'data' / 'test_agenda.db')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = 'ERROR'
