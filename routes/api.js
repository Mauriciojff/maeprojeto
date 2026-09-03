// ============================================
// ROUTES/API.JS — Rotas da API Principal
// ============================================

const express = require('express');
const router = express.Router();
const { dbRun, dbGet, dbAll } = require('../database');

// Utilitários
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

router.get('/clientes', async (req, res) => {
  try {
    const clientes = await dbAll(`SELECT * FROM clientes WHERE ativo = 1 ORDER BY nome ASC`);
    res.json(clientes);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

router.get('/clientes/:id', async (req, res) => {
  try {
    const cliente = await dbGet(`SELECT * FROM clientes WHERE id = ?`, [req.params.id]);
    if (!cliente) return res.status(404).json({ erro: 'Cliente não encontrado' });
    res.json(cliente);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

router.post('/clientes', async (req, res) => {
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

router.put('/clientes/:id', async (req, res) => {
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

router.delete('/clientes/:id', async (req, res) => {
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

router.get('/agendamentos', async (req, res) => {
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

router.get('/agendamentos/data/:data', async (req, res) => {
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

router.get('/agendamentos/:id', async (req, res) => {
  try {
    const agendamento = await dbGet(`SELECT * FROM agendamentos WHERE id = ?`, [req.params.id]);
    if (!agendamento) return res.status(404).json({ erro: 'Agendamento não encontrado' });
    res.json(agendamento);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

router.post('/agendamentos', async (req, res) => {
  try {
    const { clienteId, servico, data, horario, status, obs, preco } = req.body;

    if (!clienteId || !servico || !data || !horario) {
      return res.status(400).json({ erro: 'Campos obrigatórios faltando' });
    }

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

router.put('/agendamentos/:id', async (req, res) => {
  try {
    const { clienteId, servico, data, horario, status, obs, preco } = req.body;

    await dbRun(
      `UPDATE agendamentos SET clienteId = ?, servico = ?, data = ?, horario = ?, status = ?, obs = ?, preco = ? WHERE id = ?`,
      [clienteId, servico, data, horario, status, obs, preco, req.params.id]
    );

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

router.delete('/agendamentos/:id', async (req, res) => {
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

router.get('/faturamento', async (req, res) => {
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

router.get('/faturamento/resumo', async (req, res) => {
  try {
    const hoje = formatarDataISO(new Date());
    const agora = new Date();
    const inicioSemana = new Date(agora);
    inicioSemana.setDate(agora.getDate() - agora.getDay() + 1);
    const inicioMes = new Date(agora.getFullYear(), agora.getMonth(), 1);

    const fatHoje = await dbGet(
      `SELECT SUM(preco) as total, COUNT(*) as count FROM faturamento WHERE dataRealizacao = ?`,
      [hoje]
    );

    const fatSemana = await dbGet(
      `SELECT SUM(preco) as total, COUNT(*) as count FROM faturamento WHERE dataRealizacao >= ? AND dataRealizacao <= ?`,
      [formatarDataISO(inicioSemana), hoje]
    );

    const fatMes = await dbGet(
      `SELECT SUM(preco) as total, COUNT(*) as count FROM faturamento WHERE dataRealizacao >= ?`,
      [formatarDataISO(inicioMes)]
    );

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

router.get('/configuracoes', async (req, res) => {
  try {
    const configs = await dbAll(`SELECT chave, valor FROM configuracoes`);
    const obj = {};
    configs.forEach(c => obj[c.chave] = c.valor);
    res.json(obj);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

router.put('/configuracoes/:chave', async (req, res) => {
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

router.post('/whatsapp/log', async (req, res) => {
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

router.get('/whatsapp/logs', async (req, res) => {
  try {
    const logs = await dbAll(`SELECT * FROM logs_whatsapp ORDER BY dataEnvio DESC LIMIT 50`);
    res.json(logs);
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

// ============================================
// ROTAS - DADOS
// ============================================

router.get('/export', async (req, res) => {
  try {
    const clientes = await dbAll(`SELECT * FROM clientes WHERE ativo = 1`);
    const agendamentos = await dbAll(`SELECT * FROM agendamentos`);
    const faturamento = await dbAll(`SELECT * FROM faturamento`);
    const configuracoes = await dbAll(`SELECT * FROM configuracoes`);

    res.json({
      clientes,
      agendamentos,
      faturamento,
      configuracoes,
      dataExportacao: new Date().toISOString()
    });
  } catch (err) {
    res.status(500).json({ erro: err.message });
  }
});

router.post('/import', async (req, res) => {
  try {
    const { clientes, agendamentos, configuracoes } = req.body;

    if (Array.isArray(clientes)) {
      for (const c of clientes) {
        await dbRun(
          `INSERT OR IGNORE INTO clientes (id, nome, telefone, email) VALUES (?, ?, ?, ?)`,
          [c.id, c.nome, c.telefone, c.email]
        );
      }
    }

    if (Array.isArray(agendamentos)) {
      for (const a of agendamentos) {
        await dbRun(
          `INSERT OR IGNORE INTO agendamentos (id, clienteId, servico, data, horario, status, obs, preco) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
          [a.id, a.clienteId, a.servico, a.data, a.horario, a.status, a.obs, a.preco]
        );
      }
    }

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

module.exports = router;