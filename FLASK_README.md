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
│   │   ├── models.py             # Modelos ORM
│   │   └── wpp_models.py         # Modelos WhatsApp (mensagens, sessões)
│   ├── routes/
│   │   ├── main.py               # Dashboard
│   │   ├── auth.py               # Autenticação
│   │   ├── clientes.py           # CRUD clientes
│   │   ├── servicos.py           # CRUD serviços
│   │   ├── agendamentos.py       # CRUD agendamentos + conflitos
│   │   ├── agenda.py             # Calendário (dia/semana/mês)
│   │   └── faturamento.py        # Relatórios de faturamento
│   ├── whatsapp/                  # Integração WhatsApp Business
│   │   ├── __init__.py           # Rotas administrativas WhatsApp
│   │   ├── webhook.py            # Webhook (GET verificação + POST msgs)
│   │   ├── conversation.py       # Motor de conversa (20+ estados)
│   │   ├── api_client.py         # Cliente HTTP para Graph API
│   │   ├── security.py           # Validação HMAC, sanitização, etc.
│   │   ├── rate_limiter.py       # Rate limiting por telefone
│   │   ├── session_state.py      # Gestão de sessões de conversa
│   │   ├── notifier.py           # Notificações e comandos admin
│   │   ├── agenda_helpers.py     # Helpers para agendamento
│   │   └── wpp_models.py         # Alias para database/wpp_models.py
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
| `WHATSAPP_TOKEN`    | (vazio)               | Token de acesso Meta (Cloud API)   |
| `WHATSAPP_PHONE_NUMBER_ID` | (vazio)       | ID do número de telefone da empresa |
| `WHATSAPP_VERIFY_TOKEN` | (vazio)           | Token de verificação do webhook    |
| `WHATSAPP_WEBHOOK_SECRET` | (vazio)        | Segredo HMAC-SHA256 do webhook     |
| `ADMIN_WHATSAPP_NUMBERS` | (vazio)         | Números admin (separados por vírgula) |
| `WHATSAPP_DRY_RUN` | `false`               | Simular envios (true para dev/test) |
| `WHATSAPP_RATE_LIMIT_WINDOW` | `60`        | Janela de rate limit (segundos)     |
| `WHATSAPP_RATE_LIMIT_MAX` | `60`            | Máximo de msgs por janela          |
| `CSRF_ENABLED`      | `true`                | Proteção CSRF                      |
---

## Integração WhatsApp Business Cloud API

O sistema inclui integração completa com o WhatsApp Business Cloud API,
permitindo que clientes agendem, cancelem e remarquem compromissos
diretamente pelo WhatsApp.

### Fluxo do Webhook

1. **Meta envia GET** `/api/whatsapp/webhook` → verificação do `hub.verify_token`
2. **Meta envia POST** `/api/whatsapp/webhook` → mensagens recebidas
3. Validação de assinatura HMAC-SHA256 (`X-Hub-Signature-256`)
4. Rate limiting por telefone remetente
5. Roteamento via `conversation.py` (20+ estados)

### Configuração na Meta (Meta for Developers)

1. Criar um app em [developers.facebook.com](https://developers.facebook.com/)
2. Adicionar o produto **WhatsApp**
3. Configurar o webhook com a URL do seu servidor:
   - **URL:** `https://seudominio.com/api/whatsapp/webhook`
   - **Verify Token:** o valor de `WHATSAPP_VERIFY_TOKEN`
4. Subscrever eventos: `messages`, `messaging_postbacks`
5. Configurar o **App Secret** como `WHATSAPP_WEBHOOK_SECRET`

### Rotas do Webhook

| Método | Rota                          | Descrição                              |
|--------|-------------------------------|----------------------------------------|
| GET    | `/api/whatsapp/webhook`       | Handshake de verificação da Meta       |
| POST   | `/api/whatsapp/webhook`       | Recebimento de mensagens               |

### Comandos de Conversa (para clientes)

| Comando          | Ação                                    |
|------------------|-----------------------------------------|
| `menu`           | Exibe o menu principal                  |
| `1` ou `agendar` | Inicia o fluxo de agendamento          |
| `2` ou `cancelar`| Inicia o fluxo de cancelamento         |
| `3` ou `remarcar`| Inicia o fluxo de remarcar             |
| `4` ou `consultar`| Mostra próximos agendamentos          |

### Comandos Administrativos

| Comando              | Ação                                |
|----------------------|-------------------------------------|
| `admin agenda`       | Mostra agenda do dia (admin)        |
| `admin pendentes`    | Lista agendamentos pendentes        |
| `admin clientes`     | Lista todos os clientes             |
| `admin concluir <N>` | Marca agendamento como realizado    |
| `admin desativar <N>`| Desativa um serviço                 |

> **Nota:** Comandos administrativos requerem que o número esteja
> listado em `ADMIN_WHATSAPP_NUMBERS`.

### Modo Dry-Run

Para desenvolvimento e testes, defina `WHATSAPP_DRY_RUN=true` no `.env`.
Nesse modo, mensagens são apenas registradas sem envio real à API da Meta.

### Segurança do Webhook

- **Assinatura HMAC-SHA256:** cada POST é validado contra a assinatura
  enviada pela Meta (`X-Hub-Signature-256`)
- **Rate Limiting:** proteção contra flood (configurável via env)
- **CSRF Exempt:** as rotas do webhook são eximidas da proteção CSRF
  (a segurança é feita pela validação da assinatura)

