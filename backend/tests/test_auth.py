"""Testes de integração para autenticação."""
import pytest


def _login(client, email='admin@agenda.com', senha='Senha123456'):
    """Faz login e retorna a resposta."""
    return client.post('/auth/login', data={
        'email': email,
        'senha': senha
    }, follow_redirects=True)


class TestLogin:
    """Testes para o fluxo de login."""

    def test_login_sucesso(self, client):
        resp = _login(client)
        assert resp.status_code == 200
        assert b'Dashboard' in resp.data

    def test_login_errado(self, client):
        resp = _login(client, email='admin@agenda.com', senha='senha-errada')
        assert resp.status_code == 200
        # Deve permanecer na página de login (mensagem de erro)
        assert b'Login' in resp.data

    def test_acesso_sem_login_redireciona(self, client):
        resp = client.get('/dashboard')
        assert resp.status_code == 302


class TestPaginasProtegidas:
    """Testes para páginas que exigem autenticação."""

    def test_dashboard_requer_login(self, client):
        resp = client.get('/dashboard')
        assert resp.status_code == 302  # redireciona para login

    def test_dashboard_logado(self, client):
        _login(client)
        resp = client.get('/dashboard')
        assert resp.status_code == 200
        assert b'Dashboard' in resp.data


class TestLogout:
    """Testes para logout."""

    def test_logout(self, client):
        _login(client)
        resp = client.post('/auth/logout', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Login' in resp.data
