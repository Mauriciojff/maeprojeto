# ============================================
# ROUTES/FATURAMENTO.PY — Relatórios de faturamento
# ============================================

from flask import Blueprint, render_template, request
from datetime import datetime, date, timedelta

from ..database.models import Faturamento, Cliente, Servico
from ..database import db
from ..utils.decorators import login_required
from ..utils.helpers import formatar_moeda, formatar_data_br

faturamento_bp = Blueprint('faturamento', __name__)

MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']


@faturamento_bp.route('/')
@login_required
def relatorio():
    """Painel de faturamento com relatórios por período."""
    periodo = request.args.get('periodo', 'mes')  # dia | semana | mes | ano | custom
    hoje = date.today()

    data_inicio_str = request.args.get('de', '')
    data_fim_str = request.args.get('ate', '')

    # Determinar período
    if periodo == 'custom' and data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            data_inicio = hoje.replace(day=1)
            data_fim = hoje
    elif periodo == 'dia':
        data_inicio = data_fim = hoje
    elif periodo == 'semana':
        dias_desde_seg = hoje.weekday()
        data_inicio = hoje - timedelta(days=dias_desde_seg)
        data_fim = data_inicio + timedelta(days=6)
    elif periodo == 'ano':
        data_inicio = date(hoje.year, 1, 1)
        data_fim = hoje
    else:  # mês padrão
        data_inicio = hoje.replace(day=1)
        data_fim = hoje

    # Consultar faturamento do período
    registros = Faturamento.query.filter(
        Faturamento.data_realizacao >= data_inicio,
        Faturamento.data_realizacao <= data_fim
    ).order_by(Faturamento.data_realizacao, Faturamento.id).all()

    # Totais
    total_periodo = sum(float(r.preco) for r in registros)
    total_servicos = len(registros)

    # Montar informações detalhadas
    clientes = {c.id: c.nome for c in Cliente.query.all()}
    servicos = {s.id: s.nome for s in Servico.query.all()}

    detalhes = []
    for r in registros:
        detalhes.append({
            'id': r.id,
            'cliente': clientes.get(r.cliente_id, 'Cliente'),
            'servico': servicos.get(r.servico_id, 'Serviço'),
            'preco': float(r.preco),
            'data': r.data_realizacao
        })

    # Faturamento por serviço
    por_servico = {}
    for r in registros:
        nome = servicos.get(r.servico_id, 'Serviço')
        if nome not in por_servico:
            por_servico[nome] = {'quantidade': 0, 'total': 0.0}
        por_servico[nome]['quantidade'] += 1
        por_servico[nome]['total'] += float(r.preco)

    # Faturamento por dia (para gráfico)
    por_dia = {}
    for r in registros:
        chave = r.data_realizacao.isoformat() if r.data_realizacao else ''
        if chave not in por_dia:
            por_dia[chave] = 0.0
        por_dia[chave] += float(r.preco)
    por_dia = dict(sorted(por_dia.items()))

    # Comparação com período anterior
    dias_periodo = (data_fim - data_inicio).days + 1
    periodo_anterior_inicio = data_inicio - timedelta(days=dias_periodo)
    periodo_anterior_fim = data_inicio - timedelta(days=1)
    total_anterior = db.session.query(
        db.func.sum(Faturamento.preco)
    ).filter(
        Faturamento.data_realizacao >= periodo_anterior_inicio,
        Faturamento.data_realizacao <= periodo_anterior_fim
    ).scalar() or 0
    total_anterior = float(total_anterior)

    if total_anterior > 0:
        variacao = ((total_periodo - total_anterior) / total_anterior) * 100
    else:
        variacao = 100.0 if total_periodo > 0 else 0.0

    return render_template(
        'faturamento.html',
        periodo=periodo,
        data_inicio=data_inicio,
        data_fim=data_fim,
        total_periodo=total_periodo,
        total_servicos=total_servicos,
        detalhes=detalhes,
        por_servico=por_servico,
        por_dia=por_dia,
        variacao=variacao,
        total_anterior=total_anterior,
        MESES=MESES,
        formatar_moeda=formatar_moeda,
        formatar_data_br=formatar_data_br
    )

