# ============================================
# ROUTES/SERVICOS.PY — Cadastro de serviços
# ============================================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from decimal import Decimal, InvalidOperation

from ..database.models import Servico
from ..database import db
from ..utils.decorators import login_required
from ..utils.security import sanitize_input
import logging

logger = logging.getLogger('agenda_mae')

servicos_bp = Blueprint('servicos', __name__)


@servicos_bp.route('/')
@login_required
def listar():
    """Lista todos os serviços."""
    servicos = Servico.query.order_by(Servico.ativo.desc(), Servico.nome).all()
    return render_template('servicos.html', servicos=servicos)


@servicos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Cria um novo serviço."""
    if request.method == 'POST':
        nome = sanitize_input(request.form.get('nome', '').strip())
        descricao = sanitize_input(request.form.get('descricao', ''), 1000)
        preco_str = request.form.get('preco', '').strip().replace(',', '.')
        duracao = request.form.get('duracao_min', '').strip()

        # Validações
        erros = []
        if not nome or len(nome) < 2:
            erros.append('Nome do serviço é obrigatório (mín. 2 caracteres).')

        try:
            preco = Decimal(preco_str)
            if preco < 0:
                erros.append('Preço não pode ser negativo.')
        except (InvalidOperation, ValueError):
            erros.append('Preço inválido.')
            preco = Decimal('0')

        try:
            duracao_min = int(duracao)
            if duracao_min <= 0:
                erros.append('Duração deve ser maior que zero.')
        except (ValueError, TypeError):
            erros.append('Duração inválida.')
            duracao_min = 60

        if Servico.query.filter_by(nome=nome).first():
            erros.append(f'Já existe um serviço chamado "{nome}".')

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template('servico_form.html', servico=None)

        servico = Servico(
            nome=nome,
            descricao=descricao or None,
            preco=preco,
            duracao_min=duracao_min,
            ativo=True
        )
        db.session.add(servico)
        db.session.commit()

        logger.info(f'Serviço criado: id={servico.id}, nome={nome}')
        flash(f'Serviço "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('servicos.listar'))

    return render_template('servico_form.html', servico=None)


@servicos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edita um serviço existente."""
    servico = db.get_or_404(Servico, id)

    if request.method == 'POST':
        nome = sanitize_input(request.form.get('nome', '').strip())
        descricao = sanitize_input(request.form.get('descricao', ''), 1000)
        preco_str = request.form.get('preco', '').strip().replace(',', '.')
        duracao = request.form.get('duracao_min', '').strip()

        # Validações
        erros = []
        if not nome or len(nome) < 2:
            erros.append('Nome do serviço é obrigatório (mín. 2 caracteres).')

        try:
            preco = Decimal(preco_str)
            if preco < 0:
                erros.append('Preço não pode ser negativo.')
        except (InvalidOperation, ValueError):
            erros.append('Preço inválido.')
            preco = servico.preco

        try:
            duracao_min = int(duracao)
            if duracao_min <= 0:
                erros.append('Duração deve ser maior que zero.')
        except (ValueError, TypeError):
            erros.append('Duração inválida.')
            duracao_min = servico.duracao_min

        # Verificar nome duplicado
        outro = Servico.query.filter(Servico.nome == nome, Servico.id != id).first()
        if outro:
            erros.append(f'Já existe um serviço chamado "{nome}".')

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template('servico_form.html', servico=servico)

        servico.nome = nome
        servico.descricao = descricao or None
        servico.preco = preco
        servico.duracao_min = duracao_min
        db.session.commit()

        logger.info(f'Serviço atualizado: id={servico.id}')
        flash(f'Serviço "{nome}" atualizado com sucesso!', 'success')
        return redirect(url_for('servicos.listar'))

    return render_template('servico_form.html', servico=servico)


@servicos_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle(id):
    """Ativa/desativa um serviço."""
    servico = db.get_or_404(Servico, id)
    servico.ativo = not servico.ativo
    db.session.commit()

    estado = 'ativado' if servico.ativo else 'desativado'
    logger.info(f'Serviço {estado}: id={servico.id}')
    flash(f'Serviço "{servico.nome}" {estado}.', 'success')
    return redirect(url_for('servicos.listar'))
