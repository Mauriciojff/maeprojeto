# ============================================
# ROUTES/MAIN.PY — Rotas principais (páginas)
# ============================================

from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, session

from ..database.models import Cliente, Servico, Agendamento, Faturamento
from ..utils.decorators import login_required, admin_required
from ..utils.helpers import get_config, formatar_moeda
from ..database import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Redireciona para página correta."""
    if session.get('usuario_id'):
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Painel administrativo com resumo geral."""
    hoje = date.today()

    # Total de clientes ativos
    total_clientes = Cliente.query.filter_by(ativo=True).count()

    # Agendamentos do dia
    agendamentos_hoje = Agendamento.query.filter_by(data=hoje).order_by(Agendamento.horario).all()

    # Faturamento do dia (agendamentos realizados)
    faturamento_hoje = db.session.query(
        db.func.sum(Faturamento.preco)
    ).filter(Faturamento.data_realizacao == hoje).scalar() or 0

    # Faturamento do mês
    inicio_mes = hoje.replace(day=1)
    faturamento_mes = db.session.query(
        db.func.sum(Faturamento.preco)
    ).filter(Faturamento.data_realizacao >= inicio_mes).scalar() or 0

    # Faturamento do ano
    inicio_ano = date(hoje.year, 1, 1)
    faturamento_ano = db.session.query(
        db.func.sum(Faturamento.preco)
    ).filter(Faturamento.data_realizacao >= inicio_ano).scalar() or 0

    # Serviços mais utilizados (mês atual)
    servicos_mais_usados = db.session.query(
        Faturamento.servico_id,
        db.func.count(Faturamento.id).label('total'),
        db.func.sum(Faturamento.preco).label('valor_total')
    ).filter(Faturamento.data_realizacao >= inicio_mes).group_by(Faturamento.servico_id).order_by(
        db.desc('total')
    ).limit(5).all()

    servicos_top = []
    for item in servicos_mais_usados:
        servico = Servico.query.get(item.servico_id)
        servicos_top.append({
            'nome': servico.nome if servico else 'Desconhecido',
            'total': item.total,
            'valor_total': float(item.valor_total or 0)
        })

    # Próximos agendamentos
    proximos = Agendamento.query.filter(
        Agendamento.data >= hoje,
        Agendamento.status.in_(['pendente', 'confirmada'])
    ).order_by(Agendamento.data, Agendamento.horario).limit(8).all()

    # Agendamentos por status
    stats_status = {}
    for status in ['pendente', 'confirmada', 'realizada', 'cancelada', 'nao_vai']:
        stats_status[status] = Agendamento.query.filter_by(status=status).count()

    return render_template(
        'dashboard.html',
        total_clientes=total_clientes,
        agendamentos_hoje=agendamentos_hoje,
        faturamento_hoje=faturamento_hoje,
        faturamento_mes=faturamento_mes,
        faturamento_ano=faturamento_ano,
        servicos_top=servicos_top,
        proximos=proximos,
        stats_status=stats_status,
        hoje=hoje,
        formatar_moeda=formatar_moeda
    )
