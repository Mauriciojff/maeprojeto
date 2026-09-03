// ============================================
// DATABASE.JS — Gerenciamento do SQLite
// ============================================

const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.join(__dirname, 'data', 'agenda.db');

// Criar conexão com banco de dados
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Erro ao conectar ao banco de dados:', err.message);
  } else {
    console.log('✅ Conectado ao SQLite');
    initializeDatabase();
  }
});

// Promisificar db.run e db.all
const dbRun = (sql, params = []) => {
  return new Promise((resolve, reject) => {
    db.run(sql, params, (err) => {
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

const dbAll = (sql, params = []) => {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows || []);
    });
  });
};

// Inicializar tabelas
function initializeDatabase() {
  db.serialize(() => {
    // Tabela de usuários
    db.run(`
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

    // Tabela de clientes
    db.run(`
      CREATE TABLE IF NOT EXISTS clientes (
        id TEXT PRIMARY KEY,
        nome TEXT NOT NULL,
        telefone TEXT,
        email TEXT,
        dataCadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
        ativo INTEGER DEFAULT 1
      )
    `);

    // Tabela de agendamentos
    db.run(`
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

    // Tabela de configurações
    db.run(`
      CREATE TABLE IF NOT EXISTS configuracoes (
        id INTEGER PRIMARY KEY,
        chave TEXT UNIQUE,
        valor TEXT
      )
    `);

    // Tabela de logs de WhatsApp
    db.run(`
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

    // Tabela de faturamento
    db.run(`
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

    console.log('✅ Banco de dados inicializado');
    insertDefaultConfig();
  });
}

// Inserir configurações padrão
function insertDefaultConfig() {
  const configs = [
    { chave: 'precoManicure', valor: '40.00' },
    { chave: 'precoCilios', valor: '80.00' },
    { chave: 'precoCombo', valor: '110.00' },
    { chave: 'horaAbertura', valor: '08:00' },
    { chave: 'horaFechamento', valor: '20:00' },
    { chave: 'intervaloMin', valor: '60' }
  ];

  configs.forEach(config => {
    db.run(
      `INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)`,
      [config.chave, config.valor]
    );
  });
}

module.exports = {
  dbRun,
  dbGet,
  dbAll,
  db
};
