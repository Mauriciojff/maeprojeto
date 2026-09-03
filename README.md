# 💅 Agenda da Mãe — Manicure & Cílios

Um aplicativo completo de agendamento de manicure e cílios com integração WhatsApp, faturamento automático e gerenciamento de clientes.

## ✨ Funcionalidades

- 📅 **Agenda Visual** — Visualizar agendamentos por semana com horários disponíveis
- 💬 **Integração WhatsApp** — Lembretes e confirmações automáticas
- 💰 **Faturamento** — Controle de receitas por serviço, dia, semana e mês
- 👩 **Gerenciamento de Clientes** — Cadastro, edição e busca de clientes
- ⚙️ **Configurações** — Ajustar preços, horários e intervalo de agendamentos
- 📊 **Relatórios** — Análise de faturamento por período
- 💾 **Backup** — Exportar e importar dados em JSON
- 📱 **Responsivo** — Funciona perfeitamente em desktop e mobile

## 🚀 Instalação Rápida

### Pré-requisitos
- Node.js 14+ instalado
- npm ou yarn
- Conta WhatsApp ativa (para integração)

### Passos

1. **Abra o terminal na pasta do projeto:**
   ```bash
   cd maeprojeto
   ```

2. **Instale as dependências:**
   ```bash
   npm install
   ```

3. **Copie o arquivo de configuração:**
   ```bash
   cp .env.example .env
   ```

4. **Inicie o servidor:**
   ```bash
   npm start
   ```
   Ou para desenvolvimento com auto-reload:
   ```bash
   npm run dev
   ```

5. **Abra no navegador:**
   ```
   http://localhost:3000
   ```

## 📱 Configurar WhatsApp

### Primeira Conexão (QR Code)

1. Ao iniciar o servidor, um **QR Code** aparecerá no terminal
2. Abra **WhatsApp** no seu celular
3. Vá para: **Configurações** → **Dispositivos Vinculados** → **Vincular um dispositivo**
4. Aponte a câmera para o QR Code exibido no terminal
5. Pronto! ✅ WhatsApp está conectado

### O que funciona com WhatsApp

✅ **Lembretes automáticos** — Mensagem 24h antes do agendamento
✅ **Confirmação rápida** — Cliente responde "✅ Confirmar" ou "❌ Cancelar"
✅ **Horários disponíveis** — Cliente solicita com "📅 Horários"
✅ **Notificações** — Alerts quando cliente confirma/cancela

## 🏗️ Estrutura do Projeto

```
maeprojeto/
├── index.html              # 🎨 Interface web principal
├── app.js                  # ⚙️ Lógica do frontend (JavaScript)
├── style.css               # 🎨 Estilos CSS responsivos
├── server.js               # 🚀 Servidor Express (backend)
├── database.js             # 💾 Gerenciamento do SQLite
├── whatsapp-service.js     # 💬 Integração com WhatsApp Web
├── package.json            # 📦 Dependências do projeto
├── .env.example            # ⚙️ Exemplo de configurações
├── README.md               # 📖 Este arquivo
└── data/                   # 📁 Banco de dados (criado automaticamente)
    └── agenda.db           # 🗄️ Arquivo SQLite
```

## 🔌 API Endpoints

### Clientes
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/clientes` | Listar todas as clientes |
| GET | `/api/clientes/:id` | Obter cliente específico |
| POST | `/api/clientes` | Criar nova cliente |
| PUT | `/api/clientes/:id` | Atualizar cliente |
| DELETE | `/api/clientes/:id` | Excluir cliente |

### Agendamentos
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/agendamentos` | Listar agendamentos |
| GET | `/api/agendamentos/:id` | Obter agendamento |
| GET | `/api/agendamentos/data/:data` | Agendamentos de um dia |
| POST | `/api/agendamentos` | Criar agendamento |
| PUT | `/api/agendamentos/:id` | Atualizar agendamento |
| DELETE | `/api/agendamentos/:id` | Excluir agendamento |

### Faturamento
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/faturamento` | Listar faturamentos |
| GET | `/api/faturamento/resumo` | Resumo financeiro |

### Dados
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/export` | Exportar todos os dados |
| POST | `/api/import` | Importar dados do JSON |

## 📋 Exemplos de Uso

### Criar uma Cliente
```bash
curl -X POST http://localhost:3000/api/clientes \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Maria Silva",
    "telefone": "11 9 9999-9999",
    "email": "maria@email.com"
  }'
```

### Criar um Agendamento
```bash
curl -X POST http://localhost:3000/api/agendamentos \
  -H "Content-Type: application/json" \
  -d '{
    "clienteId": "abc123def456",
    "servico": "combo",
    "data": "2024-09-15",
    "horario": "14:00",
    "status": "confirmada",
    "preco": 110
  }'
```

### Obter Resumo Financeiro
```bash
curl http://localhost:3000/api/faturamento/resumo
```

## 🎨 Personalizações

### Alterar Cores Principais
Edite o arquivo `style.css` e mude as variáveis CSS:

```css
:root {
  --primary: #e91e63;        /* Rosa (padrão) */
  --secondary: #9c27b0;      /* Roxo */
  --success: #4caf50;        /* Verde */
  --danger: #f44336;         /* Vermelho */
}
```

### Alterar Preços dos Serviços
1. Acesse a aba **⚙️ Configurações**
2. Ajuste os valores em "Preços dos Serviços"
3. Clique em **Salvar Preços**

### Alterar Horário de Funcionamento
1. Aba **⚙️ Configurações**
2. Configure "Horário de Funcionamento"
3. Selecione o intervalo entre horários (30 ou 60 min)
4. Clique em **Salvar Horário**

## 🐛 Solução de Problemas

### ❌ "npm ERR! Cannot find module"
```bash
# Limpe a cache e reinstale
npm cache clean --force
npm install
```

### ❌ "Erro: Porta 3000 já está em uso"
```bash
# Use uma porta diferente
PORT=3001 npm start
```

### ❌ WhatsApp não conecta
- ✅ Certifique-se que tem **conexão de internet** estável
- ✅ O **QR Code expirou**? Reinicie o servidor: `npm start`
- ✅ Tente **atualizar** a página do navegador
- ✅ Se persistir, limpe a pasta `data/` e tente novamente

### ❌ Dados desapareceram
- ✅ Verifique se o arquivo `data/agenda.db` existe
- ✅ Use **Exportar Dados** antes de atualizações
- ✅ Guarde o backup em um local seguro

## 💡 Dicas de Uso

1. **Fazer Backup Regularmente** — Menu Config → Exportar Dados (JSON)
2. **Confirmar Agendamentos** — Use o botão WhatsApp para enviar lembretes
3. **Horários Ocupados** — O sistema impede conflitos automaticamente
4. **Status do Agendamento** — Mude para "Realizada" para contar no faturamento

## 📈 Próximas Funcionalidades

- [ ] 🌐 Deploy na nuvem (Heroku, Railway, Vercel)
- [ ] 📱 App mobile nativa (React Native)
- [ ] 💳 Integração com pagamentos (Stripe, PIX)
- [ ] 📞 Lembretes por SMS
- [ ] 📊 Dashboard com gráficos avançados
- [ ] 🔗 Link de agendamento público (calendário)
- [ ] 🗂️ Múltiplos profissionais/agendadores
- [ ] 🎓 Avaliações e comentários de clientes

## 📧 Contato e Suporte

- 📧 Dúvidas? Abra uma **issue** no repositório
- 💬 Sugestões? Envie um **pull request**
- 📋 Relatório de bugs? Descreva com detalhes

## 📄 Licença

MIT License — Você é livre para usar, modificar e distribuir este projeto

---

**Desenvolvido com ❤️ para facilitar a gestão do negócio de manicure e cílios** 💅✨
- ✅ **Status dos agendamentos** — Pendente, Confirmada, Não vai, Realizada
- ⚙️ **Configurações** — Preços dos serviços, horário de funcionamento e intervalo entre horários
- 💾 **Dados salvos localmente** — Os dados ficam salvos no navegador (localStorage)
- 📥 **Exportar backup** — Exporte todos os dados em JSON

## 🚀 Como usar

1. Abra o arquivo `index.html` no navegador (duplo clique ou arraste para o navegador)
2. Na aba **Clientes**, cadastre as clientes com nome e telefone
3. Na aba **Configurações**, ajuste os preços e horário de funcionamento
4. Na aba **Agenda**, clique no horário vazio (+) para criar um agendamento
5. Clique em um agendamento para editar, excluir ou enviar WhatsApp de confirmação

## 📱 Envio de WhatsApp

- Ao clicar em **📱 WhatsApp** em um agendamento, o app monta automaticamente uma mensagem de confirmação com data, horário e serviço
- O WhatsApp Web/App abre com a mensagem pronta para envio
- A cliente pode confirmar se vai ou não comparecer

## 💾 Backup dos dados

- Os dados ficam salvos automaticamente no navegador
- Use **Exportar Dados** na aba Configurações para baixar um backup em JSON
- Para restaurar, basta abrir o app no mesmo navegador (os dados são mantidos)

## 🛠️ Tecnologias

- HTML5
- CSS3
- JavaScript (Vanilla)
- localStorage para persistência
- WhatsApp API (wa.me links)

## 📁 Arquivos

- `index.html` — Estrutura da aplicação
- `style.css` — Estilos e design responsivo
- `app.js` — Lógica da aplicação