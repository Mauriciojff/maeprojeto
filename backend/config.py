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

    # WhatsApp (integração por link wa.me)
    WHATSAPP_BASE = os.getenv('WHATSAPP_BASE', 'https://wa.me')
    WHATSAPP_DDI = os.getenv('WHATSAPP_DDI', '55')

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
