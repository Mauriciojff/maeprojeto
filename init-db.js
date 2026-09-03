// ============================================
// INIT-DB.JS — Inicializador do Banco de Dados
// ============================================

require('dotenv').config();
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');
const { hashSenha } = require('./middleware/auth');
const crypto = require('crypto');

const dbPath = path.join(__dirname, 'data', 'agenda.db');

// Criar pasta data
const dataDir = path.dirname(dbPath);
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

// Conectar ao banco
const db = new sqlite3.Database(dbPath, async (err) => {
  if (err) {
    console.error('❌ Erro ao conectar ao banco:', err.message);
    process.exit(1);
  }

  console.log('✅ Conectado ao SQLite');
  
  try {
    await inicializarBancoDados();
    console.log('✅ Banco de dados inicializado com sucesso');
    db.close();
    process.exit(0);
  } catch (erro) {
    console.error('❌ Erro na inicialização:', erro.message);
    db.close();
    process.exit(1);
  }
});

// ============================================
// FUNÇÕES HELPER
// ============================================

const dbRun = (sql, params = []) => {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function(err) {
      if (err) reject(err);
      else resolve({ lastID: this.lastID, changes: this.changes });
    });
  });
};

const dbGet = (sql, params = []) => {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => {
      if (err) reject(err);
      else resolve(row);
    });
  });
};

// ============================================
// INICIALIZAÇÃO PRINCIPAL
// ============================================

async function inicializarBancoDados() {
  // 1. Criar tabela de usuários
  console.log('📝 Criando tabela de usuários...');
  await dbRun(`
    CREATE TABLE IF NOT EXISTS usuarios (
      id TEXT PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      senha_hash TEXT NOT NULL,
      nome TEXT,
      role TEXT DEFAULT 'usuario',
      ativo INTEGER DEFAULT 1,
      dataCriacao DATETIME DEFAULT CURRENT_TIMESTAMP,
      ultimoLogin DATETIME
    )
  `);

  // 2. Criar tabela de clientes
  console.log('📝 Criando tabela de clientes...');
  await dbRun(`
    CREATE TABLE IF NOT EXISTS clientes (
      id TEXT PRIMARY KEY,
      nome TEXT NOT NULL,
      telefone TEXT,
      email TEXT,
      dataCadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
      ativo INTEGER DEFAULT 1
    )
  `);

  // 3. Criar tabela de agendamentos
  console.log('📝 Criando tabela de agendamentos...');
  await dbRun(`
    CREATE TABLE IF NOT EXISTS agendamentos (
      id TEXT PRIMARY KEY,
      clienteId TEXT NOT NULL,
      servico TEXT NOT NULL,
      data TEXT NOT NULL,
      horario TEXT NOT NULL,
      status TEXT DEFAULT 'pendente',
      obs TEXT,
      preco REAL,
      confirmaçaoWhatsapp INTEGER DEFAULT 0,
      dataCriacao DATETIME DEFAULT CURRENT_TIMESTAMP,
      dataRealizacao DATETIME,
      FOREIGN KEY(clienteId) REFERENCES clientes(id)
    )
  `);

  // 4. Criar tabela de configurações
  console.log('📝 Criando tabela de configurações...');
  await dbRun(`
    CREATE TABLE IF NOT EXISTS configuracoes (
      id INTEGER PRIMARY KEY,
      chave TEXT UNIQUE,
      valor TEXT
    )
  `);

  // 5. Criar tabela de logs WhatsApp
  console.log('📝 Criando tabela de logs WhatsApp...');
  await dbRun(`
    CREATE TABLE IF NOT EXISTS logs_whatsapp (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      agendamentoId TEXT,
      clienteId TEXT,
      mensagem TEXT,
      status TEXT,
      dataEnvio DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(agendamentoId) REFERENCES agendamentos(id),
      FOREIGN KEY(clienteId) REFERENCES clientes(id)
    )
  `);

  // 6. Criar tabela de faturamento
  console.log('📝 Criando tabela de faturamento...');
  await dbRun(`
    CREATE TABLE IF NOT EXISTS faturamento (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      agendamentoId TEXT UNIQUE,
      clienteId TEXT,
      servico TEXT,
      preco REAL,
      dataRealizacao DATE,
      status TEXT DEFAULT 'realizado',
      FOREIGN KEY(agendamentoId) REFERENCES agendamentos(id),
      FOREIGN KEY(clienteId) REFERENCES clientes(id)
    )
  `);

  // 7. Criar usuário admin padrão
  console.log('👤 Criando usuário admin...');
  
  const usuarioAdmin = {
    id: crypto.randomUUID(),
    email: 'admin@agenda.com',
    senha: 'Senha123456', // Default password - MUDAR EM PRODUÇÃO!
    nome: 'Admin',
    role: 'admin'
  };

  // Verificar se usuário já existe
  const usuarioExistente = await dbGet(
    'SELECT id FROM usuarios WHERE email = ?',
    [usuarioAdmin.email]
  );

  if (!usuarioExistente) {
    const senhaHash = await hashSenha(usuarioAdmin.senha);
    
    await dbRun(
      `INSERT INTO usuarios (id, email, senha_hash, nome, role, ativo)
       VALUES (?, ?, ?, ?, ?, 1)`,
      [usuarioAdmin.id, usuarioAdmin.email, senhaHash, usuarioAdmin.nome, usuarioAdmin.role]
    );
    
    console.log('✅ Usuário admin criado:');
    console.log(`   Email: ${usuarioAdmin.email}`);
    console.log(`   Senha: ${usuarioAdmin.senha}`);
    console.log(`   ⚠️  MUDAR ESTA SENHA EM PRODUÇÃO!`);
  } else {
    console.log('ℹ️  Usuário admin já existe');
  }

  // 8. Inserir configurações padrão
  console.log('⚙️  Inserindo configurações padrão...');
  
  const configs = [
    { chave: 'precoManicure', valor: '40.00' },
    { chave: 'precoCilios', valor: '80.00' },
    { chave: 'precoCombo', valor: '110.00' },
    { chave: 'horaAbertura', valor: '08:00' },
    { chave: 'horaFechamento', valor: '20:00' },
    { chave: 'intervaloMin', valor: '60' }
  ];

  for (const config of configs) {
    await dbRun(
      `INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)`,
      [config.chave, config.valor]
    );
  }

  console.log('✅ Configurações padrão inseridas');
}

// ============================================
// EXPORTS
// ============================================

module.exports = { inicializarBancoDados };

// Se executado diretamente
if (require.main === module) {
  console.log('\n╔════════════════════════════════════════╗');
  console.log('║   🗄️  Inicializador do Banco de Dados  ║');
  console.log('╚════════════════════════════════════════╝\n');
}
