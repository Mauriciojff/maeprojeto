# ============================================
# ROUTES/AGENDAMENTOS.PY — CRUD de agendamentos
# com prevenção de conflitos de horário
# ============================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date

from ..database.models import Agendamento, Cliente, Servico, Faturamento
from ..database import db
from ..utils.decorators import login_required
from ..utils.security import sanitize_input
from ..utils.helpers import get_config, formatar_data_br, formatar_moeda
import logging

logger = logging.getLogger('agenda_mae')

agendamentos_bp = Blueprint('agendamentos', __name__)


def verificar_conflito(data, horario, servico_id, ignorar_id=None):
    """
    Verifica se há conflito de horário considerando a duração do serviço.
    Retorna o agendamento conflitante ou None.
    """
    servico = Servico.query.get(servico_id)
    duracao = servico.duracao_min if servico else 60

    try:
        h, m = map(int, horario.split(':'))
    except (ValueError, AttributeError):
        return None
    novo_inicio = h * 60 + m
    novo_fim = novo_inicio + duracao

    agendamentos = Agendamento.query.filter(
        Agendamento.data == data,
        Agendamento.status.notin_(['cancelada', 'nao_vai'])
    ).all()

    for ag in agendamentos:
        if ignorar_id and ag.id == ignorar_id:
            continue
        servico_existente = Servico.query.get(ag.servico_id)
        dur_exist = servico_existente.duracao_min if servico_existente else 60
        try:
            eh, em = map(int, ag.horario.split(':'))
        except (ValueError, AttributeError):
            continue
        exist_inicio = eh * 60 + em
        exist_fim = exist_inicio + dur_exist
        if novo_inicio < exist_fim and exist_inicio < novo_fim:
            return ag
    return None


def _get_config_horarios():
    """Obtém configurações de horário do banco."""
    return {
        'hora_abertura': get_config('hora_abertura', '08:00'),
        'hora_fechamento': get_config('hora_fechamento', '20:00'),
        'intervalo_min': int(get_config('intervalo_min', '60'))
    }


def _gerar_horarios_lista(config):
    """Gera lista de horários baseado na configuração."""
    from ..utils.helpers import gerar_horarios
    return gerar_horarios(
        config.get('hora_abertura', '08:00'),
        config.get('hora_fechamento', '20:00'),
        int(config.get('intervalo_min', '60'))
    )


# ============================================
# LISTAGEM
# ============================================

@agendamentos_bp.route('/')
@login_required
def listar():
    """Lista agendamentos com filtros."""
    data_filtro = request.args.get('data', '')
    status_filtro = request.args.get('status', '')
    cliente_filtro = request.args.get('cliente', '')

    query = Agendamento.query

    if data_filtro:
        try:
            data = datetime.strptime(data_filtro, '%Y-%m-%d').date()
            query = query.filter(Agendamento.data == data)
        except ValueError:
            flash('Data inválida.', 'error')

    if status_filtro:
        query = query.filter(Agendamento.status == status_filtro)

    if cliente_filtro:
        try:
            query = query.filter(Agendamento.cliente_id == int(cliente_filtro))
        except ValueError:
            pass

    agendamentos = query.order_by(Agendamento.data, Agendamento.horario).all()
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()

    return render_template(
        'agendamentos.html',
        agendamentos=agendamentos,
        clientes=clientes,
        data_filtro=data_filtro,
        status_filtro=status_filtro,
        cliente_filtro=cliente_filtro,
        formatar_moeda=formatar_moeda,
        formatar_data_br=formatar_data_br
    )


# ============================================
# CRIAÇÃO
# ============================================

@agendamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Cria um novo agendamento."""
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    servicos = Servico.query.filter_by(ativo=True).order_by(Servico.nome).all()
    config = _get_config_horarios()
    horarios = _gerar_horarios_lista(config)

    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id', '')
        servico_id = request.form.get('servico_id', '')
        data_str = request.form.get('data', '')
        horario = request.form.get('horario', '')
        status = request.form.get('status', 'pendente')
        obs = sanitize_input(request.form.get('obs', ''), 1000)

        erros = []
        try:
            cliente_id = int(cliente_id)
        except (ValueError, TypeError):
            cliente_id = None
            erros.append('Selecione um cliente.')

        try:
            servico_id = int(servico_id)
        except (ValueError, TypeError):
            servico_id = None
            erros.append('Selecione um serviço.')

        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            data = None
            erros.append('Data inválida.')

        if not horario:
            erros.append('Selecione um horário.')

        if status not in ['pendente', 'confirmada', 'cancelada', 'nao_vai', 'realizada']:
            status = 'pendente'

        # Verificar conflito de horário
        if data and horario and servico_id:
            conflito = verificar_conflito(data, horario, servico_id)
            if conflito:
                cliente_conflito = Cliente.query.get(conflito.cliente_id)
                erros.append(
                    f'Conflito de horário! {cliente_conflito.nome if cliente_conflito else "Cliente"} '
                    f'já tem agendamento às {conflito.horario}.'
                )

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template(
                'agendamento_form.html',
                clientes=clientes, servicos=servicos, horarios=horarios,
                agendamento=None, form=request.form
            )

        servico = Servico.query.get(servico_id) if servico_id else None
        preco = servico.preco if servico else 0

        agendamento = Agendamento(
            cliente_id=cliente_id,
            servico_id=servico_id,
            data=data,
            horario=horario,
            status=status,
            obs=obs or None,
            preco=preco
        )
        db.session.add(agendamento)
        db.session.commit()

        logger.info(f'Agendamento criado: id={agendamento.id}')
        flash('Agendamento criado com sucesso!', 'success')
        return redirect(url_for('agendamentos.listar'))

    return render_template(
        'agendamento_form.html',
        clientes=clientes, servicos=servicos, horarios=horarios,
        agendamento=None, form={}
    )


# ============================================
# EDIÇÃO
# ============================================

@agendamentos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edita um agendamento existente."""
    agendamento = db.get_or_404(Agendamento, id)
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    servicos = Servico.query.filter_by(ativo=True).order_by(Servico.nome).all()
    config = _get_config_horarios()
    horarios = _gerar_horarios_lista(config)

    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id', '')
        servico_id = request.form.get('servico_id', '')
        data_str = request.form.get('data', '')
        horario = request.form.get('horario', '')
        status = request.form.get('status', agendamento.status)
        obs = sanitize_input(request.form.get('obs', ''), 1000)

        erros = []
        try:
            cliente_id = int(cliente_id)
        except (ValueError, TypeError):
            cliente_id = None
            erros.append('Selecione um cliente.')

        try:
            servico_id = int(servico_id)
        except (ValueError, TypeError):
            servico_id = None
            erros.append('Selecione um serviço.')

        try:
            data = datetime.strptime(data_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            data = None
            erros.append('Data inválida.')

        if not horario:
            erros.append('Selecione um horário.')

        if status not in ['pendente', 'confirmada', 'cancelada', 'nao_vai', 'realizada']:
            status = agendamento.status

        # Verificar conflito (ignorando este agendamento)
        if data and horario and servico_id:
            conflito = verificar_conflito(data, horario, servico_id, ignorar_id=id)
            if conflito:
                cliente_conflito = Cliente.query.get(conflito.cliente_id)
                erros.append(
                    f'Conflito de horário! {cliente_conflito.nome if cliente_conflito else "Cliente"} '
                    f'já tem agendamento às {conflito.horario}.'
                )

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template(
                'agendamento_form.html',
                clientes=clientes, servicos=servicos, horarios=horarios,
                agendamento=agendamento, form=request.form
            )

        servico = Servico.query.get(servico_id) if servico_id else None
        status_anterior = agendamento.status

        agendamento.cliente_id = cliente_id
        agendamento.servico_id = servico_id
        agendamento.data = data
        agendamento.horario = horario
        agendamento.status = status
        agendamento.obs = obs or None
        agendamento.preco = servico.preco if servico else agendamento.preco

        db.session.commit()
        _atualizar_faturamento(agendamento, status_anterior)

        logger.info(f'Agendamento atualizado: id={agendamento.id}')
        flash('Agendamento atualizado com sucesso!', 'success')
        return redirect(url_for('agendamentos.listar'))

    return render_template(
        'agendamento_form.html',
        clientes=clientes, servicos=servicos, horarios=horarios,
        agendamento=agendamento, form={}
    )


# ============================================
# CANCELAMENTO / EXCLUSÃO / STATUS
# ============================================

@agendamentos_bp.route('/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar(id):
    """Cancela um agendamento."""
    agendamento = db.get_or_404(Agendamento, id)
    status_anterior = agendamento.status
    agendamento.status = 'cancelada'
    db.session.commit()
    _atualizar_faturamento(agendamento, status_anterior)

    logger.info(f'Agendamento cancelado: id={agendamento.id}')
    flash('Agendamento cancelado com sucesso.', 'success')
    return redirect(request.referrer or url_for('agendamentos.listar'))


@agendamentos_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    """Exclui definitivamente um agendamento."""
    agendamento = db.get_or_404(Agendamento, id)
    fat = Faturamento.query.filter_by(agendamento_id=id).first()
    if fat:
        db.session.delete(fat)
    db.session.delete(agendamento)
    db.session.commit()

    logger.info(f'Agendamento excluído: id={id}')
    flash('Agendamento excluído.', 'success')
    return redirect(request.referrer or url_for('agendamentos.listar'))


@agendamentos_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def mudar_status(id):
    """Altera o status de um agendamento."""
    agendamento = db.get_or_404(Agendamento, id)
    novo_status = request.form.get('status', '')
    status_anterior = agendamento.status

    if novo_status in ['pendente', 'confirmada', 'cancelada', 'nao_vai', 'realizada']:
        agendamento.status = novo_status
        if novo_status == 'confirmada':
            agendamento.data_confirmacao = datetime.utcnow()
        db.session.commit()
        _atualizar_faturamento(agendamento, status_anterior)
        flash('Status atualizado.', 'success')
    else:
        flash('Status inválido.', 'error')

    return redirect(request.referrer or url_for('agendamentos.listar'))


# ============================================
# API JSON
# ============================================

@agendamentos_bp.route('/api/disponiveis')
@login_required
def api_horarios_disponiveis():
    """Retorna horários disponíveis para uma data."""
    data_str = request.args.get('data', '')
    servico_id = request.args.get('servico_id', '')

    try:
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'erro': 'Data inválida'}), 400

    try:
        servico_id = int(servico_id)
    except (ValueError, TypeError):
        servico_id = None

    config = _get_config_horarios()
    horarios = _gerar_horarios_lista(config)

    disponiveis = []
    for h in horarios:
        if servico_id:
            conflito = verificar_conflito(data, h, servico_id)
            if conflito:
                continue
        disponiveis.append(h)

    if data == date.today():
        agora = datetime.now()
        disponiveis = [h for h in disponiveis if h > agora.strftime('%H:%M')]

    return jsonify({'horarios': disponiveis})


# ============================================
# HELPERS INTERNOS
# ============================================

def _atualizar_faturamento(agendamento, status_anterior):
    """
    Atualiza a tabela de faturamento conforme mudanças de status.
    """
    if agendamento.status == 'realizada':
        fat = Faturamento.query.filter_by(agendamento_id=agendamento.id).first()
        if not fat:
            fat = Faturamento(
                agendamento_id=agendamento.id,
                cliente_id=agendamento.cliente_id,
                servico_id=agendamento.servico_id,
                preco=agendamento.preco or 0,
                data_realizacao=agendamento.data
            )
            db.session.add(fat)
            db.session.commit()
    elif status_anterior == 'realizada' and agendamento.status != 'realizada':
        fat = Faturamento.query.filter_by(agendamento_id=agendamento.id).first()
        if fat:
            db.session.delete(fat)
            db.session.commit()
