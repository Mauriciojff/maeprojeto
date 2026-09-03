# ============================================
# RUN.PY — Ponto de entrada da aplicação
# ============================================

from backend import create_app
from backend.config import DevelopmentConfig, ProductionConfig
import os

app = create_app(
    ProductionConfig if os.getenv('FLASK_ENV', 'development').lower() == 'production'
    else DevelopmentConfig
)


if __name__ == '__main__':
    env = os.getenv('FLASK_ENV', 'development').lower()
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5000'))
    debug = env != 'production'

    print('=' * 50)
    print('  Agenda da Mãe — Sistema de Agendamento')
    print(f'  Ambiente: {env}')
    print(f'  URL: http://{host}:{port}')
    print('  Login padrão: admin@agenda.com / Senha123456')
    print('=' * 50)

    app.run(host=host, port=port, debug=debug)
