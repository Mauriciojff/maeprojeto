// ============================================
// TESTS/API.TEST.JS — Testes da API
// ============================================

const request = require('supertest');
const { inicializarTabelaUsuarios } = require('../middleware/auth');

// Mock do app (ajustar conforme necessário)
// const app = require('../start-server');

describe('API - Testes Completos', () => {
  let token;
  let clienteId;
  let agendamentoId;

  // ============================================
  // AUTENTICAÇÃO
  // ============================================

  describe('Autenticação', () => {
    test('Deve fazer login com credenciais válidas', async () => {
      const res = await request('http://localhost:3000')
        .post('/api/auth/login')
        .send({
          email: 'admin@agenda.com',
          senha: 'Senha123456'
        });

      expect(res.statusCode).toBe(200);
      expect(res.body).toHaveProperty('token');
      expect(res.body).toHaveProperty('refreshToken');
      
      token = res.body.token;
    });

    test('Deve falhar login com email inválido', async () => {
      const res = await request('http://localhost:3000')
        .post('/api/auth/login')
        .send({
          email: 'invalido@email.com',
          senha: 'qualquersenha'
        });

      expect(res.statusCode).toBe(401);
      expect(res.body.codigo).toBe('CREDENCIAIS_INVALIDAS');
    });

    test('Deve falhar login com senha incorreta', async () => {
      const res = await request('http://localhost:3000')
        .post('/api/auth/login')
        .send({
          email: 'admin@agenda.com',
          senha: 'senhaerrada'
        });

      expect(res.statusCode).toBe(401);
      expect(res.body.codigo).toBe('CREDENCIAIS_INVALIDAS');
    });

    test('Deve retornar perfil do usuário autenticado', async () => {
      const res = await request('http://localhost:3000')
        .get('/api/auth/me')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body).toHaveProperty('email');
      expect(res.body).toHaveProperty('nome');
    });

    test('Deve falhar sem token de autenticação', async () => {
      const res = await request('http://localhost:3000')
        .get('/api/auth/me');

      expect(res.statusCode).toBe(401);
      expect(res.body.codigo).toBe('TOKEN_NAO_FORNECIDO');
    });
  });

  // ============================================
  // CLIENTES
  // ============================================

  describe('Clientes', () => {
    test('Deve criar um novo cliente', async () => {
      const res = await request('http://localhost:3000')
        .post('/api/clientes')
        .set('Authorization', `Bearer ${token}`)
        .send({
          nome: 'Maria Silva',
          telefone: '11999999999',
          email: 'maria@email.com'
        });

      expect(res.statusCode).toBe(200);
      expect(res.body).toHaveProperty('id');
      expect(res.body.nome).toBe('Maria Silva');
      
      clienteId = res.body.id;
    });

    test('Deve validar nome obrigatório', async () => {
      const res = await request('http://localhost:3000')
        .post('/api/clientes')
        .set('Authorization', `Bearer ${token}`)
        .send({
          telefone: '11999999999'
        });

      expect(res.statusCode).toBe(400);
      expect(res.body.codigo).toBe('VALIDACAO_FALHOU');
    });

    test('Deve listar clientes', async () => {
      const res = await request('http://localhost:3000')
        .get('/api/clientes')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(Array.isArray(res.body)).toBe(true);
    });

    test('Deve obter cliente específico', async () => {
      const res = await request('http://localhost:3000')
        .get(`/api/clientes/${clienteId}`)
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body.id).toBe(clienteId);
    });

    test('Deve atualizar cliente', async () => {
      const res = await request('http://localhost:3000')
        .put(`/api/clientes/${clienteId}`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          nome: 'Maria Silva Atualizado',
          telefone: '11988888888'
        });

      expect(res.statusCode).toBe(200);
      expect(res.body.mensagem).toContain('atualizado');
    });
  });

  // ============================================
  // AGENDAMENTOS
  // ============================================

  describe('Agendamentos', () => {
    test('Deve criar um novo agendamento', async () => {
      const hoje = new Date().toISOString().split('T')[0];
      
      const res = await request('http://localhost:3000')
        .post('/api/agendamentos')
        .set('Authorization', `Bearer ${token}`)
        .send({
          clienteId,
          servico: 'manicure',
          data: hoje,
          horario: '14:00',
          status: 'confirmada',
          preco: 40.00
        });

      expect(res.statusCode).toBe(200);
      expect(res.body).toHaveProperty('id');
      
      agendamentoId = res.body.id;
    });

    test('Deve validar serviço obrigatório', async () => {
      const hoje = new Date().toISOString().split('T')[0];
      
      const res = await request('http://localhost:3000')
        .post('/api/agendamentos')
        .set('Authorization', `Bearer ${token}`)
        .send({
          clienteId,
          data: hoje,
          horario: '14:00'
        });

      expect(res.statusCode).toBe(400);
    });

    test('Deve validar formato de data', async () => {
      const res = await request('http://localhost:3000')
        .post('/api/agendamentos')
        .set('Authorization', `Bearer ${token}`)
        .send({
          clienteId,
          servico: 'manicure',
          data: 'data-invalida',
          horario: '14:00'
        });

      expect(res.statusCode).toBe(400);
      expect(res.body.codigo).toBe('VALIDACAO_FALHOU');
    });

    test('Deve listar agendamentos', async () => {
      const res = await request('http://localhost:3000')
        .get('/api/agendamentos')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(Array.isArray(res.body)).toBe(true);
    });

    test('Deve obter agendamento específico', async () => {
      const res = await request('http://localhost:3000')
        .get(`/api/agendamentos/${agendamentoId}`)
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body.id).toBe(agendamentoId);
    });

    test('Deve atualizar status de agendamento', async () => {
      const res = await request('http://localhost:3000')
        .put(`/api/agendamentos/${agendamentoId}`)
        .set('Authorization', `Bearer ${token}`)
        .send({
          status: 'realizada'
        });

      expect(res.statusCode).toBe(200);
    });
  });

  // ============================================
  // FATURAMENTO
  // ============================================

  describe('Faturamento', () => {
    test('Deve obter resumo de faturamento', async () => {
      const res = await request('http://localhost:3000')
        .get('/api/faturamento/resumo')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body).toHaveProperty('hoje');
      expect(res.body).toHaveProperty('semana');
      expect(res.body).toHaveProperty('mes');
      expect(res.body).toHaveProperty('total');
    });

    test('Deve listar faturamentos', async () => {
      const res = await request('http://localhost:3000')
        .get('/api/faturamento')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(Array.isArray(res.body)).toBe(true);
    });
  });

  // ============================================
  // CONFIGURAÇÕES
  // ============================================

  describe('Configurações', () => {
    test('Deve obter configurações', async () => {
      const res = await request('http://localhost:3000')
        .get('/api/configuracoes')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toBe(200);
      expect(res.body).toHaveProperty('precoManicure');
      expect(res.body).toHaveProperty('precoCilios');
    });

    test('Deve atualizar configuração', async () => {
      const res = await request('http://localhost:3000')
        .put('/api/configuracoes/precoManicure')
        .set('Authorization', `Bearer ${token}`)
        .send({
          valor: '50.00'
        });

      expect(res.statusCode).toBe(200);
    });
  });

  // ============================================
  // SEGURANÇA
  // ============================================

  describe('Segurança', () => {
    test('Deve rejeitar requisições sem token', async () => {
      const res = await request('http://localhost:3000')
        .get('/api/clientes');

      expect(res.statusCode).toBe(401);
    });

    test('Deve rejeitar token inválido', async () => {
      const res = await request('http://localhost:3000')
        .get('/api/clientes')
        .set('Authorization', 'Bearer token_invalido');

      expect(res.statusCode).toBe(401);
    });

    test('Deve validar campos obrigatórios', async () => {
      const res = await request('http://localhost:3000')
        .post('/api/clientes')
        .set('Authorization', `Bearer ${token}`)
        .send({});

      expect(res.statusCode).toBe(400);
    });
  });

  // ============================================
  // LIMPEZA
  // ============================================

  afterAll(async () => {
    // Limpar dados de teste se necessário
    if (agendamentoId) {
      await request('http://localhost:3000')
        .delete(`/api/agendamentos/${agendamentoId}`)
        .set('Authorization', `Bearer ${token}`);
    }
    
    if (clienteId) {
      await request('http://localhost:3000')
        .delete(`/api/clientes/${clienteId}`)
        .set('Authorization', `Bearer ${token}`);
    }
  });
});
