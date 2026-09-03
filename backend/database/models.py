# ============================================
# DATABASE/MODELS.PY — Modelos ORM
# ============================================

from datetime import datetime, date
from . import db


class Usuario(db.Model):
    """Usuário do sistema (administrador)."""
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')  # admin | usuario
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nome': self.nome,
            'role': self.role,
            'ultimo_login': self.ultimo_login
        }


class Cliente(db.Model):
    """Cliente do salão."""
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, index=True)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)

    agendamentos = db.relationship('Agendamento', backref='cliente', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'telefone': self.telefone,
            'email': self.email,
            'observacoes': self.observacoes,
            'data_cadastro': self.data_cadastro
        }


class Servico(db.Model):
    """Serviço oferecido pelo salão."""
    __tablename__ = 'servicos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    duracao_min = db.Column(db.Integer, nullable=False, default=60)  # duração em min
    ativo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco': float(self.preco),
            'duracao_min': self.duracao_min,
            'ativo': self.ativo
        }


class Agendamento(db.Model):
    """Agendamento de um serviço para um cliente."""
    __tablename__ = 'agendamentos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    data = db.Column(db.Date, nullable=False, index=True)
    horario = db.Column(db.String(5), nullable=False)  # HH:MM
    status = db.Column(db.String(20), nullable=False, default='pendente')
    # pendente | confirmada | nao_vai | cancelada | realizada
    obs = db.Column(db.Text)
    preco = db.Column(db.Numeric(10, 2))
    whatsapp_confirmado = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_confirmacao = db.Column(db.DateTime)

    servico = db.relationship('Servico', lazy=True)
    __table_args__ = (db.UniqueConstraint('data', 'horario', name='uq_data_horario'),)

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'servico_id': self.servico_id,
            'cliente': self.cliente.nome if self.cliente else None,
            'servico': self.servico.nome if self.servico else None,
            'data': self.data.isoformat() if self.data else None,
            'horario': self.horario,
            'status': self.status,
            'obs': self.obs,
            'preco': float(self.preco) if self.preco else None
        }


class Configuracao(db.Model):
    """Configurações gerais do sistema (chave-valor)."""
    __tablename__ = 'configuracoes'

    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Text)

    def to_dict(self):
        return {'chave': self.chave, 'valor': self.valor}


class Faturamento(db.Model):
    """Registro de faturamento (agendamentos realizados)."""
    __tablename__ = 'faturamento'

    id = db.Column(db.Integer, primary_key=True)
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamentos.id'), unique=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'))
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    data_realizacao = db.Column(db.Date, nullable=False)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'agendamento_id': self.agendamento_id,
            'cliente_id': self.cliente_id,
            'servico_id': self.servico_id,
            'preco': float(self.preco),
            'data_realizacao': self.data_realizacao.isoformat()
        }
