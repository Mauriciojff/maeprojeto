"""Testes de unidade para funções utilitárias."""
import pytest


class TestFormatarMoeda:
    """Testes para formatar_moeda."""

    def test_valor_normal(self):
        from backend.utils.helpers import formatar_moeda
        assert formatar_moeda(40.00) == 'R$ 40,00'

    def test_valor_grande(self):
        from backend.utils.helpers import formatar_moeda
        assert formatar_moeda(1234.56) == 'R$ 1.234,56'

    def test_valor_zero(self):
        from backend.utils.helpers import formatar_moeda
        assert formatar_moeda(0) == 'R$ 0,00'

    def test_none(self):
        from backend.utils.helpers import formatar_moeda
        assert formatar_moeda(None) == 'R$ 0,00'

    def test_string_invalida(self):
        from backend.utils.helpers import formatar_moeda
        assert formatar_moeda('abc') == 'R$ 0,00'


class TestFormatarDataBr:
    """Testes para formatar_data_br."""

    def test_data_iso(self):
        from backend.utils.helpers import formatar_data_br
        assert formatar_data_br('2025-01-15') == '15/01/2025'

    def test_none(self):
        from backend.utils.helpers import formatar_data_br
        assert formatar_data_br(None) == ''

    def test_string_invalida(self):
        from backend.utils.helpers import formatar_data_br
        assert formatar_data_br('abc') == 'abc'


class TestTelefoneLimpo:
    """Testes para telefone_limpo."""

    def test_com_formatacao(self):
        from backend.utils.helpers import telefone_limpo
        assert telefone_limpo('(11) 99999-8888') == '11999998888'

    def test_sem_formatacao(self):
        from backend.utils.helpers import telefone_limpo
        assert telefone_limpo('11999998888') == '11999998888'

    def test_none(self):
        from backend.utils.helpers import telefone_limpo
        assert telefone_limpo(None) == ''

    def test_vazio(self):
        from backend.utils.helpers import telefone_limpo
        assert telefone_limpo('') == ''


class TestGerarHorarios:
    """Testes para gerar_horarios."""

    def test_padrao(self):
        from backend.utils.helpers import gerar_horarios
        horarios = gerar_horarios('08:00', '11:00', 60)
        assert horarios == ['08:00', '09:00', '10:00']

    def test_intervalo_30(self):
        from backend.utils.helpers import gerar_horarios
        horarios = gerar_horarios('08:00', '09:30', 30)
        assert horarios == ['08:00', '08:30', '09:00']

    def test_invalido(self):
        from backend.utils.helpers import gerar_horarios
        horarios = gerar_horarios('abc', 'def', 60)
        assert isinstance(horarios, list)
