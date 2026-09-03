# Agenda da Mãe — Backend Flask

Sistema completo de agendamento para manicure e extensão de cílios,
desenvolvido em **Python/Flask** com templates **Jinja2** e banco **SQLite**.

## Funcionalidades

- 🔐 **Autenticação** — login, logout, troca de senha, proteção CSRF
- 📅 **Agenda** — visualização por dia, semana e mês (calendário)
- 📝 **Agendamentos** — CRUD completo com validação de conflito de horário
- 👤 **Clientes** — CRUD de clientes (nome, telefone, email, observações)
- 💇♀️ **Serviços** — CRUD de serviços (preço, duração, ativo/inativo)
- 💰 **Faturamento** — relatórios por dia/semana/mês/ano, comparação com período anterior
- ⚡ **API JSON** — horários disponíveis e dados da agenda para o frontend
- 📱 **Responsivo** — CSS adaptável para desktop e mobile

## Como executar

> ⚠️ **Requer Python 3.9+ instalado.**

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. (Opcional) Configurar variáveis de ambiente
# copie .env.example para .env e ajuste conforme necessário

# 3. Executar o servidor
python run.py
```

Acesse **http://127.0.0.1:5000**

**Login padrão:** `admin@agenda.com` / `Senha123456`

## Estrutura do projeto

```
maeprojeto/
├── run.py                        # Ponto de entrada
├── requirements.txt              # Dependências
├── .env.example                  # Exemplo de configuração
├── backend/
│   ├── __init__.py               # Fábrica da aplicação (create_app)
│   ├── config.py                 # Configurações
│   ├── database/
│   │   ├── __init__.py           # Instância db + init_db
│   │   ├── db.py                 # Re-export de compatibilidade
│   │   └── models.py             # Modelos ORM
│   ├── routes/
│   │   ├── main.py               # Dashboard
│   │   ├── auth.py               # Autenticação
│   │   ├── clientes.py           # CRUD clientes
│   │   ├── servicos.py           # CRUD serviços
│   │   ├── agendamentos.py       # CRUD agendamentos + conflitos
│   │   ├── agenda.py             # Calendário (dia/semana/mês)
│   │   └── faturamento.py        # Relatórios de faturamento
│   ├── static/
│   │   ├── css/style.css         # Estilos
│   │   └── js/main.js            # JavaScript
│   ├── templates/                # Templates Jinja2
│   └── tests/                    # Testes pytest
└── utils/                        # Segurança e helpers
```

## Rotas principais

| Método | Rota                       | Descrição                             |
|--------|----------------------------|---------------------------------------|
| GET    | `/`                        | Redireciona para dashboard ou login   |
| GET    | `/login`                   | Página de login                       |
| POST   | `/auth/login`              | Autenticação                          |
| POST   | `/auth/logout`             | Logout                                |
| GET    | `/dashboard`               | Painel administrativo                 |
| GET    | `/agenda`                  | Calendário (dia/semana/mês)           |
| GET    | `/agenda/dados`            | API JSON para renderização da agenda  |
| GET    | `/agendamentos`            | Lista agendamentos com filtros        |
| GET/POST | `/agendamentos/novo`     | Criar agendamento                     |
| GET/POST | `/agendamentos/<id>/editar` | Editar agendamento                |
| POST   | `/agendamentos/<id>/status` | Alterar status                      |
| POST   | `/agendamentos/<id>/cancelar` | Cancelar                          |
| GET    | `/agendamentos/api/disponiveis` | Horários disponíveis (JSON)      |
| GET    | `/clientes`                | Lista clientes                        |
| GET    | `/servicos`                | Lista serviços                        |
| GET    | `/faturamento`             | Relatórios de faturamento             |

## Funcionalidades-chave

### Validação de conflito de horário
Ao criar ou editar um agendamento, o sistema verifica automaticamente se o
horário escolhido se sobrepõe a outro agendamento ativo no mesmo dia,
considerando a duração dos serviços.

### Sincronização de faturamento
Quando um agendamento é marcado como **realizada**, um registro é criado
automaticamente na tabela de faturamento. Se o status for revertido, o
registro é removido.

### API de horários disponíveis
Endpoint `GET /agendamentos/api/disponiveis?data=YYYY-MM-DD&servico_id=N`
retorna horários livres considerando conflitos e (se hoje) horários passados.

## Testes

```bash
# Instalar pytest
pip install pytest

# Executar testes
python -m pytest backend/tests -v
```

## Configuração via .env

| Variável            | Padrão                | Descrição                          |
|---------------------|-----------------------|------------------------------------|
| `SECRET_KEY`        | (chave padrão)        | Chave secreta da aplicação         |
| `FLASK_ENV`         | `development`         | Ambiente (development/production)  |
| `FLASK_DEBUG`       | `false`               | Modo debug                         |
| `HOST`              | `127.0.0.1`           | Host do servidor                   |
| `PORT`              | `5000`                | Porta do servidor                  |
| `HORA_ABERTURA`     | `08:00`               | Abertura (geração de horários)     |
| `HORA_FECHAMENTO`   | `20:00`               | Fechamento                         |
| `INTERVALO_MIN`     | `60`                  | Intervalo entre horários (min)     |
| `WHATSAPP_DDI`      | `55`                  | DDI para links wa.me               |
| `CSRF_ENABLED`      | `true`                | Proteção CSRF                      |
