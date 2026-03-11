from datetime import datetime
from .database import db

class Visita(db.Model):
    __tablename__ = 'visitas'
    id = db.Column(db.Integer, primary_key=True)
    # Dados do visitante (preenchidos após escanear)
    nome_visitante = db.Column(db.String(100))
    placa = db.Column(db.String(10))
    destino = db.Column(db.String(100))   # pode ser selecionado de uma lista de casas
    # Dados do morador (para notificação)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=True)
    # Status do ciclo de vida
    status = db.Column(db.String(20), default='AGUARDANDO_CADASTRO')
    # Status da notificação WhatsApp
    status_whatsapp = db.Column(db.String(30), default='NENHUM')  # NOTIFICADO, SIM, NAO, TIMEOUT, PORTEIRO
    # Momentos importantes
    horario_entrada = db.Column(db.DateTime, default=datetime.now)
    horario_saida = db.Column(db.DateTime, nullable=True)
    horario_notificacao_zap = db.Column(db.DateTime, nullable=True)  # quando foi mandado pro zap
    horario_resposta_zap = db.Column(db.DateTime, nullable=True)     # quando morador respondeu
    horario_timeout = db.Column(db.DateTime, nullable=True)          # quando expirou o tempo
    # Localização em tempo real
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    # Para geofencing
    ultima_atualizacao = db.Column(db.DateTime, nullable=True)
    # ID do widget no porteiro (se foi movido lá)
    widget_id = db.Column(db.String(50), nullable=True)

class Morador(db.Model):
    __tablename__ = 'moradores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    telefone = db.Column(db.String(20))        # para futura integração WhatsApp
    email = db.Column(db.String(100))
    casa = db.Column(db.String(20))            # ex: "1719"
    # Coordenadas da residência (para rota)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    # Token único para acesso ao painel (simplificado)
    token = db.Column(db.String(50), unique=True)


class Condominio(db.Model):
    """Representa um condomínio (ou conjunto residencial)."""
    __tablename__ = 'condominios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    endereco = db.Column(db.String(200), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(50), nullable=True)
    ativo = db.Column(db.Boolean, default=True)


class Casa(db.Model):
    """Unidade/Residência dentro de um condomínio."""
    __tablename__ = 'casas'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False)
    bloco = db.Column(db.String(20), nullable=True)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominios.id'), nullable=False)

    # relacionamento opcional para navegação
    condominio = db.relationship('Condominio', backref=db.backref('casas', lazy=True))

class PlacaReconhecida(db.Model):
    __tablename__ = 'placas_reconhecidas'
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(10))
    imagem_path = db.Column(db.String(200))  # caminho da imagem salva
    data_hora = db.Column(db.DateTime, default=datetime.now)
    camera_id = db.Column(db.String(50))
