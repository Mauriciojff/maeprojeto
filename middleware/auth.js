// ============================================
// MIDDLEWARE/AUTH.JS — Sistema de Autenticação
// ============================================

const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { dbRun, dbGet, dbAll } = require('../database');
const logger = require('../utils/logger');

const JWT_SECRET = process.env.JWT_SECRET || 'sua-chave-super-secreta-12345';
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'sua-chave-refresh-67890';

// ============================================
// HASH & VERIFICAÇÃO DE SENHA
// ============================================

async function hashSenha(senha) {
  return await bcrypt.hash(senha, 10);
}

async function verificarSenha(senha, hash) {
  return await bcrypt.compare(senha, hash);
}

// ============================================
// GERAÇÃO DE TOKENS
// ============================================

function gerarToken(usuario) {
  return jwt.sign(
    { 
      id: usuario.id, 
      email: usuario.email,
      role: usuario.role || 'user'
    },
    JWT_SECRET,
    { expiresIn: '24h' }
  );
}

function gerarRefreshToken(usuario) {
  return jwt.sign(
    { id: usuario.id },
    JWT_REFRESH_SECRET,
    { expiresIn: '7d' }
  );
}

// ============================================
// MIDDLEWARE DE AUTENTICAÇÃO
// ============================================

function verificarToken(req, res, next) {
  const authHeader = req.headers.authorization;
  
  if (!authHeader) {
    logger.warn('Tentativa de acesso sem token');
    return res.status(401).json({ 
      erro: 'Token não fornecido',
      codigo: 'TOKEN_NAO_FORNECIDO'
    });
  }

  const token = authHeader.split(' ')[1]; // Bearer <token>

  if (!token) {
    return res.status(401).json({ 
      erro: 'Formato de token inválido',
      codigo: 'FORMATO_INVALIDO'
    });
  }

  try {
    const usuario = jwt.verify(token, JWT_SECRET);
    req.usuario = usuario;
    next();
  } catch (err) {
    logger.warn('Token inválido:', err.message);
    
    if (err.name === 'TokenExpiredError') {
      return res.status(401).json({ 
        erro: 'Token expirado',
        codigo: 'TOKEN_EXPIRADO'
      });
    }

    return res.status(401).json({ 
      erro: 'Token inválido',
      codigo: 'TOKEN_INVALIDO'
    });
  }
}

// ============================================
// MIDDLEWARE DE AUTORIZAÇÃO (ADMIN)
// ============================================

function verificarAdmin(req, res, next) {
  if (req.usuario.role !== 'admin') {
    logger.warn(`Acesso negado para usuário ${req.usuario.id}`);
    return res.status(403).json({ 
      erro: 'Acesso negado - privilégios de administrador necessários',
      codigo: 'ACESSO_NEGADO'
    });
  }
  next();
}

// ============================================
// OPERAÇÕES DE AUTENTICAÇÃO
// ============================================

// Criar tabela de usuários (chamado uma vez)
async function inicializarTabelaUsuarios() {
  try {
    await dbRun(`
      CREATE TABLE IF NOT EXISTS usuarios (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        nome TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        ativo INTEGER DEFAULT 1,
        dataCriacao DATETIME DEFAULT CURRENT_TIMESTAMP,
        ultimoLogin DATETIME
      )
    `);

    // Criar usuário admin padrão (se não existir)
    const admin = await dbGet('SELECT * FROM usuarios WHERE email = ?', ['admin@agenda.com']);
    
    if (!admin) {
      const senhaHash = await hashSenha('Senha123456');
      await dbRun(
        `INSERT INTO usuarios (id, email, senha_hash, nome, role) VALUES (?, ?, ?, ?, ?)`,
        [Date.now().toString(), 'admin@agenda.com', senhaHash, 'Administrador', 'admin']
      );
      logger.info('Usuário admin criado: admin@agenda.com / Senha123456');
    }
  } catch (err) {
    logger.error('Erro ao inicializar tabela de usuários:', err);
  }
}

// ============================================
// ROTAS DE AUTENTICAÇÃO
// ============================================

async function login(req, res) {
  try {
    const { email, senha } = req.body;

    if (!email || !senha) {
      return res.status(400).json({ 
        erro: 'Email e senha são obrigatórios',
        codigo: 'CAMPOS_OBRIGATORIOS'
      });
    }

    // Buscar usuário
    const usuario = await dbGet('SELECT * FROM usuarios WHERE email = ?', [email]);

    if (!usuario) {
      logger.warn(`Tentativa de login falhada: email ${email} não encontrado`);
      return res.status(401).json({ 
        erro: 'Email ou senha incorretos',
        codigo: 'CREDENCIAIS_INVALIDAS'
      });
    }

    // Verificar senha
    const senhaCorreta = await verificarSenha(senha, usuario.senha_hash);

    if (!senhaCorreta) {
      logger.warn(`Tentativa de login falhada: senha incorreta para ${email}`);
      return res.status(401).json({ 
        erro: 'Email ou senha incorretos',
        codigo: 'CREDENCIAIS_INVALIDAS'
      });
    }

    // Gerar tokens
    const token = gerarToken(usuario);
    const refreshToken = gerarRefreshToken(usuario);

    // Registrar último login
    await dbRun(
      'UPDATE usuarios SET ultimoLogin = CURRENT_TIMESTAMP WHERE id = ?',
      [usuario.id]
    );

    logger.info(`Login bem-sucedido: ${email}`);

    res.json({
      mensagem: 'Login realizado com sucesso',
      token,
      refreshToken,
      usuario: {
        id: usuario.id,
        email: usuario.email,
        nome: usuario.nome,
        role: usuario.role
      }
    });
  } catch (err) {
    logger.error('Erro no login:', err);
    res.status(500).json({ 
      erro: 'Erro ao fazer login',
      codigo: 'ERRO_LOGIN'
    });
  }
}

async function refresh(req, res) {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(400).json({ 
        erro: 'Refresh token necessário',
        codigo: 'REFRESH_TOKEN_OBRIGATORIO'
      });
    }

    try {
      const decoded = jwt.verify(refreshToken, JWT_REFRESH_SECRET);
      const usuario = await dbGet('SELECT * FROM usuarios WHERE id = ?', [decoded.id]);

      if (!usuario) {
        return res.status(401).json({ 
          erro: 'Usuário não encontrado',
          codigo: 'USUARIO_NAO_ENCONTRADO'
        });
      }

      const novoToken = gerarToken(usuario);
      const novoRefreshToken = gerarRefreshToken(usuario);

      logger.info(`Token renovado para: ${usuario.email}`);

      res.json({
        token: novoToken,
        refreshToken: novoRefreshToken
      });
    } catch (err) {
      return res.status(401).json({ 
        erro: 'Refresh token inválido',
        codigo: 'REFRESH_TOKEN_INVALIDO'
      });
    }
  } catch (err) {
    logger.error('Erro ao renovar token:', err);
    res.status(500).json({ 
      erro: 'Erro ao renovar token',
      codigo: 'ERRO_REFRESH'
    });
  }
}

async function criarUsuario(req, res) {
  try {
    const { email, senha, nome, role } = req.body;

    if (!email || !senha || !nome) {
      return res.status(400).json({ 
        erro: 'Email, senha e nome são obrigatórios',
        codigo: 'CAMPOS_OBRIGATORIOS'
      });
    }

    // Verificar se usuário já existe
    const existe = await dbGet('SELECT id FROM usuarios WHERE email = ?', [email]);

    if (existe) {
      return res.status(409).json({ 
        erro: 'Email já cadastrado',
        codigo: 'EMAIL_JA_EXISTE'
      });
    }

    const senhaHash = await hashSenha(senha);
    const id = Date.now().toString();

    await dbRun(
      `INSERT INTO usuarios (id, email, senha_hash, nome, role) VALUES (?, ?, ?, ?, ?)`,
      [id, email, senhaHash, nome, role || 'user']
    );

    logger.info(`Novo usuário criado: ${email}`);

    res.status(201).json({
      mensagem: 'Usuário criado com sucesso',
      usuario: { id, email, nome, role: role || 'user' }
    });
  } catch (err) {
    logger.error('Erro ao criar usuário:', err);
    res.status(500).json({ 
      erro: 'Erro ao criar usuário',
      codigo: 'ERRO_CRIACAO'
    });
  }
}

async function obterMeuPerfil(req, res) {
  try {
    const usuario = await dbGet('SELECT * FROM usuarios WHERE id = ?', [req.usuario.id]);

    if (!usuario) {
      return res.status(404).json({ 
        erro: 'Usuário não encontrado',
        codigo: 'USUARIO_NAO_ENCONTRADO'
      });
    }

    res.json({
      id: usuario.id,
      email: usuario.email,
      nome: usuario.nome,
      role: usuario.role,
      ultimoLogin: usuario.ultimoLogin
    });
  } catch (err) {
    logger.error('Erro ao obter perfil:', err);
    res.status(500).json({ 
      erro: 'Erro ao obter perfil',
      codigo: 'ERRO_PERFIL'
    });
  }
}

// ============================================
// EXPORTS
// ============================================

module.exports = {
  // Middleware
  verificarToken,
  verificarAdmin,
  
  // Funções de utilidade
  hashSenha,
  verificarSenha,
  gerarToken,
  gerarRefreshToken,
  inicializarTabelaUsuarios,
  
  // Rotas
  login,
  refresh,
  criarUsuario,
  obterMeuPerfil
};
