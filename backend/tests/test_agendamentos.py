"""Testes para a lógica de agendamentos (conflitos de horário)."""
import pytest
from datetime import date


@pytest.fixture
def dados_base(db_session):
    """Cria dados base para os testes de agendamento."""
    from backend.database.models import Cliente, Servico

    cliente = Cliente(nome='Maria Teste', telefone='11999990000')
    db_session.session.add(cliente)
    db_session.session.flush()

    servico_60 = Servico(nome='Manicure Test', preco=40, duracao_min=60)
    servico_120 = Servico(nome='Combo Test', preco=110, duracao_min=120)
    db_session.session.add_all([servico_60, servico_120])
    db_session.session.flush()

    db_session.session.commit()

    return {
        'cliente': cliente,
        'servico_60': servico_60,
        'servico_120': servico_120
    }


def _criar_agendamento(db_session, dados, horario, servico=None):
    """Cria um agendamento no banco."""
    from backend.database.models import Agendamento
    servico = servico or dados['servico_60']
    ag = Agendamento(
        cliente_id=dados['cliente'].id,
        servico_id=servico.id,
        data=date(2025, 6, 15),
        horario=horario,
        status='confirmada',
        preco=servico.preco
    )
    db_session.session.add(ag)
    db_session.session.commit()
    return ag


class TestVerificarConflito:
    """Testes para a função verificar_conflito."""

    def test_sem_conflito(self, db_session, dados_base):
        from backend.routes.agendamentos import verificar_conflito

        _criar_agendamento(db_session, dados_base, '08:00')
        conflito = verificar_conflito(date(2025, 6, 15), '14:00', dados_base['servico_60'].id)
        assert conflito is None

    def test_conflito_horario_igual(self, db_session, dados_base):
        from backend.routes.agendamentos import verificar_conflito

        _criar_agendamento(db_session, dados_base, '08:00')
        conflito = verificar_conflito(date(2025, 6, 15), '08:00', dados_base['servico_60'].id)
        assert conflito is not None

    def test_conflito_sobreposto(self, db_session, dados_base):
        from backend.routes.agendamentos import verificar_conflito

        # Serviço de 60 min das 08:00 às 09:00
        _criar_agendamento(db_session, dados_base, '08:00')
        # Novo às 08:30 também conflita
        conflito = verificar_conflito(date(2025, 6, 15), '08:30', dados_base['servico_60'].id)
        assert conflito is not None

    def test_sem_conflito_fim_inicio(self, db_session, dados_base):
        from backend.routes.agendamentos import verificar_conflito

        # Serviço de 60 min das 08:00-09:00
        _criar_agendamento(db_session, dados_base, '08:00')
        # Novo às 09:00 começa exatamente quando o outro termina - sem conflito
        conflito = verificar_conflito(date(2025, 6, 15), '09:00', dados_base['servico_60'].id)
        assert conflito is None

    def test_datas_diferentes_sem_conflito(self, db_session, dados_base):
        from backend.routes.agendamentos import verificar_conflito

        _criar_agendamento(db_session, dados_base, '08:00')
        conflito = verificar_conflito(date(2025, 6, 16), '08:00', dados_base['servico_60'].id)
        assert conflito is None

    def test_ignorar_proprio_agendamento(self, db_session, dados_base):
        from backend.routes.agendamentos import verificar_conflito

        ag = _criar_agendamento(db_session, dados_base, '08:00')
        # Ao editar o mesmo agendamento, ele não deve conflitar consigo mesmo
        conflito = verificar_conflito(date(2025, 6, 15), '08:00', dados_base['servico_60'].id, ignorar_id=ag.id)
        assert conflito is None
