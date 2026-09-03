// ============================================
// ROUTES/AUTH.JS — Rotas de Autenticação
// ============================================

const express = require('express');
const router = express.Router();
const { verificarToken, verificarAdmin, login, refresh, criarUsuario, obterMeuPerfil } = require('../middleware/auth');
const { validarLogin, validarRegistro } = require('../middleware/validators');
const { asyncHandler } = require('../utils/errors');
const { limitadorLogin } = require('../middleware/security');
const logger = require('../utils/logger');

// ============================================
// ROTAS PÚBLICAS (sem autenticação)
// ============================================

// POST /api/auth/login
router.post('/login', limitadorLogin, validarLogin, asyncHandler(async (req, res) => {
  await login(req, res);
}));

// POST /api/auth/refresh
router.post('/refresh', asyncHandler(async (req, res) => {
  await refresh(req, res);
}));

// ============================================
// ROTAS PROTEGIDAS (requer autenticação)
// ============================================

// GET /api/auth/me
router.get('/me', verificarToken, asyncHandler(async (req, res) => {
  await obterMeuPerfil(req, res);
}));

// POST /api/auth/logout (simples)
router.post('/logout', verificarToken, (req, res) => {
  // Em um caso real, você poderia guardar tokens em uma blacklist
  logger.info('Logout bem-sucedido:', { usuario: req.usuario.email });
  
  res.json({
    mensagem: 'Logout realizado com sucesso'
  });
});

// ============================================
// ROTAS DE ADMIN
// ============================================

// POST /api/auth/usuarios (criar novo usuário - admin only)
router.post('/usuarios', verificarToken, verificarAdmin, validarRegistro, asyncHandler(async (req, res) => {
  await criarUsuario(req, res);
}));

// ============================================
// EXPORTS
// ============================================

module.exports = router;
