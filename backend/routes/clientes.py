# ============================================
# ROUTES/CLIENTES.PY — CRUD de clientes
# ============================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

from ..database.models import Cliente, Agendamento
from ..database import db
from ..utils.decorators import login_required
from ..utils.security import sanitize_input, is_valid_telefone, is_valid_email
from ..utils.helpers import telefone_limpo, formatar_data_br
import logging

logger = logging.getLogger('agenda_mae')

clientes_bp = Blueprint('clientes', __name__)


@clientes_bp.route('/')
@login_required
def listar():
    """Lista todos os clientes ativos."""
    busca = request.args.get('q', '').strip()

    query = Cliente.query.filter_by(ativo=True)
    if busca:
        query = query.filter(Cliente.nome.ilike(f'%{busca}%'))
    query = query.order_by(Cliente.nome)

    clientes = query.all()
    return render_template('clientes.html', clientes=clientes, busca=busca)


@clientes_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Cadastra um novo cliente."""
    if request.method == 'POST':
        nome = sanitize_input(request.form.get('nome', '').strip())
        telefone = sanitize_input(request.form.get('telefone', '').strip())
        email = sanitize_input(request.form.get('email', '').strip())
        observacoes = sanitize_input(request.form.get('observacoes', ''), 1000)

        # Validações
        erros = []
        if not nome or len(nome) < 2:
            erros.append('Nome é obrigatório (mínimo 2 caracteres).')
        if not is_valid_telefone(telefone):
            erros.append('Telefone inválido.')
        if not is_valid_email(email):
            erros.append('Email inválido.')

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template('cliente_form.html', cliente=None)

        cliente = Cliente(
            nome=nome,
            telefone=telefone_limpo(telefone) if telefone else None,
            email=email or None,
            observacoes=observacoes or None
        )
        db.session.add(cliente)
        db.session.commit()

        logger.info(f'Cliente criado: id={cliente.id}, nome={nome}')
        flash(f'Cliente "{nome}" cadastrada com sucesso!', 'success')
        return redirect(url_for('clientes.listar'))

    return render_template('cliente_form.html', cliente=None)


@clientes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edita um cliente existente."""
    cliente = db.get_or_404(Cliente, id)

    if request.method == 'POST':
        nome = sanitize_input(request.form.get('nome', '').strip())
        telefone = sanitize_input(request.form.get('telefone', '').strip())
        email = sanitize_input(request.form.get('email', '').strip())
        observacoes = sanitize_input(request.form.get('observacoes', ''), 1000)

        # Validações
        erros = []
        if not nome or len(nome) < 2:
            erros.append('Nome é obrigatório (mínimo 2 caracteres).')
        if not is_valid_telefone(telefone):
            erros.append('Telefone inválido.')
        if not is_valid_email(email):
            erros.append('Email inválido.')

        if erros:
            for e in erros:
                flash(e, 'error')
            return render_template('cliente_form.html', cliente=cliente)

        cliente.nome = nome
        cliente.telefone = telefone_limpo(telefone) if telefone else None
        cliente.email = email or None
        cliente.observacoes = observacoes or None
        db.session.commit()

        logger.info(f'Cliente atualizado: id={cliente.id}')
        flash(f'Cliente "{nome}" atualizada com sucesso!', 'success')
        return redirect(url_for('clientes.listar'))

    return render_template('cliente_form.html', cliente=cliente)


@clientes_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    """Exclui (soft delete) um cliente."""
    cliente = db.get_or_404(Cliente, id)
    cliente.ativo = False
    db.session.commit()

    logger.info(f'Cliente excluído (soft): id={cliente.id}, nome={cliente.nome}')
    flash(f'Cliente "{cliente.nome}" excluída.', 'success')
    return redirect(url_for('clientes.listar'))


# ============================================
# API JSON (para integração frontend)
# ============================================

@clientes_bp.route('/api')
@login_required
def api_listar():
    """Retorna clientes em JSON (para selects dinâmicos)."""
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    return jsonify([c.to_dict() for c in clientes])
