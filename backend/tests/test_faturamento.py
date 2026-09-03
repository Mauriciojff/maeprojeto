"""Testes para o sync de faturamento."""
import pytest
from datetime import date


@pytest.fixture
def agendamento(db_session):
    """Cria um agendamento com cliente e serviço."""
    from backend.database.models import Cliente, Servico, Agendamento

    cliente = Cliente(nome='Ana Teste', telefone='11999991111')
    db_session.session.add(cliente)
    db_session.session.flush()

    servico = Servico(nome='Cílios Test', preco=80, duracao_min=60)
    db_session.session.add(servico)
    db_session.session.flush()

    ag = Agendamento(
        cliente_id=cliente.id,
        servico_id=servico.id,
        data=date(2025, 6, 20),
        horario='10:00',
        status='pendente',
        preco=servico.preco
    )
    db_session.session.add(ag)
    db_session.session.commit()
    return ag


class TestSyncFaturamento:
    """Testa que mudar o status para 'realizada' cria um registro de faturamento."""

    def test_criar_faturamento_ao_realizar(self, db_session, agendamento):
        from backend.database.models import Faturamento
        from backend.routes.agendamentos import _atualizar_faturamento

        status_anterior = agendamento.status  # 'pendente'
        agendamento.status = 'realizada'
        db_session.session.commit()

        _atualizar_faturamento(agendamento, status_anterior)

        fat = Faturamento.query.filter_by(agendamento_id=agendamento.id).first()
        assert fat is not None
        assert fat.preco == 80
        assert fat.data_realizacao == date(2025, 6, 20)

    def test_remover_faturamento_ao_desfazer(self, db_session, agendamento):
        from backend.database.models import Faturamento
        from backend.routes.agendamentos import _atualizar_faturamento

        # Primeiro marcar como realizada
        agendamento.status = 'realizada'
        db_session.session.commit()
        _atualizar_faturamento(agendamento, 'pendente')

        assert Faturamento.query.filter_by(agendamento_id=agendamento.id).first() is not None

        # Agora desfazer
        status_anterior = 'realizada'
        agendamento.status = 'pendente'
        db_session.session.commit()
        _atualizar_faturamento(agendamento, status_anterior)

        assert Faturamento.query.filter_by(agendamento_id=agendamento.id).first() is None

    def test_nao_duplicar_faturamento(self, db_session, agendamento):
        from backend.database.models import Faturamento
        from backend.routes.agendamentos import _atualizar_faturamento

        agendamento.status = 'realizada'
        db_session.session.commit()
        _atualizar_faturamento(agendamento, 'pendente')
        _atualizar_faturamento(agendamento, 'realizada')

        registros = Faturamento.query.filter_by(agendamento_id=agendamento.id).all()
        assert len(registros) == 1
