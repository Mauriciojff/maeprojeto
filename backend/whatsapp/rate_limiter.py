# ============================================
# WHATSAPP/RATE_LIMITER.PY — Controle de taxa (rate limiting)
# ============================================

import time
import threading
import logging
from collections import defaultdict, deque
from flask import current_app

logger = logging.getLogger('agenda_mae')


class RateLimiter:
    """
    Limitador de taxa baseado em memória (janela deslizante).

    Restringe o número de mensagens processadas por telefone dentro
    de uma janela de tempo. Protege contra fluxos excessivos e
    tentativas de sobrecarga. Em produção, recomenda-se usar Redis,
    mas esta implementação em memória atende à proteção básica.
    """

    def __init__(self, janela=60, max_tentativas=60):
        self.janela = janela
        self.max_tentativas = max_tentativas
        self._historico = defaultdict(deque)
        self._lock = threading.Lock()

    def permitido(self, chave):
        """
        Verifica se uma nova requisição é permitida para a chave
        (tipicamente o telefone do remetente). Limpa eventos antigos
        e conta os recentes.
        """
        agora = time.time()
        with self._lock:
            fila = self._historico[chave]
            while fila and fila[0] <= agora - self.janela:
                fila.popleft()
            if len(fila) >= self.max_tentativas:
                return False
            fila.append(agora)
            return True

    def reset(self, chave=None):
        """Reseta o limite para uma chave ou para todas."""
        with self._lock:
            if chave:
                self._historico.pop(chave, None)
            else:
                self._historico.clear()


# Instância global compartilhada
_instancia = None


def get_rate_limiter():
    """Obtém/instancia o rate limiter global, lendo a configuração."""
    global _instancia
    if _instancia is None:
        janela = int(current_app.config.get('WHATSAPP_RATE_LIMIT_WINDOW', '60'))
        max_t = int(current_app.config.get('WHATSAPP_RATE_LIMIT_MAX', '60'))
        _instancia = RateLimiter(janela=janela, max_tentativas=max_t)
    return _instancia


def resetar_rate_limiter():
    """Reseta o rate limiter (usado em testes)."""
    global _instancia
    _instancia = None
