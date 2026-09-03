// ============================================
// JEST.CONFIG.JS — Configuração de Testes
// ============================================

module.exports = {
  // Ambiente de teste
  testEnvironment: 'node',

  // Padrão de arquivos de teste
  testMatch: ['**/tests/**/*.test.js'],

  // Timeout padrão
  testTimeout: 10000,

  // Coletar cobertura
  collectCoverageFrom: [
    'middleware/**/*.js',
    'utils/**/*.js',
    'routes/**/*.js',
    '!node_modules/**',
    '!tests/**'
  ],

  // Limite de cobertura
  coverageThreshold: {
    global: {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50
    }
  },

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],

  // Transform
  transform: {
    '^.+\\.jsx?$': 'babel-jest'
  },

  // Verbose
  verbose: true
};
