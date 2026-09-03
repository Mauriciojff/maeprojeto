# 🚀 GUIA RÁPIDO - AGENDA DA MÃE

## 📋 Checklist de Instalação

### 1️⃣ Instalar Dependências
```bash
npm install
```
⏱️ Demora: ~2 minutos

### 2️⃣ Iniciar o Servidor
```bash
npm start
```

Você verá:
```
🚀 Servidor rodando em http://localhost:3000
📱 Abra no navegador: http://localhost:3000
📱 Iniciando WhatsApp Web...
```

### 3️⃣ Abrir no Navegador
Clique no link ou abra:
```
http://localhost:3000
```

### 4️⃣ Conectar WhatsApp (Primeira Vez)
1. Um **QR Code** aparecerá no terminal
2. Abra **WhatsApp** no seu celular
3. Vá para: **Configurações** → **Dispositivos Vinculados** → **Vincular um dispositivo**
4. Aponte a câmera para o **QR Code**
5. Pronto! ✅ WhatsApp conectado

---

## 📁 Estrutura de Arquivos Criados

```
maeprojeto/
├── Frontend
│   ├── index.html              ← Interface do usuário
│   ├── app.js                  ← Lógica da UI (250+ linhas)
│   ├── style.css               ← Estilos responsivos (500+ linhas)
│   └── api-client.js           ← Cliente HTTP para API
│
├── Backend
│   ├── start-server.js         ← Inicializador principal ✨ NOVO
│   ├── server.js               ← Configuração Express
│   ├── database.js             ← Gerenciamento SQLite
│   ├── whatsapp-service.js     ← Integração WhatsApp
│   └── routes/
│       └── api.js              ← Todas as rotas da API ✨ NOVO
│
├── Config
│   ├── package.json            ← Dependências
│   ├── .env.example            ← Exemplo de variáveis
│   ├── .gitignore              ← Arquivos ignorados no Git
│   └── README.md               ← Documentação completa
│
└── Data (criado automaticamente)
    └── data/
        └── agenda.db           ← Banco de dados SQLite
```

---

## ✨ Funcionalidades Implementadas

### ✅ Frontend Completo
- 📅 Agenda visual com horários
- 👩 Gerenciamento de clientes
- 💰 Dashboard de faturamento
- ⚙️ Configurações de preços e horários
- 📊 Relatórios detalhados
- 📱 Interface responsiva (mobile & desktop)

### ✅ Backend Profissional
- 🚀 Servidor Express.js
- 💾 Banco de dados SQLite com 6 tabelas
- 🔌 API RESTful com 20+ endpoints
- 🔐 Validação de dados
- 📤 Exportar/Importar dados

### ✅ Integração WhatsApp
- 💬 Envio automático de lembretes
- ✅ Confirmação de agendamentos
- ❌ Cancelamento de agendamentos
- 📅 Consulta de horários disponíveis
- 📊 Log de mensagens

### ✅ Recursos Avançados
- 📌 Modo offline (LocalStorage fallback)
- 🌐 CORS habilitado
- 📊 Resumo financeiro automático
- 🎯 Detecção de conflitos de horários
- 📁 Soft delete de clientes
- 🔄 Sistema de importação de dados

---

## 🎯 Próximos Passos (Opcionais)

### Para Colocar Online
- [ ] Deploy na Heroku/Railway/Render
- [ ] Usar banco de dados na nuvem (MongoDB/PostgreSQL)
- [ ] Configurar domínio próprio
- [ ] SSL/HTTPS

### Para Melhorar
- [ ] App mobile nativa (React Native)
- [ ] Sistema de login e permissões
- [ ] Integração com pagamentos
- [ ] Dark mode
- [ ] Notificações Push

---

## 🆘 Problemas Comuns

### ❌ "npm ERR! Cannot find module"
```bash
npm install
```

### ❌ "Porta 3000 já em uso"
```bash
PORT=3001 npm start
```

### ❌ WhatsApp não conecta
- Reinicie o servidor
- Verifique conexão de internet
- Se QR Code expirou, feche o navegador e tente novamente

### ❌ Dados não aparecem
- Verifique se `data/agenda.db` existe
- Se não, crie uma primeira cliente para inicializar o banco

---

## 📞 Comandos Úteis

```bash
# Instalar dependências
npm install

# Iniciar servidor (produção)
npm start

# Iniciar servidor (desenvolvimento com auto-reload)
npm run dev

# Exportar dados
# Abra em http://localhost:3000 → Config → Exportar Dados (JSON)

# Limpar tudo e recomeçar
rm -rf data/
npm start
```

---

## 📊 API Rápida

```bash
# Listar clientes
curl http://localhost:3000/api/clientes

# Criar cliente
curl -X POST http://localhost:3000/api/clientes \
  -H "Content-Type: application/json" \
  -d '{"nome":"Maria","telefone":"11999999999"}'

# Faturamento
curl http://localhost:3000/api/faturamento/resumo

# Health check
curl http://localhost:3000/health
```

---

## ✅ Você Está Pronto!

Agora você tem um **sistema profissional de agendamento** completo com:
- ✅ Interface bonita e responsiva
- ✅ Backend robusto
- ✅ WhatsApp integrado
- ✅ Faturamento automático
- ✅ Backup de dados

**Boa sorte com o negócio da sua mãe!** 💅✨

---

**Precisa de ajuda?** Abra uma issue ou consulte o README.md para mais detalhes.
