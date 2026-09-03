import pytest
import os
import sys

# Adiciona a raiz do projeto (que contém o pacote `backend`) ao sys.path
# backend/tests -> . (tests) -> .. (backend) -> ../.. (maeprojeto)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


@pytest.fixture
def app():
    """Cria a aplicação Flask para testes."""
    from backend import create_app
    from backend.config import TestingConfig
    from backend.database import db as _database

    app = create_app(TestingConfig)

    with app.app_context():
        _database.create_all()
        yield app
        _database.session.remove()
        _database.drop_all()


@pytest.fixture
def client(app):
    """Cliente de teste Flask."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Sessão de banco para testes."""
    from backend.database import db as _database
    with app.app_context():
        yield _database
