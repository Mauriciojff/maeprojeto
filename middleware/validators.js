// ============================================
// MIDDLEWARE/VALIDATORS.JS — Validação de Inputs
// ============================================

const { body, param, query, validationResult } = require('express-validator');
const logger = require('../utils/logger');

// ============================================
// MIDDLEWARE PARA CAPTURAR ERROS DE VALIDAÇÃO
// ============================================

function tratarErrosValidacao(req, res, next) {
  const erros = validationResult(req);
  
  if (!erros.isEmpty()) {
    logger.warn(`Validação falhou: ${JSON.stringify(erros.array())}`);
    
    return res.status(400).json({
      erro: 'Validação falhou',
      codigo: 'VALIDACAO_FALHOU',
      detalhes: erros.array().map(e => ({
        campo: e.param,
        mensagem: e.msg,
        valor: e.value
      }))
    });
  }
  next();
}

// ============================================
// VALIDADORES DE CLIENTES
// ============================================

const validarClienteNovo = [
  body('nome')
    .trim()
    .notEmpty().withMessage('Nome é obrigatório')
    .isLength({ min: 2, max: 150 }).withMessage('Nome deve ter entre 2 e 150 caracteres'),
  
  body('telefone')
    .optional()
    .trim()
    .matches(/^\d{10,15}$/).withMessage('Telefone inválido (10-15 dígitos)'),
  
  body('email')
    .optional()
    .trim()
    .isEmail().withMessage('Email inválido'),
  
  tratarErrosValidacao
];

const validarClienteAtualizacao = [
  param('id')
    .trim()
    .notEmpty().withMessage('ID é obrigatório'),
  
  body('nome')
    .optional()
    .trim()
    .isLength({ min: 2, max: 150 }).withMessage('Nome deve ter entre 2 e 150 caracteres'),
  
  body('telefone')
    .optional()
    .trim()
    .matches(/^\d{10,15}$/).withMessage('Telefone inválido'),
  
  body('email')
    .optional()
    .trim()
    .isEmail().withMessage('Email inválido'),
  
  tratarErrosValidacao
];

// ============================================
// VALIDADORES DE AGENDAMENTOS
// ============================================

const validarAgendamentoNovo = [
  body('clienteId')
    .trim()
    .notEmpty().withMessage('Cliente é obrigatório'),
  
  body('servico')
    .trim()
    .isIn(['manicure', 'cilios', 'combo']).withMessage('Serviço inválido'),
  
  body('data')
    .trim()
    .matches(/^\d{4}-\d{2}-\d{2}$/).withMessage('Data deve estar no formato YYYY-MM-DD'),
    
  body('horario')
    .trim()
    .matches(/^\d{2}:\d{2}$/).withMessage('Horário deve estar no formato HH:MM'),
  
  body('status')
    .optional()
    .isIn(['pendente', 'confirmada', 'nao_vai', 'realizada']).withMessage('Status inválido'),
  
  body('obs')
    .optional()
    .trim()
    .isLength({ max: 500 }).withMessage('Observações não pode ter mais de 500 caracteres'),
  
  body('preco')
    .optional()
    .isFloat({ min: 0 }).withMessage('Preço deve ser um número positivo'),
  
  tratarErrosValidacao
];

const validarAgendamentoAtualizacao = [
  param('id')
    .trim()
    .notEmpty().withMessage('ID é obrigatório'),
  
  body('clienteId')
    .optional()
    .trim()
    .notEmpty().withMessage('Cliente é obrigatório'),
  
  body('servico')
    .optional()
    .trim()
    .isIn(['manicure', 'cilios', 'combo']).withMessage('Serviço inválido'),
  
  body('data')
    .optional()
    .trim()
    .matches(/^\d{4}-\d{2}-\d{2}$/).withMessage('Data deve estar no formato YYYY-MM-DD'),
    
  body('horario')
    .optional()
    .trim()
    .matches(/^\d{2}:\d{2}$/).withMessage('Horário deve estar no formato HH:MM'),
  
  body('status')
    .optional()
    .isIn(['pendente', 'confirmada', 'nao_vai', 'realizada']).withMessage('Status inválido'),
  
  body('obs')
    .optional()
    .trim()
    .isLength({ max: 500 }).withMessage('Observações não pode ter mais de 500 caracteres'),
  
  body('preco')
    .optional()
    .isFloat({ min: 0 }).withMessage('Preço deve ser um número positivo'),
  
  tratarErrosValidacao
];

// ============================================
// VALIDADORES DE CONFIGURAÇÕES
// ============================================

const validarConfiguracao = [
  param('chave')
    .trim()
    .isIn(['precoManicure', 'precoCilios', 'precoCombo', 'horaAbertura', 'horaFechamento', 'intervaloMin'])
    .withMessage('Configuração inválida'),
  
  body('valor')
    .notEmpty().withMessage('Valor é obrigatório'),
  
  tratarErrosValidacao
];

// ============================================
// VALIDADORES DE AUTENTICAÇÃO
// ============================================

const validarLogin = [
  body('email')
    .trim()
    .isEmail().withMessage('Email inválido'),
  
  body('senha')
    .notEmpty().withMessage('Senha é obrigatória')
    .isLength({ min: 6 }).withMessage('Senha deve ter no mínimo 6 caracteres'),
  
  tratarErrosValidacao
];

const validarRegistro = [
  body('email')
    .trim()
    .isEmail().withMessage('Email inválido'),
  
  body('senha')
    .notEmpty().withMessage('Senha é obrigatória')
    .isLength({ min: 8 }).withMessage('Senha deve ter no mínimo 8 caracteres')
    .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .withMessage('Senha deve conter maiúscula, minúscula e número'),
  
  body('nome')
    .trim()
    .notEmpty().withMessage('Nome é obrigatório')
    .isLength({ min: 2, max: 100 }).withMessage('Nome deve ter entre 2 e 100 caracteres'),
  
  tratarErrosValidacao
];

// ============================================
// VALIDADORES DE QUERY PARAMETERS
// ============================================

const validarPaginacao = [
  query('limit')
    .optional()
    .isInt({ min: 1, max: 1000 }).withMessage('Limit deve estar entre 1 e 1000'),
  
  query('offset')
    .optional()
    .isInt({ min: 0 }).withMessage('Offset deve ser 0 ou maior'),
  
  tratarErrosValidacao
];

const validarFiltrosAgendamentos = [
  query('data')
    .optional()
    .matches(/^\d{4}-\d{2}-\d{2}$/).withMessage('Data deve estar no formato YYYY-MM-DD'),
  
  query('status')
    .optional()
    .isIn(['pendente', 'confirmada', 'nao_vai', 'realizada']).withMessage('Status inválido'),
  
  tratarErrosValidacao
];

// ============================================
// EXPORTS
// ============================================

module.exports = {
  // Clientes
  validarClienteNovo,
  validarClienteAtualizacao,
  
  // Agendamentos
  validarAgendamentoNovo,
  validarAgendamentoAtualizacao,
  
  // Configurações
  validarConfiguracao,
  
  // Autenticação
  validarLogin,
  validarRegistro,
  
  // Query
  validarPaginacao,
  validarFiltrosAgendamentos,
  
  // Middleware principal
  tratarErrosValidacao
};
