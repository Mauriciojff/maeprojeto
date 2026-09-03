// ============================================
// API-CLIENT.JS — Cliente HTTP para a API
// ============================================

const API_URL = 'http://localhost:3000/api';

class APIClient {
  // ===== CLIENTES =====
  
  static async obterClientes() {
    return this._fetch('GET', '/clientes');
  }

  static async obterCliente(id) {
    return this._fetch('GET', `/clientes/${id}`);
  }

  static async criarCliente(data) {
    return this._fetch('POST', '/clientes', data);
  }

  static async atualizarCliente(id, data) {
    return this._fetch('PUT', `/clientes/${id}`, data);
  }

  static async excluirCliente(id) {
    return this._fetch('DELETE', `/clientes/${id}`);
  }

  // ===== AGENDAMENTOS =====

  static async obterAgendamentos(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this._fetch('GET', `/agendamentos${query ? '?' + query : ''}`);
  }

  static async obterAgendamentosDia(data) {
    return this._fetch('GET', `/agendamentos/data/${data}`);
  }

  static async obterAgendamento(id) {
    return this._fetch('GET', `/agendamentos/${id}`);
  }

  static async criarAgendamento(data) {
    return this._fetch('POST', '/agendamentos', data);
  }

  static async atualizarAgendamento(id, data) {
    return this._fetch('PUT', `/agendamentos/${id}`, data);
  }

  static async excluirAgendamento(id) {
    return this._fetch('DELETE', `/agendamentos/${id}`);
  }

  // ===== FATURAMENTO =====

  static async obterFaturamento(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this._fetch('GET', `/faturamento${query ? '?' + query : ''}`);
  }

  static async obterResumoFaturamento() {
    return this._fetch('GET', '/faturamento/resumo');
  }

  // ===== CONFIGURAÇÕES =====

  static async obterConfiguracoes() {
    return this._fetch('GET', '/configuracoes');
  }

  static async atualizarConfiguracao(chave, valor) {
    return this._fetch('PUT', `/configuracoes/${chave}`, { valor });
  }

  // ===== WHATSAPP =====

  static async registrarLogWhatsApp(data) {
    return this._fetch('POST', '/whatsapp/log', data);
  }

  static async obterLogsWhatsApp() {
    return this._fetch('GET', '/whatsapp/logs');
  }

  // ===== DADOS =====

  static async exportarDados() {
    return this._fetch('GET', '/export');
  }

  static async importarDados(dados) {
    return this._fetch('POST', '/import', dados);
  }

  // ===== HELPER =====

  static async _fetch(method, endpoint, data = null) {
    try {
      const options = {
        method,
        headers: {
          'Content-Type': 'application/json'
        }
      };

      if (data) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(`${API_URL}${endpoint}`, options);

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.erro || `Erro ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.error(`API Error [${method} ${endpoint}]:`, err);
      throw err;
    }
  }
}

// ============================================
// MODO OFFLINE - Fallback para LocalStorage
// ============================================

class OfflineStorage {
  static KEY = 'agendaMae';

  static async obterClientes() {
    return this._getState().clientes || [];
  }

  static async criarCliente(data) {
    const state = this._getState();
    const cliente = { id: this._gerarId(), ...data, dataCadastro: new Date().toISOString() };
    state.clientes.push(cliente);
    this._setState(state);
    return cliente;
  }

  static async obterAgendamentos() {
    return this._getState().agendamentos || [];
  }

  static async criarAgendamento(data) {
    const state = this._getState();
    const agendamento = { id: this._gerarId(), ...data, dataCriacao: new Date().toISOString() };
    state.agendamentos.push(agendamento);
    this._setState(state);
    return agendamento;
  }

  static async atualizarAgendamento(id, data) {
    const state = this._getState();
    const idx = state.agendamentos.findIndex(a => a.id === id);
    if (idx !== -1) {
      state.agendamentos[idx] = { ...state.agendamentos[idx], ...data };
      this._setState(state);
    }
  }

  static async obterResumoFaturamento() {
    // Cálculo simulado
    return { hoje: 0, semana: 0, mes: 0, total: 0 };
  }

  static _getState() {
    const saved = localStorage.getItem(this.KEY);
    return saved ? JSON.parse(saved) : { clientes: [], agendamentos: [] };
  }

  static _setState(state) {
    localStorage.setItem(this.KEY, JSON.stringify(state));
  }

  static _gerarId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
  }
}

// ============================================
// SELETOR AUTOMÁTICO - API ou Offline
// ============================================

let useAPI = false;

async function initializeAPI() {
  try {
    // Tentar conectar à API
    await fetch('http://localhost:3000/api/clientes');
    useAPI = true;
    console.log('✅ Usando API do servidor');
    return true;
  } catch (err) {
    useAPI = false;
    console.log('⚠️ API não disponível - usando modo offline');
    return false;
  }
}

function getDataSource() {
  return useAPI ? APIClient : OfflineStorage;
}
