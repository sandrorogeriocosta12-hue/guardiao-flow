"""
WebSocket Manager for Guardião Flow
Gerencia todas as conexões e broadcasts de eventos em tempo real.

Rooms (Salas):
  - porteiro_{condominio_id}
  - interfone_{condominio_id}
  - visita_{visita_id}
  - morador_{morador_token}

Eventos são estruturados com: { event, data, timestamp, source }
"""

from flask_socketio import SocketIO, join_room, leave_room, emit, rooms
from datetime import datetime
from functools import wraps
import json
import logging
from .database import db
from .models import Visita, Morador

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instância global
socketio = None
connected_clients = {}

def init_socketio(app):
    """Inicializa SocketIO com a app Flask."""
    global socketio
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*", 
        async_mode='threading', 
        logger=False, 
        engineio_logger=False,
        ping_timeout=60,
        ping_interval=25
    )
    
    @socketio.on('connect')
    def on_connect(auth):
        """Cliente se conecta ao WebSocket."""
        client_id = auth.get('client_id') if auth else 'unknown'
        logger.info(f"[✓ CONNECT] {client_id}")
        emit('CONEXAO_ESTABELECIDA', {
            'mensagem': 'Bem-vindo ao Guardião Flow',
            'timestamp': datetime.now().isoformat(),
            'servidor_versao': '2.0'
        })
    
    @socketio.on('disconnect')
    def on_disconnect():
        """Cliente se desconecta."""
        logger.info(f"[✗ DISCONNECT]")
    
    @socketio.on('ENTRAR_SALA')
    def on_entrar_sala(data):
        """Cliente entra em uma room específica."""
        room = data.get('room')
        if room:
            join_room(room)
            logger.info(f"[→ ROOM] Entrou em {room}")
            emit('SALA_CONECTADA', {
                'room': room,
                'timestamp': datetime.now().isoformat()
            }, room=room)
    
    @socketio.on('SAIR_SALA')
    def on_sair_sala(data):
        """Cliente sai de uma room."""
        room = data.get('room')
        if room:
            leave_room(room)
            logger.info(f"[← ROOM] Saiu de {room}")
    
    @socketio.on('PING')
    def on_ping(data):
        """Keepalive/heartbeat."""
        emit('PONG', {'timestamp': datetime.now().isoformat()})

    # ----- Handlers para eventos emitidos pelos clientes (compatibilidade com testes) -----
    @socketio.on('REGISTRAR_VISITA')
    def on_registrar_visita(data):
        """Recebe registro de visita via WebSocket (fallback ao POST)."""
        try:
            qr_id = data.get('qr_id')
            visita = Visita.query.get(qr_id)
            if not visita or visita.status != 'AGUARDANDO_CADASTRO':
                emit('ERROR', {'msg': 'QR inválido ou expirado'})
                return
            visita.nome_visitante = data.get('nome')
            visita.placa = data.get('placa')
            visita.destino = data.get('destino')
            morador = Morador.query.filter_by(casa=data.get('destino')).first()
            if morador:
                visita.morador_id = morador.id
            visita.status = 'AGUARDANDO_MORADOR'
            db.session.commit()
            # Notifica
            nova_visita_criada(1, visita)
        except Exception as e:
            logger.exception('Erro REGISTRAR_VISITA: %s', e)

    @socketio.on('AUTORIZAR_VISITA')
    def on_autorizar_visita(data):
        """Morador autoriza via WebSocket."""
        try:
            visita_id = data.get('visita_id')
            token = data.get('morador_token') or data.get('token')
            logger.info(f"[→ SOCKET] AUTORIZAR_VISITA token={token} visita_id={visita_id}")
            morador = Morador.query.filter_by(token=token).first()
            visita = Visita.query.get(visita_id)
            if not visita or not morador or visita.morador_id != morador.id:
                emit('ERROR', {'msg': 'Acesso negado'})
                return
            visita.status = 'EM_ROTA_ENTRADA'
            db.session.commit()
            visita_liberada(1, visita)
        except Exception as e:
            logger.exception('Erro AUTORIZAR_VISITA: %s', e)

    @socketio.on('ENVIAR_GPS')
    def on_enviar_gps(data):
        """Atualização de GPS via WebSocket."""
        try:
            visita_id = data.get('visita_id')
            lat = data.get('latitude') or data.get('lat')
            lng = data.get('longitude') or data.get('lng')
            visita = Visita.query.get(visita_id)
            if not visita:
                return
            visita.latitude = lat
            visita.longitude = lng
            visita.ultima_atualizacao = datetime.now()
            db.session.commit()
            localizacao_atualizada(1, visita, lat, lng, data.get('precisao_metros') or data.get('accuracy'))
            verificar = globals().get('verificar_geofence')
            # chamar verificar_geofence se estiver disponível (definida no app)
            if verificar:
                try:
                    verificar(visita)
                except Exception:
                    pass
        except Exception as e:
            logger.exception('Erro ENVIAR_GPS: %s', e)

    @socketio.on('INICIAR_RETORNO')
    def on_iniciar_retorno(data):
        try:
            visita_id = data.get('visita_id')
            visita = Visita.query.get(visita_id)
            if not visita:
                return
            visita.status = 'EM_ROTA_SAIDA'
            db.session.commit()
            retorno_iniciado(1, visita)
        except Exception as e:
            logger.exception('Erro INICIAR_RETORNO: %s', e)
    
    return socketio

# ========== FUNÇÕES DE EMIT ESTRUTURADAS ==========

def _emit_event(room, evento, dados, source='server'):
    """Emite evento estruturado para uma room."""
    if not socketio:
        return False
    
    payload = {
        'event': evento,
        'data': dados,
        'timestamp': datetime.now().isoformat(),
        'source': source
    }
    
    socketio.emit(evento, payload, room=room, skip_sid=None)
    logger.info(f"[📤 {evento}] room={room}")
    return True

def _emit_multiplo(evento, dados, rooms_list, source='server'):
    """Emite para múltiplas rooms."""
    if not socketio:
        return False
    
    payload = {
        'event': evento,
        'data': dados,
        'timestamp': datetime.now().isoformat(),
        'source': source
    }
    
    for room in rooms_list:
        socketio.emit(evento, payload, room=room, skip_sid=None)
    
    logger.info(f"[📤 {evento}] rooms={len(rooms_list)}")
    return True

# ========== BROADCASTS POR TIPO DE CLIENTE ==========

def emitir_para_porteiro(condominio_id, evento, dados):
    """Emite evento para o painel do porteiro."""
    room = f'porteiro_{condominio_id}'
    return _emit_event(room, evento, dados)

def emitir_para_interfone(condominio_id, evento, dados):
    """Emite evento para a tela do interfone."""
    room = f'interfone_{condominio_id}'
    return _emit_event(room, evento, dados)

def emitir_para_visitante(visita_id, evento, dados):
    """Emite evento para o visitante específico."""
    room = f'visita_{visita_id}'
    return _emit_event(room, evento, dados)

def emitir_para_morador(morador_token, evento, dados):
    """Emite evento para o morador específico."""
    room = f'morador_{morador_token}'
    return _emit_event(room, evento, dados)

# ========== EVENTOS DE NEGÓCIO ==========

def qr_code_gerado(condominio_id, qr_id, qr_image_base64, expira_em_segundos=120):
    """QR Code foi gerado e está pronto para exibição."""
    dados = {
        'qr_id': qr_id,
        'qr_url': f'http://localhost:5001/?qr_id={qr_id}',
        'qr_image_base64': qr_image_base64,
        'expira_em_segundos': expira_em_segundos,
        'gerado_em': datetime.now().isoformat()
    }
    _emit_multiplo('QR_CODE_GERADO', dados, [
        f'interfone_{condominio_id}',
        f'porteiro_{condominio_id}'
    ])

def nova_visita_criada(condominio_id, visita):
    """Nova visita foi registrada no sistema."""
    morador = Morador.query.get(visita.morador_id) if visita.morador_id else None
    dados = {
        'visita_id': visita.id,
        'nome_visitante': visita.nome_visitante,
        'placa': visita.placa,
        'destino': visita.destino,
        'status': visita.status,
        'horario_entrada': visita.horario_entrada.isoformat() if visita.horario_entrada else None,
        'morador_id': visita.morador_id,
        'morador_nome': morador.nome if morador else None
    }
    _emit_event(f'porteiro_{condominio_id}', 'VISITA_CRIADA', dados)

def visita_liberada(condominio_id, visita):
    """Morador aprovou entrada do visitante."""
    logger.info(f"[→ BUSINESS] visita_liberada called visita={getattr(visita,'id',None)} condominio={condominio_id}")
    morador = Morador.query.get(visita.morador_id) if visita.morador_id else None
    mapa_destino = {
        'nome': visita.destino,
        'latitude': morador.latitude if morador else -23.5505,
        'longitude': morador.longitude if morador else -46.6333,
        'geofence_raio_metros': 20
    }
    
    dados = {
        'visita_id': visita.id,
        'status': 'EM_ROTA_ENTRADA',
        'morador_nome': morador.nome if morador else None,
        'autorizado_em': datetime.now().isoformat(),
        'mapa_destino': mapa_destino
    }
    
    # Visitante vê autorização e rota
    _emit_event(f'visita_{visita.id}', 'VISITA_LIBERADA', dados)
    
    # Porteiro vê status atualizado
    _emit_event(f'porteiro_{condominio_id}', 'VISITA_LIBERADA', dados)

def visita_rejeitada(condominio_id, visita):
    """Morador recusou entrada do visitante."""
    dados = {
        'visita_id': visita.id,
        'status': 'REJEITADA',
        'recusada_por': Morador.query.get(visita.morador_id).nome if visita.morador_id else None,
        'timestamp': datetime.now().isoformat(),
        'mensagem_visitante': 'Sua entrada foi recusada. Por favor, contate o morador.'
    }
    
    _emit_event(f'visita_{visita.id}', 'VISITA_REJEITADA', dados)
    _emit_event(f'porteiro_{condominio_id}', 'VISITA_REJEITADA', dados)

def localizacao_atualizada(condominio_id, visita, lat, lng, precisao=None):
    """GPS do visitante atualizado (40-50m de intervalo)."""
    dados = {
        'visita_id': visita.id,
        'latitude': lat,
        'longitude': lng,
        'precisao_metros': precisao or 10,
        'timestamp': datetime.now().isoformat(),
        'status': visita.status
    }
    _emit_event(f'porteiro_{condominio_id}', 'LOCALIZACAO_ATUALIZADA', dados)

def visitante_chegou_destino(condominio_id, visita):
    """Geofence acionado - visitante chegou ao destino (< 20m)."""
    dados = {
        'visita_id': visita.id,
        'evento': 'chegada',
        'latitude': visita.latitude,
        'longitude': visita.longitude,
        'timestamp': datetime.now().isoformat(),
        'mensagem': 'Visitante chegou ao destino. Portão será aberto automaticamente.'
    }
    
    mor = Morador.query.get(visita.morador_id) if visita.morador_id else None
    _emit_multiplo('VISITANTE_CHEGOU_DESTINO', dados, [
        f'visita_{visita.id}',
        f'porteiro_{condominio_id}',
        f'morador_{mor.token}' if mor else None
    ])

def retorno_iniciado(condominio_id, visita):
    """Visitante iniciou retorno à portaria."""
    dados = {
        'visita_id': visita.id,
        'status': 'EM_ROTA_SAIDA',
        'timestamp': datetime.now().isoformat(),
        'iniciado_por': 'visitante',
        'mensagem': 'Visitante iniciando retorno à portaria'
    }
    
    mor = Morador.query.get(visita.morador_id) if visita.morador_id else None
    _emit_multiplo('RETORNO_INICIADO', dados, [
        f'porteiro_{condominio_id}',
        f'morador_{mor.token}' if mor else None
    ])

def geofence_acionado(condominio_id, visita, tipo='saida', distancia=None):
    """Geofence acionado - visitante saindo da portaria (> 30m)."""
    dados = {
        'visita_id': visita.id,
        'tipo': tipo,
        'latitude': visita.latitude,
        'longitude': visita.longitude,
        'distancia_portaria_metros': distancia or 30,
        'timestamp': datetime.now().isoformat(),
        'mensagem': f'Visitante saindo do condomínio - Acesso finalizado'
    }
    
    _emit_multiplo('GEOFENCE_ACIONADO', dados, [
        f'porteiro_{condominio_id}',
        f'visita_{visita.id}'
    ])

def visita_finalizada(condominio_id, visita, motivo='geofence_saida'):
    """Visita foi finalizada - acesso encerrado automaticamente."""
    duracao_minutos = 0
    if visita.horario_entrada and visita.horario_saida:
        duracao = (visita.horario_saida - visita.horario_entrada).total_seconds() / 60
        duracao_minutos = int(duracao)
    
    dados = {
        'visita_id': visita.id,
        'status': 'FINALIZADO',
        'nome_visitante': visita.nome_visitante,
        'horario_entrada': visita.horario_entrada.isoformat() if visita.horario_entrada else None,
        'horario_saida': visita.horario_saida.isoformat() if visita.horario_saida else None,
        'duracao_minutos': duracao_minutos,
        'motivo': motivo,
        'timestamp': datetime.now().isoformat()
    }
    
    mor = Morador.query.get(visita.morador_id) if visita.morador_id else None
    _emit_multiplo('VISITA_FINALIZADA', dados, [
        f'visita_{visita.id}',
        f'porteiro_{condominio_id}',
        f'morador_{mor.token}' if mor else None
    ])
# ========== ROOM MANAGEMENT ==========

def room_exists(room_name):
    """Verifica se uma room tem clientes conectados."""
    if not socketio:
        return False
    # Nota: flask-socketio não expõe isso facilmente, então sempre retorna True
    return True

def cliente_registrou_sala(tipo, id_recurso=None, condominio_id=1):
    """Liga/desliga cliente para a sala correta."""
    if tipo == 'porteiro':
        join_room(f'porteiro_{condominio_id}')
    elif tipo == 'interfone':
        join_room(f'interfone_{condominio_id}')
    elif tipo == 'visitante' and id_recurso:
        join_room(f'visita_{id_recurso}')
    elif tipo == 'morador' and id_recurso:
        join_room(f'morador_{id_recurso}')
    
    logger.info(f"[SALA_JOIN] {tipo} → {id_recurso or condominio_id}")

