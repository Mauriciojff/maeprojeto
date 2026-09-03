# ============================================
# DATABASE/__INIT__.PY — Gerenciamento do banco
# ============================================

import os
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from flask import current_app

# Instância SQLAlchemy (ORM)
db = SQLAlchemy()


# ============================================
# INICIALIZAÇÃO DO BANCO
# ============================================

def init_db():
    """
    Inicializa o banco de dados, criando tabelas
    e o usuário admin padrão se não existirem.
    """
    import os
    from flask import current_app

    # Garantir que o diretório do banco existe
    db_path = current_app.config['DB_PATH']
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    # Garantir que o diretório de logs existe
    log_dir = current_app.config.get('LOG_DIR')
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    from .models import Cliente, Servico, Agendamento, Usuario, Configuracao, Faturamento
    from .wpp_models import (
        MensagemRecebida, MensagemEnviada, SessaoConversa,
        LogAuditoria, ConfigWhatsApp
    )

    db.create_all()

    # Criar usuário admin padrão
    admin = Usuario.query.filter_by(email='admin@agenda.com').first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin = Usuario(
            email='admin@agenda.com',
            senha_hash=generate_password_hash('Senha123456'),
            nome='Administrador',
            role='admin'
        )
        db.session.add(admin)
        db.session.flush()

    # Criar serviços padrão
    if Servico.query.count() == 0:
        servicos = [
            Servico(nome='Manicure', preco=40.00, duracao_min=60, ativo=True),
            Servico(nome='Cílios', preco=80.00, duracao_min=60, ativo=True),
            Servico(nome='Manicure + Cílios', preco=110.00, duracao_min=120, ativo=True),
        ]
        db.session.add_all(servicos)

    # Configurações padrão
    padrao = {
        'hora_abertura': '08:00',
        'hora_fechamento': '20:00',
        'intervalo_min': '60'
    }
    for chave, valor in padrao.items():
        if not Configuracao.query.filter_by(chave=chave).first():
            db.session.add(Configuracao(chave=chave, valor=valor))

    db.session.commit()


# ============================================
# UTILITÁRIOS DE CONEXÃO (para queries diretas)
# ============================================

def get_connection():
    """Obtém uma conexão direta com o SQLite."""
    path = current_app.config['DB_PATH']
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn
