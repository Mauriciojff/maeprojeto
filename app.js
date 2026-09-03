// ============================================
// AGENDA DA MÃE — Manicure & Cílios
// App de agendamento com faturamento e WhatsApp
// ============================================

// ---------- CONSTANTES ----------
const STORAGE_KEY = 'agendaMae';
const DIAS_SEMANA = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];
const DIAS_SEMANA_ABREV = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
const MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];

const SERVICOS = {
  manicure: { nome: 'Manicure', icone: '💅' },
  cilios: { nome: 'Cílios', icone: '👁️' },
  combo: { nome: 'Manicure + Cílios', icone: '✨' }
};

const STATUS = {
  pendente: { nome: 'Pendente', icone: '⏳' },
  confirmada: { nome: 'Confirmada', icone: '✅' },
  nao_vai: { nome: 'Não vai', icone: '❌' },
  realizada: { nome: 'Realizada', icone: '💯' }
};

// ---------- ESTADO ----------
let state = {
  clientes: [],
  agendamentos: [],
  config: {
    precos: { manicure: 40, cilios: 80, combo: 110 },
    horaAbertura: '08:00',
    horaFechamento: '20:00',
    intervaloMin: 60
  }
};

let semanaAtual = new Date();
let agendamentoEditando = null;
let whatsappAgendamento = null;
let whatsappCliente = null;

// ---------- UTILITÁRIOS ----------
function formatarMoeda(valor) {
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatarData(data) {
  const d = new Date(data);
  return d.toLocaleDateString('pt-BR');
}

function formatarDataISO(data) {
  const d = new Date(data);
  const ano = d.getFullYear();
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  return `${ano}-${mes}-${dia}`;
}

function hojeISO() {
  return formatarDataISO(new Date());
}

function dataISOtoDate(iso) {
  const [ano, mes, dia] = iso.split('-').map(Number);
  return new Date(ano, mes - 1, dia);
}

function addDias(data, dias) {
  const d = new Date(data);
  d.setDate(d.getDate() + dias);
  return d;
}

function inicioDaSemana(data) {
  const d = new Date(data);
  const dia = d.getDay();
  const diff = d.getDate() - dia + (dia === 0 ? -6 : 1); // Segunda como início
  return new Date(d.setDate(diff));
}

function gerarHorarios() {
  const { horaAbertura, horaFechamento, intervaloMin } = state.config;
  const [hA, mA] = horaAbertura.split(':').map(Number);
  const [hF, mF] = horaFechamento.split(':').map(Number);
  const horarios = [];
  let hora = hA * 60 + mA;
  const fim = hF * 60 + mF;
  while (hora < fim) {
    const h = Math.floor(hora / 60);
    const m = hora % 60;
    horarios.push(`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`);
    hora += intervaloMin;
  }
  return horarios;
}

function gerarId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
}

function limparTelefone(tel) {
  return tel.replace(/\D/g, '');
}

// ---------- PERSISTÊNCIA ----------
function salvarState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function carregarState() {
  const salvo = localStorage.getItem(STORAGE_KEY);
  if (salvo) {
    try {
      state = JSON.parse(salvo);
      // Garantir estrutura completa
      if (!state.config) state.config = { precos: {}, horaAbertura: '08:00', horaFechamento: '20:00', intervaloMin: 60 };
      if (!state.config.precos) state.config.precos = { manicure: 40, cilios: 80, combo: 110 };
      if (!state.clientes) state.clientes = [];
      if (!state.agendamentos) state.agendamentos = [];
    } catch (e) {
      console.error('Erro ao carregar dados:', e);
    }
  }
}

// ---------- CLIENTES ----------
function getCliente(id) {
  return state.clientes.find(c => c.id === id);
}

function getClienteNome(id) {
  const c = getCliente(id);
  return c ? c.nome : 'Cliente removida';
}

function getClienteTelefone(id) {
  const c = getCliente(id);
  return c ? c.telefone : '';
}

// ---------- AGENDAMENTOS ----------
function getAgendamentosDoDia(iso) {
  return state.agendamentos.filter(a => a.data === iso);
}

function getAgendamentoPorHorario(iso, horario) {
  return state.agendamentos.find(a => a.data === iso && a.horario === horario);
}

function getPrecoServico(servico) {
  return state.config.precos[servico] || 0;
}

// ---------- RENDER: AGENDA ----------
function renderAgenda() {
  const inicio = inicioDaSemana(semanaAtual);
  const dias = [];
  for (let i = 0; i < 7; i++) {
    dias.push(addDias(inicio, i));
  }

  // Headers
  const dayHeaders = document.getElementById('dayHeaders');
  dayHeaders.innerHTML = '';
  dias.forEach(d => {
    const iso = formatarDataISO(d);
    const hoje = iso === hojeISO();
    const div = document.createElement('div');
    div.className = 'day-header' + (hoje ? ' today' : '');
    div.innerHTML = `
      <div class="day-name">${DIAS_SEMANA_ABREV[d.getDay()]}</div>
      <div class="day-date">${d.getDate()}/${d.getMonth() + 1}</div>
    `;
    dayHeaders.appendChild(div);
  });

  // Range label
  const primeiro = dias[0];
  const ultimo = dias[6];
  const mesmoMes = primeiro.getMonth() === ultimo.getMonth();
  const label = mesmoMes
    ? `${primeiro.getDate()} a ${ultimo.getDate()} de ${MESES[ultimo.getMonth()]}`
    : `${primeiro.getDate()} ${MESES[primeiro.getMonth()].substring(0, 3)} a ${ultimo.getDate()} ${MESES[ultimo.getMonth()]}`;
  document.getElementById('dateRange').textContent = label;

  // Corpo
  const body = document.getElementById('agendaBody');
  body.innerHTML = '';
  const horarios = gerarHorarios();

  horarios.forEach(horario => {
    const row = document.createElement('div');
    row.className = 'agenda-row';

    const timeLabel = document.createElement('div');
    timeLabel.className = 'time-label';
    timeLabel.textContent = horario;
    row.appendChild(timeLabel);

    const daySlots = document.createElement('div');
    daySlots.className = 'day-slots';

    dias.forEach(d => {
      const iso = formatarDataISO(d);
      const slot = document.createElement('div');
      slot.className = 'slot';

      const agendamento = getAgendamentoPorHorario(iso, horario);
      if (agendamento) {
        const card = document.createElement('button');
        card.className = `appointment-card status-${agendamento.status}`;
        card.innerHTML = `
          <span class="app-client">${getClienteNome(agendamento.clienteId)}</span>
          <span class="app-service">${SERVICOS[agendamento.servico].icone} ${SERVICOS[agendamento.servico].nome}</span>
          <span class="app-status">${STATUS[agendamento.status].icone} ${STATUS[agendamento.status].nome}</span>
        `;
        card.addEventListener('click', () => abrirModalAgendamento(agendamento));
        slot.appendChild(card);
      } else {
        slot.className += ' empty';
        slot.title = `Agendar ${horario} em ${formatarData(iso)}`;
        slot.addEventListener('click', () => abrirModalAgendamento(null, iso, horario));
      }

      daySlots.appendChild(slot);
    });

    row.appendChild(daySlots);
    body.appendChild(row);
  });
}

// ---------- RENDER: FATURAMENTO ----------
function calcularFaturamento() {
  const hoje = hojeISO();
  const agora = new Date();
  const inicioSemana = inicioDaSemana(agora);
  const fimSemana = addDias(inicioSemana, 6);
  const inicioMes = new Date(agora.getFullYear(), agora.getMonth(), 1);
  const fimMes = new Date(agora.getFullYear(), agora.getMonth() + 1, 0);

  let fatHoje = 0, countHoje = 0;
  let fatSemana = 0, countSemana = 0;
  let fatMes = 0, countMes = 0;
  let fatTotal = 0, countTotal = 0;

  const porServico = { manicure: 0, cilios: 0, combo: 0 };
  const porDia = {};

  state.agendamentos.forEach(a => {
    if (a.status !== 'realizada') return;
    const preco = getPrecoServico(a.servico);
    const data = dataISOtoDate(a.data);

    fatTotal += preco;
    countTotal++;
    porServico[a.servico] = (porServico[a.servico] || 0) + preco;

    if (!porDia[a.data]) porDia[a.data] = 0;
    porDia[a.data] += preco;

    if (a.data === hoje) {
      fatHoje += preco;
      countHoje++;
    }

    if (data >= inicioSemana && data <= fimSemana) {
      fatSemana += preco;
      countSemana++;
    }

    if (data >= inicioMes && data <= fimMes) {
      fatMes += preco;
      countMes++;
    }
  });

  return { fatHoje, countHoje, fatSemana, countSemana, fatMes, countMes, fatTotal, countTotal, porServico, porDia };
}

function renderFaturamento() {
  const f = calcularFaturamento();

  document.getElementById('fatHoje').textContent = formatarMoeda(f.fatHoje);
  document.getElementById('fatHojeCount').textContent = `${f.countHoje} agendamento(s)`;
  document.getElementById('fatSemana').textContent = formatarMoeda(f.fatSemana);
  document.getElementById('fatSemanaCount').textContent = `${f.countSemana} agendamento(s)`;
  document.getElementById('fatMes').textContent = formatarMoeda(f.fatMes);
  document.getElementById('fatMesCount').textContent = `${f.countMes} agendamento(s)`;
  document.getElementById('fatTotal').textContent = formatarMoeda(f.fatTotal);
  document.getElementById('fatTotalCount').textContent = `${f.countTotal} agendamento(s)`;

  // Por serviço
  const porServicoEl = document.getElementById('fatPorServico');
  porServicoEl.innerHTML = '';
  const maxServico = Math.max(...Object.values(f.porServico), 1);
  Object.entries(SERVICOS).forEach(([key, serv]) => {
    const valor = f.porServico[key] || 0;
    const pct = (valor / maxServico) * 100;
    const row = document.createElement('div');
    row.className = 'fat-bar';
    row.innerHTML = `
      <div class="fat-bar-label">${serv.icone} ${serv.nome}</div>
      <div class="fat-bar-track"><div class="fat-bar-fill" style="width: ${pct}%"></div></div>
      <div class="fat-bar-value">${formatarMoeda(valor)}</div>
    `;
    porServicoEl.appendChild(row);
  });

  // Por dia (últimos 14 dias)
  const porDiaEl = document.getElementById('fatPorDia');
  porDiaEl.innerHTML = '';
  const dias = [];
  for (let i = 13; i >= 0; i--) {
    dias.push(addDias(new Date(), -i));
  }
  const maxDia = Math.max(...dias.map(d => f.porDia[formatarDataISO(d)] || 0), 1);
  dias.forEach(d => {
    const iso = formatarDataISO(d);
    const valor = f.porDia[iso] || 0;
    const pct = (valor / maxDia) * 100;
    const row = document.createElement('div');
    row.className = 'fat-day-row';
    row.innerHTML = `
      <div class="fat-day-label">${DIAS_SEMANA_ABREV[d.getDay()]} ${d.getDate()}/${d.getMonth() + 1}</div>
      <div class="fat-day-bar"><div class="fat-day-fill" style="width: ${pct}%"></div></div>
      <div class="fat-day-value">${formatarMoeda(valor)}</div>
    `;
    porDiaEl.appendChild(row);
  });
}

// ---------- RENDER: CLIENTES ----------
function renderClientes() {
  const busca = document.getElementById('buscaCliente').value.toLowerCase();
  const lista = document.getElementById('listaClientes');
  lista.innerHTML = '';

  const filtrados = state.clientes.filter(c =>
    c.nome.toLowerCase().includes(busca) ||
    (c.telefone || '').includes(busca)
  );

  if (filtrados.length === 0) {
    lista.innerHTML = '<p class="hint">Nenhuma cliente encontrada.</p>';
    return;
  }

  filtrados.forEach(c => {
    const item = document.createElement('div');
    item.className = 'cliente-item';
    item.innerHTML = `
      <div class="cliente-info">
        <div class="cliente-nome">${c.nome}</div>
        <div class="cliente-telefone">📱 ${c.telefone || 'Sem telefone'}</div>
      </div>
      <div class="cliente-actions">
        <button class="btn btn-outline btn-sm" data-whatsapp="${c.id}">📱 WhatsApp</button>
        <button class="btn btn-danger btn-sm" data-excluir="${c.id}">🗑️</button>
      </div>
    `;
    item.querySelector('[data-whatsapp]').addEventListener('click', () => abrirWhatsAppCliente(c));
    item.querySelector('[data-excluir]').addEventListener('click', () => excluirCliente(c.id));
    lista.appendChild(item);
  });
}

// ---------- RENDER: CONFIG ----------
function renderConfig() {
  document.getElementById('precoManicure').value = state.config.precos.manicure;
  document.getElementById('precoCilios').value = state.config.precos.cilios;
  document.getElementById('precoCombo').value = state.config.precos.combo;
  document.getElementById('horaAbertura').value = state.config.horaAbertura;
  document.getElementById('horaFechamento').value = state.config.horaFechamento;
  document.getElementById('intervaloMin').value = state.config.intervaloMin;
}

// ---------- MODAIS ----------
function abrirModal(modalId) {
  document.getElementById(modalId).classList.add('active');
}

function fecharModal(modalId) {
  document.getElementById(modalId).classList.remove('active');
}

function abrirModalAgendamento(agendamento, data, horario) {
  agendamentoEditando = agendamento || null;
  const modal = document.getElementById('modalAgendamento');
  document.getElementById('modalAgendamentoTitle').textContent = agendamento ? 'Editar Agendamento' : 'Novo Agendamento';
  document.getElementById('agendamentoId').value = agendamento ? agendamento.id : '';

  // Mostrar/esconder botões de edição
  document.getElementById('btnWhatsAppAgendamento').style.display = agendamento ? 'inline-block' : 'none';
  document.getElementById('btnExcluirAgendamento').style.display = agendamento ? 'inline-block' : 'none';

  // Clientes
  const selectCliente = document.getElementById('agendamentoCliente');
  selectCliente.innerHTML = '';
  state.clientes.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.id;
    opt.textContent = c.nome;
    selectCliente.appendChild(opt);
  });
  if (state.clientes.length === 0) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = '— Cadastre uma cliente primeiro —';
    selectCliente.appendChild(opt);
  }

  // Horários
  const selectHorario = document.getElementById('agendamentoHorario');
  selectHorario.innerHTML = '';
  const horarios = gerarHorarios();
  horarios.forEach(h => {
    const opt = document.createElement('option');
    opt.value = h;
    opt.textContent = h;
    selectHorario.appendChild(opt);
  });

  if (agendamento) {
    document.getElementById('agendamentoCliente').value = agendamento.clienteId;
    document.getElementById('agendamentoServico').value = agendamento.servico;
    document.getElementById('agendamentoData').value = agendamento.data;
    document.getElementById('agendamentoHorario').value = agendamento.horario;
    document.getElementById('agendamentoStatus').value = agendamento.status;
    document.getElementById('agendamentoObs').value = agendamento.obs || '';
  } else {
    document.getElementById('agendamentoCliente').value = state.clientes.length > 0 ? state.clientes[0].id : '';
    document.getElementById('agendamentoServico').value = 'manicure';
    document.getElementById('agendamentoData').value = data || hojeISO();
    document.getElementById('agendamentoHorario').value = horario || horarios[0];
    document.getElementById('agendamentoStatus').value = 'pendente';
    document.getElementById('agendamentoObs').value = '';
  }

  abrirModal('modalAgendamento');
}

function abrirModalCliente() {
  document.getElementById('clienteNome').value = '';
  document.getElementById('clienteTelefone').value = '';
  abrirModal('modalCliente');
}

function abrirWhatsAppAgendamento(agendamento) {
  whatsappAgendamento = agendamento;
  const cliente = getCliente(agendamento.clienteId);
  if (!cliente || !cliente.telefone) {
    mostrarToast('Cliente sem telefone cadastrado!', 'error');
    return;
  }
  const data = dataISOtoDate(agendamento.data);
  const msg = `Olá ${cliente.nome}! 💅\n\nLembrete do seu agendamento:\n📅 Data: ${DIAS_SEMANA[data.getDay()]}, ${data.getDate()} de ${MESES[data.getMonth()]}\n⏰ Horário: ${agendamento.horario}\n✨ Serviço: ${SERVICOS[agendamento.servico].nome}\n\nPor favor, confirme se você vai comparecer. 😊\n\nObrigada!`;
  document.getElementById('whatsappMensagem').value = msg;
  abrirModal('modalWhatsApp');
}

function abrirWhatsAppCliente(cliente) {
  if (!cliente.telefone) {
    mostrarToast('Cliente sem telefone cadastrado!', 'error');
    return;
  }
  const msg = `Olá ${cliente.nome}! 💅✨`;
  document.getElementById('whatsappMensagem').value = msg;
  whatsappAgendamento = null;
  whatsappCliente = cliente;
  abrirModal('modalWhatsApp');
}

// ---------- AÇÕES ----------
function salvarAgendamento() {
  const id = document.getElementById('agendamentoId').value;
  const clienteId = document.getElementById('agendamentoCliente').value;
  const servico = document.getElementById('agendamentoServico').value;
  const data = document.getElementById('agendamentoData').value;
  const horario = document.getElementById('agendamentoHorario').value;
  const status = document.getElementById('agendamentoStatus').value;
  const obs = document.getElementById('agendamentoObs').value;

  if (!clienteId) {
    mostrarToast('Selecione uma cliente!', 'error');
    return;
  }
  if (!data) {
    mostrarToast('Selecione uma data!', 'error');
    return;
  }

  // Verificar conflito de horário
  const conflito = state.agendamentos.find(a =>
    a.data === data && a.horario === horario && a.id !== id && a.status !== 'nao_vai'
  );
  if (conflito) {
    mostrarToast('Este horário já está ocupado!', 'error');
    return;
  }

  if (id) {
    // Editar
    const idx = state.agendamentos.findIndex(a => a.id === id);
    if (idx !== -1) {
      state.agendamentos[idx] = { ...state.agendamentos[idx], clienteId, servico, data, horario, status, obs };
    }
    mostrarToast('Agendamento atualizado! ✅');
  } else {
    // Novo
    state.agendamentos.push({
      id: gerarId(),
      clienteId,
      servico,
      data,
      horario,
      status,
      obs,
      criadoEm: new Date().toISOString()
    });
    mostrarToast('Agendamento criado! ✅');
  }

  salvarState();
  fecharModal('modalAgendamento');
  renderAgenda();
  renderFaturamento();
}

function excluirAgendamento(id) {
  if (!confirm('Excluir este agendamento?')) return;
  state.agendamentos = state.agendamentos.filter(a => a.id !== id);
  salvarState();
  fecharModal('modalAgendamento');
  renderAgenda();
  renderFaturamento();
  mostrarToast('Agendamento excluído.');
}

function salvarCliente() {
  const nome = document.getElementById('clienteNome').value.trim();
  const telefone = document.getElementById('clienteTelefone').value.trim();

  if (!nome) {
    mostrarToast('Informe o nome da cliente!', 'error');
    return;
  }

  state.clientes.push({
    id: gerarId(),
    nome,
    telefone
  });

  salvarState();
  fecharModal('modalCliente');
  renderClientes();
  renderAgenda();
  mostrarToast('Cliente cadastrada! ✅');
}

function excluirCliente(id) {
  if (!confirm('Excluir esta cliente? Os agendamentos dela serão mantidos.')) return;
  state.clientes = state.clientes.filter(c => c.id !== id);
  salvarState();
  renderClientes();
  renderAgenda();
  mostrarToast('Cliente excluída.');
}

function salvarPrecos() {
  state.config.precos.manicure = parseFloat(document.getElementById('precoManicure').value) || 0;
  state.config.precos.cilios = parseFloat(document.getElementById('precoCilios').value) || 0;
  state.config.precos.combo = parseFloat(document.getElementById('precoCombo').value) || 0;
  salvarState();
  renderFaturamento();
  mostrarToast('Preços salvos! ✅');
}

function salvarHorario() {
  state.config.horaAbertura = document.getElementById('horaAbertura').value;
  state.config.horaFechamento = document.getElementById('horaFechamento').value;
  state.config.intervaloMin = parseInt(document.getElementById('intervaloMin').value);
  salvarState();
  renderAgenda();
  mostrarToast('Horário salvo! ✅');
}

function enviarWhatsApp() {
  const msg = document.getElementById('whatsappMensagem').value;
  let telefone = '';

  if (whatsappAgendamento) {
    telefone = getClienteTelefone(whatsappAgendamento.clienteId);
  } else if (whatsappCliente) {
    telefone = whatsappCliente.telefone;
  }

  if (!telefone) {
    mostrarToast('Telefone não encontrado!', 'error');
    return;
  }

  const telLimpo = limparTelefone(telefone);
  const url = `https://wa.me/55${telLimpo}?text=${encodeURIComponent(msg)}`;
  window.open(url, '_blank');
  fecharModal('modalWhatsApp');
  whatsappAgendamento = null;
  whatsappCliente = null;
  mostrarToast('WhatsApp aberto! 📱');
}

function exportarDados() {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `agenda-mae-backup-${hojeISO()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  mostrarToast('Dados exportados! 📥');
}

function limparDados() {
  if (!confirm('Tem certeza? Todos os dados serão apagados permanentemente!')) return;
  if (!confirm('Última confirmação: deseja realmente apagar TUDO?')) return;
  state = {
    clientes: [],
    agendamentos: [],
    config: {
      precos: { manicure: 40, cilios: 80, combo: 110 },
      horaAbertura: '08:00',
      horaFechamento: '20:00',
      intervaloMin: 60
    }
  };
  salvarState();
  renderAgenda();
  renderFaturamento();
  renderClientes();
  renderConfig();
  mostrarToast('Todos os dados foram apagados.');
}

// ---------- TOAST ----------
let toastTimeout = null;
function mostrarToast(msg, tipo = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = 'toast show ' + tipo;
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.className = 'toast';
  }, 3000);
}

// ---------- EVENTOS ----------
function initEventos() {
  // Abas
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
      if (tab.dataset.tab === 'faturamento') renderFaturamento();
      if (tab.dataset.tab === 'clientes') renderClientes();
      if (tab.dataset.tab === 'config') renderConfig();
    });
  });

  // Navegação de semana
  document.getElementById('btnSemanaAnterior').addEventListener('click', () => {
    semanaAtual = addDias(semanaAtual, -7);
    renderAgenda();
  });
  document.getElementById('btnSemanaProxima').addEventListener('click', () => {
    semanaAtual = addDias(semanaAtual, 7);
    renderAgenda();
  });
  document.getElementById('btnHoje').addEventListener('click', () => {
    semanaAtual = new Date();
    renderAgenda();
  });

  // Novo agendamento
  document.getElementById('btnNovoAgendamento').addEventListener('click', () => abrirModalAgendamento(null));

  // Modal agendamento
  document.getElementById('btnFecharModalAgendamento').addEventListener('click', () => fecharModal('modalAgendamento'));
  document.getElementById('btnCancelarAgendamento').addEventListener('click', () => fecharModal('modalAgendamento'));
  document.getElementById('btnSalvarAgendamento').addEventListener('click', salvarAgendamento);
  document.getElementById('btnWhatsAppAgendamento').addEventListener('click', () => {
    if (agendamentoEditando) {
      abrirWhatsAppAgendamento(agendamentoEditando);
    }
  });
  document.getElementById('btnExcluirAgendamento').addEventListener('click', () => {
    if (agendamentoEditando) {
      excluirAgendamento(agendamentoEditando.id);
    }
  });

  // Modal cliente
  document.getElementById('btnNovoCliente').addEventListener('click', abrirModalCliente);
  document.getElementById('btnAddClienteRapido').addEventListener('click', abrirModalCliente);
  document.getElementById('btnFecharModalCliente').addEventListener('click', () => fecharModal('modalCliente'));
  document.getElementById('btnCancelarCliente').addEventListener('click', () => fecharModal('modalCliente'));
  document.getElementById('btnSalvarCliente').addEventListener('click', salvarCliente);

  // Busca cliente
  document.getElementById('buscaCliente').addEventListener('input', renderClientes);

  // Config
  document.getElementById('btnSalvarPrecos').addEventListener('click', salvarPrecos);
  document.getElementById('btnSalvarHorario').addEventListener('click', salvarHorario);
  document.getElementById('btnExportar').addEventListener('click', exportarDados);
  document.getElementById('btnLimparDados').addEventListener('click', limparDados);

  // WhatsApp
  document.getElementById('btnFecharModalWhatsApp').addEventListener('click', () => fecharModal('modalWhatsApp'));
  document.getElementById('btnCancelarWhatsApp').addEventListener('click', () => fecharModal('modalWhatsApp'));
  document.getElementById('btnEnviarWhatsApp').addEventListener('click', enviarWhatsApp);

  // Fechar modal ao clicar fora
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.classList.remove('active');
    });
  });

  // Tecla ESC fecha modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
    }
  });
}

// ---------- INICIALIZAÇÃO ----------
function init() {
  carregarState();
  initEventos();
  renderAgenda();
  renderFaturamento();
  renderClientes();
  renderConfig();
}

document.addEventListener('DOMContentLoaded', init);