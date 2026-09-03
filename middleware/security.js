// ============================================
// MIDDLEWARE/SECURITY.JS — Segurança & Rate Limiting
// ============================================

const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const logger = require('../utils/logger');
const { RateLimitError } = require('../utils/errors');

// ============================================
// HELMET.JS - HEADERS DE SEGURANÇA
// ============================================

const helmetConfig = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:', 'https:']
    }
  },
  hsts: {
    maxAge: 31536000, // 1 ano
    includeSubDomains: true,
    preload: true
  },
  frameguard: {
    action: 'deny'
  },
  noSniff: true,
  xssFilter: true
});

// ============================================
// RATE LIMITING - LIMITES DIFERENTES
// ============================================

// Limite geral (15 requisições por 15 minutos por IP)
const limitadorGeral = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutos
  max: 100, // 100 requisições
  message: 'Muitas requisições deste IP, tente novamente mais tarde',
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    logger.seguranca('RATE_LIMIT_EXCEEDED', null, {
      ip: req.ip,
      rota: req.originalUrl,
      tentativas: req.rateLimit.current
    });
    res.status(429).json({
      erro: 'Muitas requisições',
      codigo: 'RATE_LIMIT_EXCEEDED',
      retryAfter: req.rateLimit.resetTime
    });
  },
  skip: (req) => {
    // Não aplicar rate limit em ambiente de desenvolvimento
    return process.env.NODE_ENV === 'development';
  }
});

// Limite para login (5 tentativas por 15 minutos)
const limitadorLogin = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: 'Muitas tentativas de login, tente novamente em 15 minutos',
  skipSuccessfulRequests: true, // Não contar tentativas bem-sucedidas
  handler: (req, res) => {
    logger.seguranca('LOGIN_RATE_LIMIT', null, {
      email: req.body?.email,
      ip: req.ip,
      tentativas: req.rateLimit.current
    });
    res.status(429).json({
      erro: 'Muitas tentativas de login',
      codigo: 'LOGIN_RATE_LIMIT',
      retryAfter: 15 * 60
    });
  }
});

// Limite para criar recurso (50 por hora)
const limitadorCriacao = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hora
  max: 50,
  message: 'Limite de criação de recursos excedido',
  handler: (req, res) => {
    logger.seguranca('CREATION_RATE_LIMIT', null, {
      usuario: req.usuario?.email,
      ip: req.ip,
      rota: req.originalUrl
    });
    res.status(429).json({
      erro: 'Limite de criação excedido',
      codigo: 'CREATION_RATE_LIMIT',
      retryAfter: 60 * 60
    });
  }
});

// ============================================
// VALIDAÇÃO DE ORIGEM (CORS SEGURO)
// ============================================

const corsSeguro = {
  origin: function(origin, callback) {
    const origensPermitidas = [
      'http://localhost:3000',
      'http://localhost:3001',
      'http://127.0.0.1:3000',
      process.env.FRONTEND_URL
    ];

    // Permitir requisições sem origin (mobile apps, Postman)
    if (!origin || origensPermitidas.includes(origin)) {
      callback(null, true);
    } else {
      logger.seguranca('CORS_REJEITADO', null, {
        origin,
        ip: require('os').hostname()
      });
      callback(new Error('CORS: Origem não permitida'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  maxAge: 86400 // 24 horas
};

// ============================================
// VERIFICAÇÃO DE API KEY (OPCIONAL)
// ============================================

function verificarAPIKey(req, res, next) {
  const apiKey = req.headers['x-api-key'];
  const chaveExpectada = process.env.API_KEY;

  if (!chaveExpectada) {
    // Se não configurou chave, pular verificação
    return next();
  }

  if (!apiKey || apiKey !== chaveExpectada) {
    logger.seguranca('ACESSO_NEGADO_CHAVE_API', null, {
      ip: req.ip,
      url: req.originalUrl,
      temChave: !!apiKey
    });
    
    return res.status(401).json({
      erro: 'API Key inválida ou ausente',
      codigo: 'INVALID_API_KEY'
    });
  }

  next();
}

// ============================================
// SANITIZAÇÃO DE INPUTS
// ============================================

function sanitizarInputs(req, res, next) {
  // Sanitizar body
  if (req.body) {
    Object.keys(req.body).forEach(key => {
      if (typeof req.body[key] === 'string') {
        // Remover caracteres perigosos
        req.body[key] = req.body[key]
          .trim()
          .replace(/[<>]/g, '') // Remover < >
          .replace(/\\x00/g, ''); // Remover null bytes
      }
    });
  }

  // Sanitizar query params
  if (req.query) {
    Object.keys(req.query).forEach(key => {
      if (typeof req.query[key] === 'string') {
        req.query[key] = req.query[key]
          .trim()
          .replace(/[<>]/g, '');
      }
    });
  }

  next();
}

// ============================================
// LOGS DE SEGURANÇA
// ============================================

function registrarAcessos(req, res, next) {
  // Log de acessos a rotas sensíveis
  const rotasSensiveis = ['/api/auth', '/api/usuarios', '/api/configuracoes'];
  
  if (rotasSensiveis.some(rota => req.path.startsWith(rota))) {
    logger.seguranca('ACESSO_ROTA_SENSIVEL', req.usuario, {
      metodo: req.method,
      rota: req.path,
      ip: req.ip,
      userAgent: req.get('user-agent')
    });
  }

  next();
}

// ============================================
// PREVENÇÃO DE ATAQUES COMUNS
// ============================================

function preventivosSeguranca(req, res, next) {
  // Remover header X-Powered-By
  res.removeHeader('X-Powered-By');
  
  // Adicionar headers de segurança customizados
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  
  next();
}

// ============================================
// EXPORTS
// ============================================

module.exports = {
  // Headers de segurança
  helmetConfig,
  
  // Rate limiters
  limitadorGeral,
  limitadorLogin,
  limitadorCriacao,
  
  // CORS
  corsSeguro,
  
  // Validações
  verificarAPIKey,
  sanitizarInputs,
  registrarAcessos,
  preventivosSeguranca
};
