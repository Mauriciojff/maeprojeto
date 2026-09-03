# ============================================
# ROUTES/AUTH.PY — Autenticação
# ============================================

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from ..database.models import Usuario
from ..database import db
from ..utils.security import sanitize_input, is_safe_password
import logging

logger = logging.getLogger('agenda_mae')

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login."""
    # Se já está logado, redirecionar
    if session.get('usuario_id'):
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', '').strip().lower())
        senha = request.form.get('senha', '')

        if not email or not senha:
            flash('Informe email e senha.', 'error')
            return render_template('login.html')

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not check_password_hash(usuario.senha_hash, senha):
            logger.warning(f'Tentativa de login falhou para: {email}')
            flash('Email ou senha incorretos.', 'error')
            return render_template('login.html')

        if not usuario.ativo:
            flash('Usuário desativado. Contate o administrador.', 'error')
            return render_template('login.html')

        # Login bem-sucedido
        session.clear()
        session['usuario_id'] = usuario.id
        session['usuario_email'] = usuario.email
        session['usuario_nome'] = usuario.nome
        session['usuario_role'] = usuario.role
        session.permanent = True

        usuario.ultimo_login = datetime.utcnow()
        db.session.commit()

        logger.info(f'Login bem-sucedido: {email}')
        flash(f'Bem-vindo(a), {usuario.nome}!', 'success')

        # Redirecionar para página solicitada ou dashboard
        proxima = request.args.get('next')
        if proxima and proxima.startswith('/'):
            return redirect(proxima)
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Encerra a sessão."""
    email = session.get('usuario_email')
    session.clear()
    if email:
        logger.info(f'Logout: {email}')
    flash('Sessão encerrada com sucesso.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/trocar-senha', methods=['GET', 'POST'])
def trocar_senha():
    """Permite ao usuário trocar a senha."""
    if not session.get('usuario_id'):
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if not senha_atual or not nova_senha or not confirmar_senha:
            flash('Preencha todos os campos.', 'error')
            return render_template('trocar_senha.html')

        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem.', 'error')
            return render_template('trocar_senha.html')

        if not is_safe_password(nova_senha):
            flash('A senha deve ter no mínimo 8 caracteres, com maiúscula, minúscula e número.', 'error')
            return render_template('trocar_senha.html')

        usuario = Usuario.query.get(session['usuario_id'])
        if not usuario or not check_password_hash(usuario.senha_hash, senha_atual):
            flash('Senha atual incorreta.', 'error')
            return render_template('trocar_senha.html')

        usuario.senha_hash = generate_password_hash(nova_senha)
        db.session.commit()

        logger.info(f'Senha alterada para usuário: {usuario.email}')
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('trocar_senha.html')
