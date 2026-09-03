# ============================================
# DATABASE/WPP_MODELS.PY — Modelos da integração WhatsApp
# ============================================

from datetime import datetime
from . import db


class MensagemRecebida(db.Model):
    """Mensagem recebida via webhook do WhatsApp."""
    __tablename__ = 'mensagens_recebidas'

    id = db.Column(db.Integer, primary_key=True)
    whatsapp_id = db.Column(db.String(80), unique=True, index=True)
    telefone = db.Column(db.String(20), nullable=False, index=True)
    nome_contato = db.Column(db.String(150))
    corpo = db.Column(db.Text)
    tipo = db.Column(db.String(20), default='text')  # text | interactive | imagem ...
    texto_normalizado = db.Column(db.String(200))
    processada = db.Column(db.Boolean, default=False)
    data_recebimento = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'whatsapp_id': self.whatsapp_id,
            'telefone': self.telefone,
            'nome_contato': self.nome_contato,
            'corpo': self.corpo,
            'tipo': self.tipo,
            'processada': self.processada,
            'data_recebimento': self.data_recebimento
        }


class MensagemEnviada(db.Model):
    """Mensagem enviada pela aplicação via WhatsApp API."""
    __tablename__ = 'mensagens_enviadas'

    id = db.Column(db.Integer, primary_key=True)
    whatsapp_message_id = db.Column(db.String(80), unique=True)
    telefone = db.Column(db.String(20), nullable=False, index=True)
    corpo = db.Column(db.Text)
    tipo = db.Column(db.String(20), default='text')  # text | template
    status = db.Column(db.String(20), default='enviada')
    # enviada | entregue | lida | erro
    erro = db.Column(db.String(255))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'whatsapp_message_id': self.whatsapp_message_id,
            'telefone': self.telefone,
            'corpo': self.corpo,
            'tipo': self.tipo,
            'status': self.status,
            'erro': self.erro,
            'data_envio': self.data_envio
        }


class SessaoConversa(db.Model):
    """
    Sessão de conversa do WhatsApp.

    Guarda o estado da conversa (fluxo atual), dados temporários
    que o cliente está digitando (cadastro, agendamento) e contexto
    da conversa para retomada.
    """
    __tablename__ = 'sessoes_conversa'

    id = db.Column(db.Integer, primary_key=True)
    telefone = db.Column(db.String(20), nullable=False, unique=True, index=True)
    estado = db.Column(db.String(40), default='menu')  # estado do fluxo
    contexto = db.Column(db.Text, default='{}')  # JSON com dados temporários
    ultima_atividade = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    qtd_mensagens = db.Column(db.Integer, default=0)
    criada_em = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'telefone': self.telefone,
            'estado': self.estado,
            'contexto': self.contexto,
            'ultima_atividade': self.ultima_atividade,
            'qtd_mensagens': self.qtd_mensagens
        }


class LogAuditoria(db.Model):
    """Log de auditoria de ações administrativas e eventos de segurança."""
    __tablename__ = 'logs_auditoria'

    id = db.Column(db.Integer, primary_key=True)
    telefone = db.Column(db.String(20), index=True)
    acao = db.Column(db.String(80), nullable=False, index=True)
    detalhe = db.Column(db.Text)  # descrição sem dados sensíveis
    ip = db.Column(db.String(45))
    data = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'telefone': self.telefone,
            'acao': self.acao,
            'detalhe': self.detalhe,
            'data': self.data
        }


class ConfigWhatsApp(db.Model):
    """
    Configurações da integração WhatsApp armazenadas no banco.
    Somente valores NÃO secretos devem ficar aqui (tokens/segredos
    devem permanecer em variáveis de ambiente).
    """
    __tablename__ = 'config_whatsapp'

    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(60), unique=True, nullable=False)
    valor = db.Column(db.Text)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    def to_dict(self):
        return {'chave': self.chave, 'valor': self.valor}
