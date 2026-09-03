# ============================================
# AGENDA DA MÃE — Backend Flask
# Aplicação de agendamento para manicure e cílios
# ============================================

from flask import Flask
from flask_wtf.csrf import CSRFProtect
import os
import logging
from logging.handlers import RotatingFileHandler

from .config import Config
from .database import db, init_db

# Proteção CSRF
csrf = CSRFProtect()


def create_app(config_class=Config):
    """
    Fábrica da aplicação Flask.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensões
    csrf.init_app(app)
    db.init_app(app)

    # Criar diretório de logs se necessário
    if not os.path.exists(app.config['LOG_DIR']):
        os.makedirs(app.config['LOG_DIR'])

    # Configurar logging
    _configurar_logging(app)

    # Garantir que o banco está inicializado
    with app.app_context():
        init_db()

    # Registrar blueprints
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.clientes import clientes_bp
    from .routes.agendamentos import agendamentos_bp
    from .routes.servicos import servicos_bp
    from .routes.agenda import agenda_bp
    from .routes.faturamento import faturamento_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(clientes_bp, url_prefix='/clientes')
    app.register_blueprint(agendamentos_bp, url_prefix='/agendamentos')
    app.register_blueprint(servicos_bp, url_prefix='/servicos')
    app.register_blueprint(agenda_bp, url_prefix='/agenda')
    app.register_blueprint(faturamento_bp, url_prefix='/faturamento')

    # Tratamento de erros
    _configurar_tratamento_erros(app)

    # Contextos globais para templates
    @app.context_processor
    def injetar_contexto_global():
        from datetime import datetime, timedelta
        from flask import request
        return {
            'now_year': datetime.now().year,
            'timedelta': timedelta,
            'request': request
        }

    return app


def _configurar_logging(app):
    """Configura o sistema de logging da aplicação."""
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Logger geral
    logger = logging.getLogger('agenda_mae')
    logger.setLevel(log_level.upper())

    # Handler de erro
    error_handler = RotatingFileHandler(
        os.path.join(app.config['LOG_DIR'], 'error.log'),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # Handler geral
    info_handler = RotatingFileHandler(
        os.path.join(app.config['LOG_DIR'], 'combined.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
        encoding='utf-8'
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    logger.addHandler(info_handler)

    # Console em dev
    if app.debug or app.config.get('ENV') == 'development':
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        logger.addHandler(console)


def _configurar_tratamento_erros(app):
    """Configura tratamento centralizado de erros."""
    from flask import render_template, request
    logger = logging.getLogger('agenda_mae')

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return {'erro': 'Recurso não encontrado'}, 404
        return render_template('erro.html', codigo=404, mensagem='Página não encontrada'), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f'Erro interno: {e}', exc_info=True)
        if request.path.startswith('/api/'):
            return {'erro': 'Erro interno do servidor'}, 500
        return render_template('erro.html', codigo=500, mensagem='Erro interno do servidor'), 500

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/'):
            return {'erro': 'Acesso negado'}, 403
        return render_template('erro.html', codigo=403, mensagem='Acesso negado'), 403

    @app.errorhandler(401)
    def unauthorized(e):
        if request.path.startswith('/api/'):
            return {'erro': 'Não autenticado'}, 401
        return render_template('erro.html', codigo=401, mensagem='Não autenticado'), 401
