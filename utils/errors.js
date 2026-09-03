// ============================================
// UTILS/ERRORS.JS — Erros Customizados
// ============================================

const logger = require('./logger');

// ============================================
// CLASSES DE ERRO CUSTOMIZADAS
// ============================================

class APIError extends Error {
  constructor(mensagem, codigo, status = 500, detalhes = {}) {
    super(mensagem);
    this.nome = this.constructor.name;
    this.codigo = codigo;
    this.status = status;
    this.detalhes = detalhes;
    this.timestamp = new Date().toISOString();
    
    Error.captureStackTrace(this, this.constructor);
  }
  
  toJSON() {
    return {
      erro: this.message,
      codigo: this.codigo,
      status: this.status,
      detalhes: this.detalhes,
      timestamp: this.timestamp
    };
  }
}

// ============================================
// ERROS ESPECÍFICOS
// ============================================

class ValidationError extends APIError {
  constructor(mensagem, detalhes = {}) {
    super(mensagem, 'VALIDATION_ERROR', 400, detalhes);
    this.nome = 'ValidationError';
  }
}

class AuthenticationError extends APIError {
  constructor(mensagem = 'Autenticação necessária', detalhes = {}) {
    super(mensagem, 'AUTHENTICATION_ERROR', 401, detalhes);
    this.nome = 'AuthenticationError';
  }
}

class AuthorizationError extends APIError {
  constructor(mensagem = 'Acesso negado', detalhes = {}) {
    super(mensagem, 'AUTHORIZATION_ERROR', 403, detalhes);
    this.nome = 'AuthorizationError';
  }
}

class NotFoundError extends APIError {
  constructor(recurso, detalhes = {}) {
    super(`${recurso} não encontrado`, 'NOT_FOUND', 404, detalhes);
    this.nome = 'NotFoundError';
  }
}

class ConflictError extends APIError {
  constructor(mensagem, detalhes = {}) {
    super(mensagem, 'CONFLICT', 409, detalhes);
    this.nome = 'ConflictError';
  }
}

class DatabaseError extends APIError {
  constructor(mensagem = 'Erro ao acessar banco de dados', detalhes = {}) {
    super(mensagem, 'DATABASE_ERROR', 500, detalhes);
    this.nome = 'DatabaseError';
  }
}

class InternalServerError extends APIError {
  constructor(mensagem = 'Erro interno do servidor', detalhes = {}) {
    super(mensagem, 'INTERNAL_SERVER_ERROR', 500, detalhes);
    this.nome = 'InternalServerError';
  }
}

class RateLimitError extends APIError {
  constructor(mensagem = 'Muitas requisições', retryAfter = 60) {
    super(mensagem, 'RATE_LIMIT', 429, { retryAfter });
    this.nome = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

// ============================================
// MIDDLEWARE DE TRATAMENTO DE ERROS
// ============================================

function errorHandler(err, req, res, next) {
  // Se não é APIError, converter para InternalServerError
  if (!(err instanceof APIError)) {
    logger.error('Erro não tratado:', err);
    
    const erro = new InternalServerError(
      process.env.NODE_ENV === 'production' 
        ? 'Erro interno do servidor' 
        : err.message,
      { originalErro: err.message }
    );
    
    return res.status(erro.status).json(erro.toJSON());
  }
  
  // Log do erro
  logger.warn(`${err.nome}: ${err.message}`, {
    codigo: err.codigo,
    status: err.status,
    usuario: req.usuario?.email,
    url: req.originalUrl,
    detalhes: err.detalhes
  });
  
  // Responder com erro
  res.status(err.status).json(err.toJSON());
}

// ============================================
// WRAPPER PARA ROTAS ASYNC
// ============================================

function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

// ============================================
// VALIDADORES HELPERS
// ============================================

function validarCamposObrigatorios(obj, campos) {
  const faltantes = campos.filter(campo => !obj[campo]);
  
  if (faltantes.length > 0) {
    throw new ValidationError(
      'Campos obrigatórios faltando',
      { campos: faltantes }
    );
  }
}

function validarTipo(valor, tipo, nomeCampo) {
  const tipoReal = typeof valor;
  
  if (tipoReal !== tipo) {
    throw new ValidationError(
      `Campo '${nomeCampo}' deve ser do tipo ${tipo}`,
      { campo: nomeCampo, tipoEsperado: tipo, tipoRecebido: tipoReal }
    );
  }
}

function validarIntervalo(valor, min, max, nomeCampo) {
  if (valor < min || valor > max) {
    throw new ValidationError(
      `Campo '${nomeCampo}' deve estar entre ${min} e ${max}`,
      { campo: nomeCampo, min, max, valor }
    );
  }
}

function validarFormato(valor, regex, nomeCampo, formato = 'formato inválido') {
  if (!regex.test(valor)) {
    throw new ValidationError(
      `Campo '${nomeCampo}' tem ${formato}`,
      { campo: nomeCampo, valor }
    );
  }
}

// ============================================
// EXPORTS
// ============================================

module.exports = {
  // Classes
  APIError,
  ValidationError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ConflictError,
  DatabaseError,
  InternalServerError,
  RateLimitError,
  
  // Middleware
  errorHandler,
  asyncHandler,
  
  // Validadores
  validarCamposObrigatorios,
  validarTipo,
  validarIntervalo,
  validarFormato
};
