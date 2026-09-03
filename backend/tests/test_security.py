"""Testes para funções de segurança."""
import pytest


class TestSanitizeInput:
    """Testes para sanitize_input."""

    def test_html_escaping(self):
        from backend.utils.security import sanitize_input
        assert sanitize_input('<script>alert(1)</script>') == '&lt;script&gt;alert(1)&lt;/script&gt;'

    def test_limit_tamanho(self):
        from backend.utils.security import sanitize_input
        valor = 'a' * 100
        assert len(sanitize_input(valor, max_len=10)) == 10

    def test_none(self):
        from backend.utils.security import sanitize_input
        assert sanitize_input(None) is None

    def test_texto_normal(self):
        from backend.utils.security import sanitize_input
        assert sanitize_input('Olá mundo') == 'Olá mundo'


class TestIsSafePassword:
    """Testes para is_safe_password."""

    def test_senha_forte(self):
        from backend.utils.security import is_safe_password
        assert is_safe_password('Senha123')

    def test_senha_curta(self):
        from backend.utils.security import is_safe_password
        assert not is_safe_password('Ab1')

    def test_sem_maiuscula(self):
        from backend.utils.security import is_safe_password
        assert not is_safe_password('senha1234')

    def test_sem_numero(self):
        from backend.utils.security import is_safe_password
        assert not is_safe_password('SenhaForte')

    def test_senha_comum(self):
        from backend.utils.security import is_safe_password
        assert not is_safe_password('Senha123456')


class TestIsValidTelefone:
    """Testes para is_valid_telefone."""

    def test_telefone_valido(self):
        from backend.utils.security import is_valid_telefone
        assert is_valid_telefone('(11) 99999-8888')

    def test_telefone_invalido_curto(self):
        from backend.utils.security import is_valid_telefone
        assert not is_valid_telefone('1234')

    def test_telefone_vazio(self):
        from backend.utils.security import is_valid_telefone
        assert is_valid_telefone('')


class TestIsValidEmail:
    """Testes para is_valid_email."""

    def test_email_valido(self):
        from backend.utils.security import is_valid_email
        assert is_valid_email('teste@exemplo.com')

    def test_email_invalido(self):
        from backend.utils.security import is_valid_email
        assert not is_valid_email('teste@exemplo')

    def test_email_vazio(self):
        from backend.utils.security import is_valid_email
        assert is_valid_email('')
