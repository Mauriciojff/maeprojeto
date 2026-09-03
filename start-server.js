// ============================================
// START-SERVER.JS — Inicializador do Servidor
// ============================================

require('dotenv').config();
const express = require('express');
const path = require('path');
const fs = require('fs');

// Importar componentes
const apiRoutes = require('./routes/api');
const authRoutes = require('./routes/auth');
const { initWhatsApp } = require('./whatsapp-service');

// Importar middleware de segurança e logging
const { helmetConfig, limitadorGeral, sanitizarInputs, registrarAcessos, preventivosSeguranca } = require('./middleware/security');
const logger = require('./utils/logger');
const { errorHandler } = require('./utils/errors');

// Importar body-parser e CORS
const cors = require('cors');
const compression = require('compression');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 3000;
const ENABLE_WHATSAPP = process.env.WHATSAPP_ENABLED !== 'false';

// ============================================
// MIDDLEWARE - ORDEM CRÍTICA
// ============================================

// 1. Headers de segurança (helmet)
app.use(helmetConfig);

// 2. Compressão de respostas
app.use(compression());

// 3. CORS
app.use(cors({
  origin: [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://127.0.0.1:3000',
    process.env.FRONTEND_URL || 'http://localhost:3000'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// 4. Body parser
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ limit: '50mb', extended: true }));

// 5. Logging HTTP
app.use(logger.loggerHTTP);

// 6. Sanitização de inputs
app.use(sanitizarInputs);

// 7. Rate limiting geral
app.use(limitadorGeral);

// 8. Preventivos de segurança
app.use(preventivosSeguranca);

// 9. Registro de acessos
app.use(registrarAcessos);

// 10. Arquivos estáticos
app.use(express.static(path.join(__dirname)));

// ============================================
// CRIAR PASTA DATA
// ============================================

const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

// ============================================
// ROTAS
// ============================================

// Autenticação (pública)
app.use('/api/auth', authRoutes);

// Demais APIs (protegidas)
app.use('/api', apiRoutes);

// Servir index.html na raiz
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    whatsappEnabled: ENABLE_WHATSAPP,
    ambiente: process.env.NODE_ENV || 'development'
  });
});

// ============================================
// ERROR HANDLER (deve ser último middleware)
// ============================================

app.use(errorHandler);

// ============================================
// INICIAR SERVIDOR
// ============================================

const server = app.listen(PORT, () => {
  console.log('\n');
  console.log('╔════════════════════════════════════════╗');
  console.log('║     💅 AGENDA DA MÃE - v2.0.0         ║');
  console.log('║   Com Segurança, Logging e Testes     ║');
  console.log('╚════════════════════════════════════════╝');
  console.log(`\n🚀 Servidor rodando em http://localhost:${PORT}`);
  console.log(`📱 Abra no navegador: http://localhost:${PORT}`);
  console.log(`💾 Banco de dados: ${path.join(dataDir, 'agenda.db')}`);
  console.log(`📊 Logs: ./logs/ (error.log, combined.log, http.log)\n`);

  // Inicializar WhatsApp (se habilitado)
  if (ENABLE_WHATSAPP) {
    console.log('📱 Iniciando WhatsApp Web...');
    console.log('   Escaneie o QR Code com seu celular\n');
    
    try {
      initWhatsApp();
    } catch (err) {
      logger.warn('WhatsApp não disponível:', { erro: err.message });
    }
  } else {
    console.log('⚠️  WhatsApp desabilitado\n');
  }

  console.log('═════════════════════════════════════════');
  console.log('✅ Sistema pronto para uso!');
  console.log('═════════════════════════════════════════');
  console.log('\n🔐 Teste o login:');
  console.log('   Email: admin@agenda.com');
  console.log('   Senha: Senha123456\n');
  
  logger.info('Servidor iniciado', {
    porta: PORT,
    ambiente: process.env.NODE_ENV || 'development',
    whatsapp: ENABLE_WHATSAPP
  });
});

// ============================================
// TRATAMENTO DE ERROS E SINAIS
// ============================================

process.on('unhandledRejection', (err) => {
  logger.error('Rejeição não capturada:', err);
});

process.on('uncaughtException', (err) => {
  logger.error('Exceção não capturada:', err);
  setTimeout(() => process.exit(1), 1000);
});

process.on('SIGINT', () => {
  console.log('\n\n🛑 Encerrando servidor...');
  logger.info('Encerrando processo via SIGINT');
  
  server.close(() => {
    console.log('✅ Servidor encerrado');
    logger.info('Servidor encerrado com sucesso');
    process.exit(0);
  });
});

module.exports = app;
