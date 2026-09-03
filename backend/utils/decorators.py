# ============================================
# UTILS/DECORATORS.PY — Decoradores de autorização
# ============================================

from functools import wraps
from flask import session, redirect, url_for, flash, request, abort, jsonify
import logging

logger = logging.getLogger('agenda_mae')


def login_required(f):
    """Exige que o usuário esteja autenticado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('usuario_id'):
            if request.path.startswith('/api/'):
                return jsonify({'erro': 'Não autenticado'}), 401
            flash('Faça login para continuar.', 'error')
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Exige que o usuário seja administrador."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('usuario_id'):
            if request.path.startswith('/api/'):
                return jsonify({'erro': 'Não autenticado'}), 401
            flash('Faça login para continuar.', 'error')
            return redirect(url_for('auth.login', next=request.path))

        if session.get('usuario_role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({'erro': 'Privilégios de administrador necessários'}), 403
            abort(403)
        return f(*args, **kwargs)
    return decorated
