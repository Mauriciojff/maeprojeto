// ============================================
// UTILS/LOGGER.JS — Sistema de Logging
// ============================================

const winston = require('winston');
const path = require('path');
const fs = require('fs');

// Criar pasta de logs se não existir
const logsDir = path.join(__dirname, '..', 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// ============================================
// CONFIGURAÇÃO DO LOGGER
// ============================================

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  
  defaultMeta: { 
    service: 'agenda-mae',
    ambiente: process.env.NODE_ENV || 'development'
  },
  
  transports: [
    // Arquivo de erros
    new winston.transports.File({
      filename: path.join(logsDir, 'error.log'),
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5
    }),
    
    // Arquivo combinado
    new winston.transports.File({
      filename: path.join(logsDir, 'combined.log'),
      maxsize: 5242880, // 5MB
      maxFiles: 10
    }),
    
    // Arquivo de requisições HTTP
    new winston.transports.File({
      filename: path.join(logsDir, 'http.log'),
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
        winston.format.printf(info => {
          return `[${info.timestamp}] ${info.level.toUpperCase()}: ${info.message}`;
        })
      )
    })
  ]
});

// Adicionar console em desenvolvimento
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.timestamp({ format: 'HH:mm:ss' }),
      winston.format.printf(info => {
        const { timestamp, level, message, ...meta } = info;
        const metaStr = Object.keys(meta).length 
          ? JSON.stringify(meta, null, 2) 
          : '';
        return `${timestamp} [${level}]: ${message} ${metaStr}`;
      })
    )
  }));
}

// ============================================
// MIDDLEWARE DE LOGGING HTTP
// ============================================

function loggerHTTP(req, res, next) {
  const inicio = Date.now();
  
  // Capturar resposta original
  const originalSend = res.send;
  
  res.send = function(data) {
    const duracao = Date.now() - inicio;
    const statusCode = res.statusCode;
    
    // Log da requisição HTTP
    logger.http({
      method: req.method,
      url: req.originalUrl,
      status: statusCode,
      duracao: `${duracao}ms`,
      ip: req.ip,
      usuario: req.usuario?.email || 'anônimo',
      userAgent: req.get('user-agent')
    });
    
    // Log de erro se status for 4xx ou 5xx
    if (statusCode >= 400) {
      logger.warn({
        tipo: 'HTTP_ERROR',
        method: req.method,
        url: req.originalUrl,
        status: statusCode,
        duracao: `${duracao}ms`,
        body: req.body
      });
    }
    
    return originalSend.call(this, data);
  };
  
  next();
}

// ============================================
// MÉTODOS DE LOG CUSTOMIZADOS
// ============================================

const customLogger = {
  // Log genérico
  log: (nivel, mensagem, dados = {}) => {
    logger.log(nivel, mensagem, dados);
  },
  
  // Info
  info: (mensagem, dados = {}) => {
    logger.info(mensagem, dados);
  },
  
  // Warning
  warn: (mensagem, dados = {}) => {
    logger.warn(mensagem, dados);
  },
  
  // Error
  error: (mensagem, erro = null, dados = {}) => {
    const meta = {
      ...dados,
      ...(erro instanceof Error && {
        erro: erro.message,
        stack: erro.stack
      })
    };
    logger.error(mensagem, meta);
  },
  
  // Debug
  debug: (mensagem, dados = {}) => {
    logger.debug(mensagem, dados);
  },
  
  // Auditoria
  auditoria: (acao, usuario, recurso, detalhes = {}) => {
    logger.info('AUDITORIA', {
      acao,
      usuario: usuario?.email || 'sistema',
      recurso,
      timestamp: new Date().toISOString(),
      ...detalhes
    });
  },
  
  // Performance
  performance: (operacao, duracao, status = 'sucesso') => {
    logger.info('PERFORMANCE', {
      operacao,
      duracao: `${duracao}ms`,
      status,
      timestamp: new Date().toISOString()
    });
  },
  
  // Segurança
  seguranca: (evento, usuario, detalhes = {}) => {
    logger.warn('SEGURANÇA', {
      evento,
      usuario: usuario?.email || 'desconhecido',
      ip: detalhes.ip,
      timestamp: new Date().toISOString(),
      ...detalhes
    });
  },
  
  // WhatsApp
  whatsapp: (evento, dados = {}) => {
    logger.info('WHATSAPP', {
      evento,
      timestamp: new Date().toISOString(),
      ...dados
    });
  },
  
  // Database
  database: (operacao, tabela, duracao = null, erro = null) => {
    const nivel = erro ? 'error' : 'debug';
    logger[nivel]('DATABASE', {
      operacao,
      tabela,
      duracao: duracao ? `${duracao}ms` : null,
      erro: erro?.message,
      timestamp: new Date().toISOString()
    });
  }
};

// ============================================
// CAPTURADOR DE EXCEÇÕES NÃO CAPTURADAS
// ============================================

process.on('unhandledRejection', (razao, promise) => {
  logger.error('UNHANDLED REJECTION', {
    razao: razao instanceof Error ? razao.message : razao,
    stack: razao instanceof Error ? razao.stack : null,
    promise: promise.toString()
  });
});

process.on('uncaughtException', (erro) => {
  logger.error('UNCAUGHT EXCEPTION', {
    erro: erro.message,
    stack: erro.stack
  });
  // Encerrar processo após log
  setTimeout(() => process.exit(1), 1000);
});

// ============================================
// EXPORTS
// ============================================

module.exports = customLogger;
module.exports.loggerHTTP = loggerHTTP;
module.exports.winston = logger;
