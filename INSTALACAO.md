# 📖 MANUAL DE INSTALAÇÃO COMPLETO

## 🎯 Objetivo
Transformar o projeto em um **sistema profissional de agendamento** para manicure e cílios com WhatsApp integrado.

---

## 📋 PRÉ-REQUISITOS

### ✅ Verifique se tem:

1. **Node.js** (versão 14 ou superior)
   ```bash
   node --version
   ```
   Se não tiver, baixe em: https://nodejs.org/

2. **npm** (geralmente vem com Node.js)
   ```bash
   npm --version
   ```

3. **WhatsApp** instalado no celular (para integração)

4. **Editor de código** (recomendado: VS Code)
   - Baixe em: https://code.visualstudio.com/

---

## 🚀 INSTALAÇÃO PASSO A PASSO

### PASSO 1: Abrir o Terminal

#### Windows:
1. Pressione `Win + R`
2. Digite `cmd`
3. Pressione Enter

#### Mac/Linux:
1. Pressione `Ctrl + Alt + T` (Linux) ou `Cmd + Space` (Mac)
2. Digite `terminal`
3. Pressione Enter

### PASSO 2: Navegar até a pasta do projeto

```bash
cd Desktop/projetomãe/mae/maeprojeto
```

**Ou use o arquivo Explorer do Windows:**
1. Abra `C:\Users\[seu-usuario]\Desktop\projetomãe\mae\maeprojeto`
2. Clique na barra de endereço
3. Digite `cmd`
4. Pressione Enter

### PASSO 3: Instalar Dependências

```bash
npm install
```

**O que faz:** Baixa todas as bibliotecas necessárias (Express, SQLite, WhatsApp, etc)

⏱️ **Tempo:** 2-5 minutos

📊 **Status:** Você verá `added 150+ packages`

### PASSO 4: Criar arquivo .env (Opcional)

```bash
cp .env.example .env
```

**Ou manualmente:**
1. Copie o arquivo `.env.example`
2. Renomeie para `.env`
3. Você pode editar os valores depois

### PASSO 5: Iniciar o Servidor

```bash
npm start
```

**Você deve ver:**
```
╔════════════════════════════════════════╗
║     💅 AGENDA DA MÃE - v1.0.0         ║
╚════════════════════════════════════════╝

🚀 Servidor rodando em http://localhost:3000
📱 Abra no navegador: http://localhost:3000
💾 Banco de dados: ./data/agenda.db

📱 Iniciando WhatsApp Web...
   Escaneie o QR Code com seu celular

═════════════════════════════════════════
✅ Sistema pronto para uso!
═════════════════════════════════════════
```

### PASSO 6: Abrir no Navegador

1. **Opção A:** Clique no link: `http://localhost:3000`
2. **Opção B:** Abra o navegador e digite: `http://localhost:3000`

---

## 📱 CONECTAR WHATSAPP (Primeira Vez)

### Passo 1: Escanear QR Code

Quando o servidor inicia, um **QR Code** aparecerá no terminal assim:

```
📱 Escaneie este QR Code com WhatsApp:
██████████████████████████████
██ ▄▄▄▄▄ █▄█▀ ██ ▄▄▄▄▄ ████
██ █   █ █ █ ▀██ █   █ ████
██ █▄▄▄█ █ ▀█▀▀█ █▄▄▄█ ████
██▄▄▄▄▄▄▄█▀█ █ █▄▄▄▄▄▄▄████
██████████████████████████████
```

### Passo 2: Usar WhatsApp Web

1. Abra **WhatsApp** no seu celular
2. Vá para **Configurações** (ícone de engrenagem)
3. Toque em **Dispositivos Vinculados**
4. Toque em **Vincular um dispositivo**
5. Aponte a **câmera** para o **QR Code** do terminal

### Passo 3: Confirmar

Depois de alguns segundos, você verá:
```
✅ WhatsApp conectado com sucesso!
```

---

## ✅ TESTAR SE TÁ FUNCIONANDO

### 1. Acessar o App

Abra: `http://localhost:3000`

Você deve ver:
- Cabeçalho rosa com "💅 Agenda da Mãe"
- Botão "+ Novo Agendamento"
- Abas: Agenda, Faturamento, Clientes, Configurações

### 2. Criar uma Cliente

1. Clique em "👩 Clientes"
2. Clique em "+ Nova Cliente"
3. Preencha:
   - **Nome:** Maria Silva
   - **Telefone:** (11) 99999-9999
4. Clique em "Salvar"

### 3. Criar um Agendamento

1. Clique em "+ Novo Agendamento"
2. Preencha:
   - **Cliente:** Maria Silva
   - **Serviço:** Manicure + Cílios
   - **Data:** Selecione uma data
   - **Horário:** Selecione um horário
   - **Status:** Confirmada
3. Clique em "Salvar"

### 4. Verificar Faturamento

1. Clique em "💰 Faturamento"
2. Você deve ver valores atualizados

✅ **Se chegou aqui, está funcionando!**

---

## 🎨 PERSONALIZAÇÕES BÁSICAS

### Mudar Preços

1. Clique em "⚙️ Configurações"
2. Vá para "Preços dos Serviços"
3. Altere os valores:
   - Manicure: R$ 40,00
   - Cílios: R$ 80,00
   - Combo: R$ 110,00
4. Clique em "Salvar Preços"

### Mudar Horários

1. "⚙️ Configurações"
2. "Horário de Funcionamento"
3. Altere:
   - Abertura: 08:00
   - Fechamento: 20:00
   - Intervalo: 30 ou 60 minutos
4. Clique em "Salvar Horário"

### Mudar Cores

Arquivo: `style.css`

Procure por:
```css
:root {
  --primary: #e91e63;     /* Mude esse valor */
}
```

Cores sugeridas:
- Rosa: `#e91e63`
- Roxo: `#9c27b0`
- Verde: `#4caf50`
- Azul: `#2196F3`

---

## 📊 ESTRUTURA DE DADOS

### Banco de Dados Criado Automaticamente

Arquivo: `data/agenda.db` (SQLite)

**Tabelas:**
1. **clientes** — Nome, telefone, email
2. **agendamentos** — Data, hora, cliente, serviço
3. **faturamento** — Preço, data realização
4. **configuracoes** — Preços, horários
5. **logs_whatsapp** — Histórico de mensagens

---

## 🆘 SOLUÇÃO DE PROBLEMAS

### ❌ Erro: "npm: comando não encontrado"

**Causa:** Node.js não está instalado

**Solução:**
1. Baixe Node.js: https://nodejs.org/
2. Instale com as opções padrão
3. Reinicie o computador
4. Tente novamente: `npm install`

---

### ❌ Erro: "Porta 3000 já em uso"

**Causa:** Outro programa está usando a porta 3000

**Solução - Opção 1:**
```bash
PORT=3001 npm start
```
Depois abra: `http://localhost:3001`

**Solução - Opção 2:**
1. Pressione `Ctrl + C` no terminal para parar
2. Espere 30 segundos
3. Digite: `npm start`

---

### ❌ WhatsApp não conecta

**Causa:** Sessão expirada ou problema de conexão

**Solução:**
1. Pare o servidor: `Ctrl + C`
2. Delete a pasta `.wwebjs_auth`
3. Reinicie: `npm start`
4. Escaneie o QR Code novamente

---

### ❌ "Erro ao conectar ao banco de dados"

**Causa:** Arquivo `agenda.db` corrompido

**Solução:**
```bash
# Pare o servidor (Ctrl + C)
rm -rf data/agenda.db
npm start
```
O banco será recriado automaticamente.

---

### ❌ Página em branco ao abrir

**Causa:** Servidor não iniciou ou port incorreta

**Solução:**
1. Verifique no terminal se vê: "✅ Sistema pronto para uso!"
2. Tente: `http://localhost:3000` (não esqueça o `:3000`)
3. Atualize a página: `Ctrl + F5`

---

## 💾 BACKUP E RESTAURAÇÃO

### Fazer Backup

1. "⚙️ Configurações"
2. "Dados"
3. Clique em "📥 Exportar Dados (JSON)"
4. Salve o arquivo em um local seguro

### Restaurar Dados

1. "⚙️ Configurações"
2. "Dados"
3. Clique em "📂 Importar Dados"
4. Selecione o arquivo JSON

---

## 🔄 MODO DESENVOLVIMENTO

Para desenvolvimento com auto-reload:

```bash
npm run dev
```

Sempre que você salvar um arquivo, o servidor reinicia automaticamente.

---

## 📞 SUPORTE

### Verifique:
- [ ] Node.js está instalado? (`node --version`)
- [ ] npm está funcionando? (`npm --version`)
- [ ] Você abriu a pasta correta no terminal?
- [ ] Você rodou `npm install`?
- [ ] Porta 3000 está livre?
- [ ] Você tem WhatsApp no celular?

### Mais informações:
- Leia: `README.md`
- Leia: `QUICK_START.md`
- Acesse: `http://localhost:3000/health` para status

---

## 🎉 Pronto!

Você tem um **sistema profissional de agendamento** funcionando!

**Próximos passos:**
1. ✅ Adicione mais clientes
2. ✅ Configure preços
3. ✅ Teste o WhatsApp
4. ✅ Exporte seus dados
5. ✅ Compartilhe com sua mãe! 💅

---

**Desenvolvido com ❤️ para facilitar a vida** ✨
