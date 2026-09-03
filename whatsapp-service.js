// ============================================
// WHATSAPP-SERVICE.JS — Integração WhatsApp
// ============================================

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const { dbGet, dbAll, dbRun } = require('./database');

const API_URL = 'http://localhost:3000';

let client = null;
let isConnected = false;

// Inicializar cliente WhatsApp
function initWhatsApp() {
  console.log('🔄 Inicializando WhatsApp Web...');

  client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
  });

  // QR Code para autenticação
  client.on('qr', (qr) => {
    console.log('\n📱 Escaneie este QR Code com WhatsApp:');
    qrcode.generate(qr, { small: true });
  });

  // Cliente pronto
  client.on('ready', () => {
    console.log('✅ WhatsApp conectado com sucesso!');
    isConnected = true;
  });

  // Receber mensagens
  client.on('message', (message) => {
    handleIncomingMessage(message);
  });

  // Desconexão
  client.on('disconnected', () => {
    console.log('❌ WhatsApp desconectado');
    isConnected = false;
  });

  // Inicializar
  client.initialize();
}

// Processar mensagens recebidas
async function handleIncomingMessage(message) {
  const numero = message.from.replace('@c.us', '');
  const texto = message.body.toLowerCase();

  console.log(`📨 Mensagem de ${numero}: ${texto}`);

  // Procurar cliente pelo telefone
  const cliente = await dbGet(
    `SELECT * FROM clientes WHERE telefone LIKE ?`,
    [`%${numero}%`]
  );

  if (!cliente) {
    await message.reply('Olá! 👋 Você não está cadastrado no nosso sistema. Por favor, entre em contato conosco.');
    return;
  }

  // Processar comandos/respostas
  if (texto.includes('confirmar') || texto.includes('sim') || texto.includes('✅')) {
    await processarConfirmacao(message, cliente);
  } else if (texto.includes('cancelar') || texto.includes('não') || texto.includes('❌')) {
    await processarCancelamento(message, cliente);
  } else if (texto.includes('horário') || texto.includes('disponível')) {
    await enviarHorarioDisponivel(message, cliente);
  } else if (texto.includes('agende') || texto.includes('agendar')) {
    await message.reply('Para agendar, acesse: https://seu-app.com/agenda ou envie: DATA HORA (ex: 30/08 14:00)');
  } else {
    await message.reply('Desculpe, não entendi. Envie:\n✅ Confirmar - confirmar agendamento\n❌ Cancelar - cancelar agendamento\n📅 Horários - ver horários disponíveis');
  }
}

// Processar confirmação de agendamento
async function processarConfirmacao(message, cliente) {
  try {
    const agendamentos = await dbAll(
      `SELECT * FROM agendamentos WHERE clienteId = ? AND status = 'pendente' ORDER BY data DESC, horario DESC LIMIT 1`,
      [cliente.id]
    );

    if (agendamentos.length === 0) {
      await message.reply('Você não tem agendamentos pendentes. 😊');
      return;
    }

    const agendamento = agendamentos[0];
    await dbRun(
      `UPDATE agendamentos SET status = 'confirmada', confirmaçaoWhatsapp = 1 WHERE id = ?`,
      [agendamento.id]
    );

    await message.reply(`✅ Agendamento confirmado!\n📅 ${agendamento.data}\n⏰ ${agendamento.horario}\nAté logo! 💅`);

    // Registrar log
    await dbRun(
      `INSERT INTO logs_whatsapp (agendamentoId, clienteId, mensagem, status) VALUES (?, ?, ?, ?)`,
      [agendamento.id, cliente.id, 'Confirmação recebida via WhatsApp', 'confirmado']
    );
  } catch (err) {
    console.error('Erro ao processar confirmação:', err);
    await message.reply('Ocorreu um erro ao processar sua confirmação. Tente novamente.');
  }
}

// Processar cancelamento
async function processarCancelamento(message, cliente) {
  try {
    const agendamentos = await dbAll(
      `SELECT * FROM agendamentos WHERE clienteId = ? AND status = 'confirmada' ORDER BY data DESC, horario DESC LIMIT 1`,
      [cliente.id]
    );

    if (agendamentos.length === 0) {
      await message.reply('Você não tem agendamentos confirmados para cancelar. 😊');
      return;
    }

    const agendamento = agendamentos[0];
    await dbRun(
      `UPDATE agendamentos SET status = 'nao_vai' WHERE id = ?`,
      [agendamento.id]
    );

    await message.reply(`❌ Agendamento cancelado.\n📅 ${agendamento.data}\n⏰ ${agendamento.horario}\n\nSe mudar de ideia, nos avise! 💅`);

    // Registrar log
    await dbRun(
      `INSERT INTO logs_whatsapp (agendamentoId, clienteId, mensagem, status) VALUES (?, ?, ?, ?)`,
      [agendamento.id, cliente.id, 'Cancelamento recebido via WhatsApp', 'cancelado']
    );
  } catch (err) {
    console.error('Erro ao processar cancelamento:', err);
    await message.reply('Ocorreu um erro ao processar seu cancelamento. Tente novamente.');
  }
}

// Enviar horários disponíveis
async function enviarHorarioDisponivel(message, cliente) {
  try {
    const hoje = new Date();
    const proximos7Dias = [];
    
    for (let i = 0; i < 7; i++) {
      proximos7Dias.push(new Date(hoje.getTime() + i * 24 * 60 * 60 * 1000));
    }

    let mensagem = '📅 Horários disponíveis:\n\n';

    for (const dia of proximos7Dias) {
      const dataISO = dia.toISOString().split('T')[0];
      const agendados = await dbAll(
        `SELECT horario FROM agendamentos WHERE data = ? AND status != 'nao_vai'`,
        [dataISO]
      );

      const horariosAgendados = agendados.map(a => a.horario);
      const horarios = ['08:00', '09:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00'];
      const disponiveis = horarios.filter(h => !horariosAgendados.includes(h));

      mensagem += `${formatarDia(dia)}: ${disponiveis.slice(0, 3).join(', ')}\n`;
    }

    mensagem += '\nPara agendar, responda: DATA HORA (ex: 30/08 14:00)';
    await message.reply(mensagem);
  } catch (err) {
    console.error('Erro ao enviar horários:', err);
    await message.reply('Erro ao buscar horários disponíveis. Tente novamente.');
  }
}

// Enviar mensagem proativa
async function enviarLembrete(clienteId, agendamentoId) {
  try {
    if (!isConnected) {
      console.log('⚠️ WhatsApp não conectado. Salvando mensagem para envio posterior.');
      return;
    }

    const cliente = await dbGet(`SELECT * FROM clientes WHERE id = ?`, [clienteId]);
    const agendamento = await dbGet(`SELECT * FROM agendamentos WHERE id = ?`, [agendamentoId]);

    if (!cliente || !cliente.telefone) {
      console.log('Cliente sem telefone');
      return;
    }

    const numero = cliente.telefone.replace(/\D/g, '');
    const chatId = `55${numero}@c.us`;
    const dataBR = agendamento.data.split('-').reverse().join('/');
    
    const msg = `Olá ${cliente.nome}! 💅\n\n` +
                `Lembrete do seu agendamento:\n` +
                `📅 Data: ${dataBR}\n` +
                `⏰ Horário: ${agendamento.horario}\n` +
                `✨ Serviço: ${agendamento.servico}\n\n` +
                `Por favor, confirme se você vai comparecer.\n` +
                `Responda: ✅ Confirmar ou ❌ Cancelar`;

    await client.sendMessage(chatId, msg);

    // Registrar log
    await dbRun(
      `INSERT INTO logs_whatsapp (agendamentoId, clienteId, mensagem, status) VALUES (?, ?, ?, ?)`,
      [agendamentoId, clienteId, msg, 'lembrete_enviado']
    );

    console.log(`✅ Lembrete enviado para ${cliente.nome}`);
  } catch (err) {
    console.error('Erro ao enviar lembrete:', err);
  }
}

// Enviar confirmação de agendamento
async function enviarConfirmacaoAgendamento(clienteId, agendamentoId) {
  try {
    if (!isConnected) {
      console.log('⚠️ WhatsApp não conectado');
      return;
    }

    const cliente = await dbGet(`SELECT * FROM clientes WHERE id = ?`, [clienteId]);
    const agendamento = await dbGet(`SELECT * FROM agendamentos WHERE id = ?`, [agendamentoId]);

    if (!cliente || !cliente.telefone) return;

    const numero = cliente.telefone.replace(/\D/g, '');
    const chatId = `55${numero}@c.us`;
    const dataBR = agendamento.data.split('-').reverse().join('/');

    const msg = `Olá ${cliente.nome}! ✨\n\n` +
                `Seu agendamento foi confirmado! 🎉\n` +
                `📅 ${dataBR}\n` +
                `⏰ ${agendamento.horario}\n` +
                `💅 ${agendamento.servico}\n\n` +
                `Até logo! 😊`;

    await client.sendMessage(chatId, msg);

    await dbRun(
      `INSERT INTO logs_whatsapp (agendamentoId, clienteId, mensagem, status) VALUES (?, ?, ?, ?)`,
      [agendamentoId, clienteId, msg, 'confirmacao_enviada']
    );
  } catch (err) {
    console.error('Erro ao enviar confirmação:', err);
  }
}

// Formatador de data
function formatarDia(data) {
  const dias = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab'];
  return `${dias[data.getDay()]} ${data.getDate()}/${data.getMonth() + 1}`;
}

// Verificar status da conexão
function getStatus() {
  return {
    conectado: isConnected,
    timestamp: new Date().toISOString()
  };
}

module.exports = {
  initWhatsApp,
  enviarLembrete,
  enviarConfirmacaoAgendamento,
  getStatus
};
