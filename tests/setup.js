// ============================================
// TESTS/SETUP.JS — Setup dos Testes
// ============================================

// Configurar variáveis de ambiente para testes
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret-key';
process.env.LOG_LEVEL = 'error'; // Não logar durante testes

// Aumentar timeout padrão
jest.setTimeout(10000);

// Mock de módulos se necessário
jest.mock('../utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  debug: jest.fn(),
  auditoria: jest.fn(),
  performance: jest.fn(),
  seguranca: jest.fn(),
  whatsapp: jest.fn(),
  database: jest.fn(),
  loggerHTTP: jest.fn((req, res, next) => next())
}));

// Após todos os testes, fechar conexões
afterAll(async () => {
  // Fechar banco de dados
  // await db.close();
  
  // Dar tempo para limpeza
  await new Promise(resolve => setTimeout(resolve, 100));
});
