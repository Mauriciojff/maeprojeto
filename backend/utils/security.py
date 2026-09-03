# ============================================
# UTILS/SECURITY.PY — Funções de segurança
# ============================================

import re
import html
from functools import wraps
from flask import session, redirect, url_for, flash, request, abort

# ============================================
# SANITIZAÇÃO DE INPUTS (Prevenção XSS)
# ============================================

def sanitize_input(valor, max_len=500):
    """
    Sanitiza uma string, removendo tags HTML perigosas
    e limitando o tamanho. Previne XSS.
    """
    if not valor:
        return valor
    if not isinstance(valor, str):
        return valor

    # Remover tags HTML potencialmente perigosas
    valor = html.escape(valor)

    # Remover scripts/js
    valor = re.sub(r'(?i)<script.*?</script>', '', valor)
    valor = re.sub(r'(?i)javascript:', '', valor)

    # Limitar tamanho
    return valor[:max_len]


def sanitize_all_inputs(form_data, max_len=500):
    """Sanitiza todos os campos string de um formulário."""
    result = {}
    for chave, valor in form_data.items():
        if isinstance(valor, str):
            result[chave] = sanitize_input(valor, max_len)
        else:
            result[chave] = valor
    return result


# ============================================
# VALIDAÇÃO DE SENHA FORTE
# ============================================

def is_safe_password(senha):
    """
    Verifica se a senha é forte:
    - mínimo 8 caracteres
    - pelo menos 1 letra maiúscula
    - pelo menos 1 letra minúscula
    - pelo menos 1 número
    """
    if len(senha) < 8:
        return False
    if not re.search(r'[A-Z]', senha):
        return False
    if not re.search(r'[a-z]', senha):
        return False
    if not re.search(r'\d', senha):
        return False
    # Não permitir senhas muito comuns
    comuns = {'12345678', 'senha123456', 'password', 'abc12345'}
    if senha.lower() in comuns:
        return False
    return True


# ============================================
# VALIDAÇÃO DE TELEFONE
# ============================================

def is_valid_telefone(telefone):
    """Valida telefone brasileiro (10-13 dígitos após remoção de pontuação)."""
    if not telefone:
        return True  # Opcional
    digitos = re.sub(r'\D', '', telefone)
    return 10 <= len(digitos) <= 13


# ============================================
# VALIDAÇÃO DE EMAIL
# ============================================

def is_valid_email(email):
    """Valida formato de email básico."""
    if not email:
        return True  # Opcional
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))
