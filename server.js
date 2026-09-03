// ============================================
// SERVER.JS — Backend com Express
// ============================================

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
const { dbRun, dbGet, dbAll } = require('./database');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ limit: '50mb', extended: true }));
app.use(express.static(path.join(__dirname)));

// Criar pasta de dados se não existir
if (!fs.existsSync(path.join(__dirname, 'data'))) {
  fs.mkdirSync(path.join(__dirname, 'data'));
}

// ============================================
// UTILITÁRIOS
// ============================================

function gerarId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
}

function formatarDataISO(data) {
  const d = new Date(data);
  const ano = d.getFullYear();
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  return `${ano}-${mes}-${dia}`;
}

// ============================================
// ROTAS - CLIENTES
// ============================================

// GET - Listar clientes
app.get('/api/clientes', async (req, res) => {
  try {
    const clientes = await dbAll(`SELECT * FROM clientes WHERE ativo = 1 ORDER BY nome ASC`);
    res.json(clientes);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// GET - Cliente por ID
app.get('/api/clientes/:id', async (req, res) => {
  try {
    const cliente = await dbGet(`SELECT * FROM clientes WHERE id = ?`, [req.params.id]);
    if (!cliente) return res.status(404).json({ erro: 'Cliente não encontrado' });
    res.json(cliente);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// POST - Criar cliente
app.post('/api/clientes', async (req, res) => {
  try {
    const { nome, telefone, email } = req.body;
    if (!nome) return res.status(400).json({ erro: 'Nome é obrigatório' });

    const id = gerarId();
    await dbRun(
      `INSERT INTO clientes (id, nome, telefone, email) VALUES (?, ?, ?, ?)`,
      [id, nome, telefone || null, email || null]
    );
    res.json({ id, nome, telefone, email, mensagem: 'Cliente criado com sucesso!' });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// PUT - Atualizar cliente
app.put('/api/clientes/:id', async (req, res) => {
  try {
    const { nome, telefone, email } = req.body;
    await dbRun(
      `UPDATE clientes SET nome = ?, telefone = ?, email = ? WHERE id = ?`,
      [nome, telefone, email, req.params.id]
    );
    res.json({ mensagem: 'Cliente atualizado!' });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// DELETE - Excluir cliente (soft delete)
app.delete('/api/clientes/:id', async (req, res) => {
  try {
    await dbRun(`UPDATE clientes SET ativo = 0 WHERE id = ?`, [req.params.id]);
    res.json({ mensagem: 'Cliente excluído!' });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// ============================================
// ROTAS - AGENDAMENTOS
// ============================================

// GET - Listar agendamentos
app.get('/api/agendamentos', async (req, res) => {
  try {
    const { data, status } = req.query;
    let sql = `SELECT * FROM agendamentos WHERE 1=1`;
    const params = [];

    if (data) {
      sql += ` AND data = ?`;
      params.push(data);
    }
    if (status) {
      sql += ` AND status = ?`;
      params.push(status);
    }

    sql += ` ORDER BY data ASC, horario ASC`;
    const agendamentos = await dbAll(sql, params);
    res.json(agendamentos);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// GET - Agendamentos por data
app.get('/api/agendamentos/data/:data', async (req, res) => {
  try {
    const agendamentos = await dbAll(
      `SELECT * FROM agendamentos WHERE data = ? ORDER BY horario ASC`,
      [req.params.data]
    );
    res.json(agendamentos);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// GET - Agendamento por ID
app.get('/api/agendamentos/:id', async (req, res) => {
  try {
    const agendamento = await dbGet(`SELECT * FROM agendamentos WHERE id = ?`, [req.params.id]);
    if (!agendamento) return res.status(404).json({ erro: 'Agendamento não encontrado' });
    res.json(agendamento);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// POST - Criar agendamento
app.post('/api/agendamentos', async (req, res) => {
  try {
    const { clienteId, servico, data, horario, status, obs, preco } = req.body;

    if (!clienteId || !servico || !data || !horario) {
      return res.status(400).json({ erro: 'Campos obrigatórios faltando' });
    }

    // Verificar conflito de horário
    const conflito = await dbGet(
      `SELECT id FROM agendamentos WHERE data = ? AND horario = ? AND status != 'nao_vai'`,
      [data, horario]
    );
    if (conflito) return res.status(409).json({ erro: 'Este horário já está ocupado!' });

    const id = gerarId();
    await dbRun(
      `INSERT INTO agendamentos (id, clienteId, servico, data, horario, status, obs, preco) 
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [id, clienteId, servico, data, horario, status || 'pendente', obs || null, preco || 0]
    );

    res.json({ id, mensagem: 'Agendamento criado com sucesso!' });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// PUT - Atualizar agendamento
app.put('/api/agendamentos/:id', async (req, res) => {
  try {
    const { clienteId, servico, data, horario, status, obs, preco } = req.body;

    await dbRun(
      `UPDATE agendamentos SET clienteId = ?, servico = ?, data = ?, horario = ?, status = ?, obs = ?, preco = ? WHERE id = ?`,
      [clienteId, servico, data, horario, status, obs, preco, req.params.id]
    );

    // Se status for 'realizada', registrar no faturamento
    if (status === 'realizada') {
      const agendamento = await dbGet(`SELECT * FROM agendamentos WHERE id = ?`, [req.params.id]);
      if (agendamento) {
        await dbRun(
          `INSERT OR REPLACE INTO faturamento (agendamentoId, clienteId, servico, preco, dataRealizacao) 
           VALUES (?, ?, ?, ?, ?)`,
          [req.params.id, clienteId, servico, preco, data]
        );
      }
    }

    res.json({ mensagem: 'Agendamento atualizado!' });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// DELETE - Excluir agendamento
app.delete('/api/agendamentos/:id', async (req, res) => {
  try {
    await dbRun(`DELETE FROM agendamentos WHERE id = ?`, [req.params.id]);
    await dbRun(`DELETE FROM faturamento WHERE agendamentoId = ?`, [req.params.id]);
    res.json({ mensagem: 'Agendamento excluído!' });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// ============================================
// ROTAS - FATURAMENTO
// ============================================

// GET - Faturamento por período
app.get('/api/faturamento', async (req, res) => {
  try {
    const { dataInicio, dataFim } = req.query;
    let sql = `SELECT * FROM faturamento WHERE 1=1`;
    const params = [];

    if (dataInicio) {
      sql += ` AND dataRealizacao >= ?`;
      params.push(dataInicio);
    }
    if (dataFim) {
      sql += ` AND dataRealizacao <= ?`;
      params.push(dataFim);
    }

    sql += ` ORDER BY dataRealizacao DESC`;
    const faturamento = await dbAll(sql, params);
    res.json(faturamento);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// GET - Resumo de faturamento
app.get('/api/faturamento/resumo', async (req, res) => {
  try {
    const hoje = formatarDataISO(new Date());
    const agora = new Date();
    const inicioSemana = new Date(agora);
    inicioSemana.setDate(agora.getDate() - agora.getDay() + 1);
    const inicioMes = new Date(agora.getFullYear(), agora.getMonth(), 1);

    // Hoje
    const fatHoje = await dbGet(
      `SELECT SUM(preco) as total, COUNT(*) as count FROM faturamento WHERE dataRealizacao = ?`,
      [hoje]
    );

    // Semana
    const fatSemana = await dbGet(
      `SELECT SUM(preco) as total, COUNT(*) as count FROM faturamento WHERE dataRealizacao >= ? AND dataRealizacao <= ?`,
      [formatarDataISO(inicioSemana), hoje]
    );

    // Mês
    const fatMes = await dbGet(
      `SELECT SUM(preco) as total, COUNT(*) as count FROM faturamento WHERE dataRealizacao >= ?`,
      [formatarDataISO(inicioMes)]
    );

    // Total
    const fatTotal = await dbGet(
      `SELECT SUM(preco) as total, COUNT(*) as count FROM faturamento`
    );

    res.json({
      hoje: { total: fatHoje.total || 0, count: fatHoje.count || 0 },
      semana: { total: fatSemana.total || 0, count: fatSemana.count || 0 },
      mes: { total: fatMes.total || 0, count: fatMes.count || 0 },
      total: { total: fatTotal.total || 0, count: fatTotal.count || 0 }
    });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// ============================================
// ROTAS - CONFIGURAÇÕES
// ============================================

// GET - Obter configurações
app.get('/api/configuracoes', async (req, res) => {
  try {
    const configs = await dbAll(`SELECT chave, valor FROM configuracoes`);
    const obj = {};
    configs.forEach(c => obj[c.chave] = c.valor);
    res.json(obj);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// PUT - Atualizar configuração
app.put('/api/configuracoes/:chave', async (req, res) => {
  try {
    const { valor } = req.body;
    await dbRun(
      `INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)`,
      [req.params.chave, valor]
    );
    res.json({ mensagem: 'Configuração atualizada!' });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// ============================================
// ROTAS - WHATSAPP
// ============================================

// POST - Registrar envio WhatsApp
app.post('/api/whatsapp/log', async (req, res) => {
  try {
    const { agendamentoId, clienteId, mensagem, status } = req.body;
    await dbRun(
      `INSERT INTO logs_whatsapp (agendamentoId, clienteId, mensagem, status) VALUES (?, ?, ?, ?)`,
      [agendamentoId, clienteId, mensagem, status || 'enviado']
    );
    res.json({ mensagem: 'Log registrado!' });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// GET - Logs de WhatsApp
app.get('/api/whatsapp/logs', async (req, res) => {
  try {
    const logs = await dbAll(`SELECT * FROM logs_whatsapp ORDER BY dataEnvio DESC LIMIT 50`);
    res.json(logs);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// ============================================
// ROTAS - EXPORT/IMPORT
// ============================================

// GET - Exportar dados
app.get('/api/export', async (req, res) => {
  try {
    const clientes = await dbAll(`SELECT * FROM clientes WHERE ativo = 1`);
    const agendamentos = await dbAll(`SELECT * FROM agendamentos`);
    const faturamento = await dbAll(`SELECT * FROM faturamento`);
    const configuracoes = await dbAll(`SELECT * FROM configuracoes`);

    const dados = {
      clientes,
      agendamentos,
      faturamento,
      configuracoes,
      dataExportacao: new Date().toISOString()
    };

    res.json(dados);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// POST - Importar dados
app.post('/api/import', async (req, res) => {
  try {
    const { clientes, agendamentos, configuracoes } = req.body;

    // Importar clientes
    if (Array.isArray(clientes)) {
      for (const c of clientes) {
        await dbRun(
          `INSERT OR IGNORE INTO clientes (id, nome, telefone, email) VALUES (?, ?, ?, ?)`,
          [c.id, c.nome, c.telefone, c.email]
        );
      }
    }

    // Importar agendamentos
    if (Array.isArray(agendamentos)) {
      for (const a of agendamentos) {
        await dbRun(
          `INSERT OR IGNORE INTO agendamentos (id, clienteId, servico, data, horario, status, obs, preco) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
          [a.id, a.clienteId, a.servico, a.data, a.horario, a.status, a.obs, a.preco]
        );
      }
    }

    // Importar configurações
    if (Array.isArray(configuracoes)) {
      for (const c of configuracoes) {
        await dbRun(
          `INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)`,
          [c.chave, c.valor]
        );
      }
    }

    res.json({ mensagem: 'Dados importados com sucesso!' });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// ============================================
// INICIAR SERVIDOR
// ============================================

app.listen(PORT, () => {
  console.log(`\n🚀 Servidor rodando em http://localhost:${PORT}`);
  console.log(`📱 Acesse a aplicação em http://localhost:${PORT}`);
});
