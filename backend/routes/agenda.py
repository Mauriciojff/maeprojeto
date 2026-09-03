# ============================================
# ROUTES/AGENDA.PY — Visualização do calendário
# (dia / semana / mês)
# ============================================

from flask import Blueprint, render_template, request
from datetime import datetime, date, timedelta

from ..database.models import Agendamento, Cliente, Servico
from ..utils.decorators import login_required
from ..utils.helpers import get_config, gerar_horarios
import calendar as cal

agenda_bp = Blueprint('agenda', __name__)

DIAS_SEMANA = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']


def _get_config_horarios():
    return {
        'hora_abertura': get_config('hora_abertura', '08:00'),
        'hora_fechamento': get_config('hora_fechamento', '20:00'),
        'intervalo_min': int(get_config('intervalo_min', '60'))
    }


@agenda_bp.route('/')
@login_required
def visualizar():
    """Página principal da agenda (visão semana por padrão)."""
    visao = request.args.get('visao', 'semana')  # dia | semana | mes
    data_str = request.args.get('data', '')
    data_atual = date.today()

    # Determinar data de referência
    try:
        if data_str:
            data_ref = datetime.strptime(data_str, '%Y-%m-%d').date()
        else:
            data_ref = data_atual
    except ValueError:
        data_ref = data_atual

    return render_template(
        'agenda.html',
        visao=visao,
        data_ref=data_ref,
        data_atual=data_atual,
        DIAS_SEMANA=DIAS_SEMANA,
        MESES=MESES
    )


# ============================================
# DADOS PARA RENDERIZAÇÃO (API auxiliar via templates)
# ============================================

@agenda_bp.route('/dados')
@login_required
def dados():
    """
    Retorna os dados necessários para montar a visualização.
    Parâmetros: visao, data.
    """
    visao = request.args.get('visao', 'semana')
    data_str = request.args.get('data', '')
    data_ref = date.today()

    try:
        data_ref = datetime.strptime(data_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass

    # Determinar período a consultar
    if visao == 'dia':
        data_inicio = data_ref
        data_fim = data_ref
        dias_headers = [data_ref]
    elif visao == 'semana':
        # Semana começa na segunda-feira
        dias_desde_seg = data_ref.weekday()
        data_inicio = data_ref - timedelta(days=dias_desde_seg)
        data_fim = data_inicio + timedelta(days=6)
        dias_headers = [data_inicio + timedelta(days=i) for i in range(7)]
    else:  # mês
        data_inicio = data_ref.replace(day=1)
        ultimo_dia = cal.monthrange(data_ref.year, data_ref.month)[1]
        data_fim = data_ref.replace(day=ultimo_dia)
        dias_headers = [data_inicio + timedelta(days=i) for i in range(ultimo_dia)]

    # Buscar agendamentos do período
    agendamentos = Agendamento.query.filter(
        Agendamento.data >= data_inicio,
        Agendamento.data <= data_fim,
        Agendamento.status.notin_(['cancelada'])
    ).order_by(Agendamento.data, Agendamento.horario).all()

    # Obter informações dos clientes
    clientes = {c.id: c.nome for c in Cliente.query.filter_by(ativo=True).all()}

    # Configuração para gerar horários
    config = _get_config_horarios()
    horarios = gerar_horarios(config['hora_abertura'], config['hora_fechamento'], config['intervalo_min'])

    # Estruturar agendamentos por data
    agendamentos_por_dia = {}
    for ag in agendamentos:
        chave = ag.data.isoformat()
        if chave not in agendamentos_por_dia:
            agendamentos_por_dia[chave] = []
        agendamentos_por_dia[chave].append({
            'id': ag.id,
            'cliente': clientes.get(ag.cliente_id, 'Cliente'),
            'cliente_id': ag.cliente_id,
            'servico': ag.servico.nome if ag.servico else '',
            'servico_id': ag.servico_id,
            'horario': ag.horario,
            'status': ag.status,
            'preco': float(ag.preco) if ag.preco else 0
        })

    return {
        'horarios': horarios,
        'agendamentos': agendamentos_por_dia,
        'dias': [d.isoformat() for d in dias_headers],
    }
