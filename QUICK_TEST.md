# 🧪 TESTE RÁPIDO DO SISTEMA

## ✅ Pré-requisitos
- Node.js 14+ instalado
- npm ou yarn
- Postman ou Insomnia (opcional para testes de API)

---

## 🚀 Iniciar o Sistema

### 1. Instalar Dependências
```bash
npm install
```

### 2. Criar .env (se não existir)
```bash
cp .env.example .env
```

**Verificar valores em .env:**
```
NODE_ENV=development
PORT=3000
JWT_SECRET=sua-chave-super-secreta-change-me
JWT_REFRESH_SECRET=sua-chave-refresh-change-me
WHATSAPP_ENABLED=false
```

### 3. Iniciar Servidor
```bash
npm start
```

Você verá:
```
╔════════════════════════════════════════╗
║     💅 AGENDA DA MÃE - v2.0.0         ║
║   Com Segurança, Logging e Testes     ║
╚════════════════════════════════════════╝

🚀 Servidor rodando em http://localhost:3000
📱 Abra no navegador: http://localhost:3000
💾 Banco de dados: ./data/agenda.db
📊 Logs: ./logs/ (error.log, combined.log, http.log)

✅ Sistema pronto para uso!

🔐 Teste o login:
   Email: admin@agenda.com
   Senha: Senha123456
```

---

## 🧪 Testes via Postman/Insomnia

### 1️⃣ LOGIN (Obter Token)

**Método:** POST  
**URL:** `http://localhost:3000/api/auth/login`  
**Body (JSON):**
```json
{
  "email": "admin@agenda.com",
  "senha": "Senha123456"
}
```

**Resposta Esperada (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "usuario": {
    "id": "...",
    "email": "admin@agenda.com",
    "nome": "Admin",
    "role": "admin"
  }
}
```

**Copie o valor de `token` para usar nos próximos testes!**

---

### 2️⃣ OBTER PERFIL (Com Autenticação)

**Método:** GET  
**URL:** `http://localhost:3000/api/auth/me`  
**Headers:**
```
Authorization: Bearer {COLA_O_TOKEN_AQUI}
```

**Resposta Esperada (200 OK):**
```json
{
  "id": "...",
  "email": "admin@agenda.com",
  "nome": "Admin",
  "role": "admin",
  "ativo": 1,
  "dataCriacao": "2024-..."
}
```

---

### 3️⃣ CRIAR CLIENTE

**Método:** POST  
**URL:** `http://localhost:3000/api/clientes`  
**Headers:**
```
Authorization: Bearer {TOKEN}
Content-Type: application/json
```

**Body:**
```json
{
  "nome": "Maria Silva",
  "telefone": "11999999999",
  "email": "maria@email.com"
}
```

**Resposta Esperada (200 OK):**
```json
{
  "id": "uuid-aqui",
  "nome": "Maria Silva",
  "telefone": "11999999999",
  "email": "maria@email.com",
  "dataCadastro": "2024-...",
  "ativo": 1
}
```

---

### 4️⃣ LISTAR CLIENTES

**Método:** GET  
**URL:** `http://localhost:3000/api/clientes`  
**Headers:**
```
Authorization: Bearer {TOKEN}
```

**Resposta Esperada (200 OK):**
```json
[
  {
    "id": "...",
    "nome": "Maria Silva",
    "telefone": "11999999999",
    "email": "maria@email.com",
    "dataCadastro": "2024-...",
    "ativo": 1
  }
]
```

---

### 5️⃣ CRIAR AGENDAMENTO

**Método:** POST  
**URL:** `http://localhost:3000/api/agendamentos`  
**Headers:**
```
Authorization: Bearer {TOKEN}
```

**Body:**
```json
{
  "clienteId": "{id_do_cliente_criado_acima}",
  "servico": "manicure",
  "data": "2024-01-20",
  "horario": "14:00",
  "status": "confirmada",
  "preco": 40.00
}
```

**Resposta Esperada (200 OK):**
```json
{
  "id": "...",
  "clienteId": "...",
  "servico": "manicure",
  "data": "2024-01-20",
  "horario": "14:00",
  "status": "confirmada",
  "preco": 40.00
}
```

---

### ❌ TESTAR ERRO DE VALIDAÇÃO

**Método:** POST  
**URL:** `http://localhost:3000/api/clientes`  
**Headers:**
```
Authorization: Bearer {TOKEN}
```

**Body (INVÁLIDO - faltam campos):**
```json
{
  "nome": "Jo" // Nome muito curto
}
```

**Resposta Esperada (400):**
```json
{
  "erro": "Falha na validação",
  "codigo": "VALIDACAO_FALHOU",
  "status": 400,
  "detalhes": {
    "erros": [
      {
        "campo": "nome",
        "mensagem": "Name must be at least 2 characters"
      }
    ]
  },
  "timestamp": "2024-..."
}
```

---

### 🔒 TESTAR ACESSO NEGADO (Sem Token)

**Método:** GET  
**URL:** `http://localhost:3000/api/clientes`  
**Headers:** (SEM Authorization)

**Resposta Esperada (401):**
```json
{
  "erro": "Token não fornecido",
  "codigo": "TOKEN_NAO_FORNECIDO",
  "status": 401,
  "timestamp": "2024-..."
}
```

---

## 📊 Verificar Logs

Os logs estão sendo salvos em `./logs/`:

```bash
# Ver erros
tail -f ./logs/error.log

# Ver todos os eventos
tail -f ./logs/combined.log

# Ver requisições HTTP
tail -f ./logs/http.log
```

---

## 🧬 Rodar Testes Automatizados

```bash
# Rodar todos os testes
npm test

# Rodar com cobertura
npm test -- --coverage

# Rodar em modo watch
npm test -- --watch
```

**Esperado:**
- ~60 testes rodando
- Suite de autenticação passando
- Suite de validação passando
- Suite de segurança passando

---

## 🐛 Troubleshooting

### Erro: "EADDRINUSE: address already in use"
Porta 3000 já está em uso. Mudar em `.env`:
```
PORT=3001
```

### Erro: "JWT_SECRET not found"
Adicionar a `.env`:
```
JWT_SECRET=chave-aleatoria-aqui
JWT_REFRESH_SECRET=outra-chave-aleatoria
```

### Erro: "Cannot find module logger"
Verificar se `utils/logger.js` existe:
```bash
ls -la utils/logger.js
```

### Banco de dados não criado
Verificar permissões de escrita:
```bash
mkdir -p data
chmod 755 data
```

---

## 📱 Teste no Navegador

1. Abra `http://localhost:3000` no navegador
2. O login automático funcionará com token armazenado no localStorage
3. Crie alguns clientes
4. Crie alguns agendamentos
5. Veja o faturamento em tempo real

---

## 🔄 Fluxo Completo de Teste

```
1. npm start
2. POST /api/auth/login → obter token
3. GET /api/auth/me → validar autenticação
4. POST /api/clientes → criar cliente
5. GET /api/clientes → listar clientes
6. POST /api/agendamentos → criar agendamento
7. GET /api/agendamentos → listar agendamentos
8. GET /api/faturamento/resumo → ver faturamento
9. Verificar ./logs/combined.log → ver logging
10. npm test → rodar testes completos
```

---

**Status:** ✅ Sistema pronto para teste  
**Próximos Passos:** Integração com frontend, testes E2E  
**Suporte:** Ver documentação em README.md
