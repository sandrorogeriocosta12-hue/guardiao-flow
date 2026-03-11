import os
import qrcode
import uuid
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from .database import db
from .models import Visita, Morador
from .websocket_manager import init_socketio, emitir_para_porteiro, emitir_para_interfone, emitir_para_visitante, emitir_para_morador, nova_visita_criada, visita_liberada, visita_rejeitada, localizacao_atualizada, visitante_chegou_destino, retorno_iniciado, geofence_acionado, visita_finalizada, qr_code_gerado
from .notificacao_service import NotificacaoService

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Inicializa WebSocket
socketio = init_socketio(app)

# Configuração SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    # Criar alguns moradores de exemplo (se não houver nenhum)
    if not Morador.query.first():
        m1 = Morador(nome="João Silva", telefone="11999999999", email="joao@email.com", casa="1719", 
                     latitude=-23.5505, longitude=-46.6333, token=str(uuid.uuid4()))
        m2 = Morador(nome="Maria Souza", telefone="11888888888", email="maria@email.com", casa="1720",
                     latitude=-23.5510, longitude=-46.6340, token=str(uuid.uuid4()))
        db.session.add_all([m1, m2])
        db.session.commit()
        print("Moradores de exemplo criados.")
        print(f"Tokens: {m1.casa} -> {m1.token}, {m2.casa} -> {m2.token}")

# ========== ROTAS ESTÁTICAS ==========

@app.route('/')
def root():
    return send_file('../frontend/index.html')

@app.route('/morador.html')
def morador_page():
    return send_file('../frontend/morador.html')

@app.route('/monitor.html')
def monitor_page():
    return send_file('../frontend/monitor.html')

# ========== ROTAS PÚBLICAS / VISITANTE ==========

@app.route('/api/iniciar_visita', methods=['POST'])
def iniciar_visita():
    """Chamado após escanear QR, quando o visitante preenche seus dados."""
    data = request.json
    qr_id = data.get('qr_id')
    visita = Visita.query.filter_by(id=qr_id, status='AGUARDANDO_CADASTRO').first()
    if not visita:
        return jsonify({'erro': 'QR Code inválido ou expirado'}), 400

    visita.nome_visitante = data.get('nome')
    visita.placa = data.get('placa')
    visita.destino = data.get('destino')
    morador = Morador.query.filter_by(casa=data.get('destino')).first()
    if morador:
        visita.morador_id = morador.id
    visita.status = 'AGUARDANDO_MORADOR'
    db.session.commit()

    # Notifica porteiro via WebSocket
    nova_visita_criada(1, visita)

    # 🎯 NOVO: Enviar notificação WhatsApp com sistema de timeout
    if morador and morador.telefone:
        try:
            # Inicia o fluxo de notificação com fallback automático
            NotificacaoService.notificar_morador(visita.id, socketio)
            print(f"[✅] Sistema de notificação iniciado para Visita {visita.id}")
        except Exception as e:
            print(f"[⚠️] Erro ao iniciar notificação: {e}")
            # Se falhar, move direto pro porteiro
            NotificacaoService.mover_para_porteiro(
                visita.id, 
                socketio, 
                razao="Erro ao enviar WhatsApp"
            )
    
    return jsonify({'visita_id': visita.id, 'status': visita.status})

@app.route('/api/visita/<int:visita_id>')
def get_visita(visita_id):
    visita = Visita.query.get_or_404(visita_id)
    morador = Morador.query.get(visita.morador_id) if visita.morador_id else None
    return jsonify({
        'id': visita.id,
        'status': visita.status,
        'nome': visita.nome_visitante,
        'placa': visita.placa,
        'destino': visita.destino,
        'latitude': visita.latitude,
        'longitude': visita.longitude,
        'morador': {'nome': morador.nome, 'casa': morador.casa} if morador else None
    })

@app.route('/api/atualizar_localizacao', methods=['POST'])
def atualizar_localizacao():
    data = request.json
    visita_id = data.get('visita_id')
    lat = data.get('lat')
    lng = data.get('lng')
    visita = Visita.query.get(visita_id)
    if not visita:
        return jsonify({'erro': 'Visita não encontrada'}), 404
    if visita.status in ['EM_ROTA_ENTRADA', 'EM_ROTA_SAIDA']:
        visita.latitude = lat
        visita.longitude = lng
        visita.ultima_atualizacao = datetime.now()
        db.session.commit()
        
        # Broadcast via WebSocket (condomínio 1)
        localizacao_atualizada(1, visita, lat, lng, data.get('accuracy'))
        
        # Verifica geofencing
        verificar_geofence(visita)
    return jsonify({'status': 'ok'})

@app.route('/api/finalizar_visita/<int:visita_id>', methods=['POST'])
def finalizar_visita(visita_id):
    visita = Visita.query.get_or_404(visita_id)
    visita.horario_saida = datetime.now()
    visita.status = 'FINALIZADO'
    db.session.commit()
    
    # Notifica via WebSocket
    duracao = (visita.horario_saida - visita.horario_entrada).total_seconds() / 60
    visita_finalizada(visita_id, {
        'nome': visita.nome_visitante,
        'placa': visita.placa
    }, int(duracao))
    
    return jsonify({'status': 'finalizado'})

# ========== ROTAS PARA O PORTEIRO (Interfone) ==========

@app.route('/api/gerar_qr', methods=['POST'])
def gerar_qr():
    nova_visita = Visita(status='AGUARDANDO_CADASTRO')
    db.session.add(nova_visita)
    db.session.commit()
    
    # Notifica interfone via WebSocket (condomínio 1)
    qr_code_gerado(1, nova_visita.id, None)
    
    qr_data = f"http://{request.host}/?qr_id={nova_visita.id}"
    return jsonify({'qr_id': nova_visita.id, 'qr_data': qr_data})

@app.route('/api/qrcode/<int:qr_id>')
def gerar_qrcode_img(qr_id):
    qr_data = f"http://{request.host}/?qr_id={qr_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/api/visitas_ativas_porteiro')
def visitas_ativas_porteiro():
    visitas = Visita.query.filter(Visita.status.in_(['AGUARDANDO_MORADOR', 'EM_ROTA_ENTRADA', 'EM_ROTA_SAIDA'])).all()
    return jsonify([{
        'id': v.id,
        'nome': v.nome_visitante,
        'placa': v.placa,
        'destino': v.destino,
        'status': v.status,
        'latitude': v.latitude,
        'longitude': v.longitude
    } for v in visitas])

# ========== ROTAS PARA O MORADOR ==========

@app.route('/api/morador/visitas_pendentes/<token>')
def visitas_pendentes_morador(token):
    morador = Morador.query.filter_by(token=token).first_or_404()
    visitas = Visita.query.filter_by(morador_id=morador.id, status='AGUARDANDO_MORADOR').all()
    return jsonify([{
        'id': v.id,
        'nome': v.nome_visitante,
        'placa': v.placa,
        'destino': v.destino,
        'horario_entrada': v.horario_entrada.isoformat()
    } for v in visitas])

@app.route('/api/morador/liberar', methods=['POST'])
def liberar_visita():
    data = request.json
    visita_id = data.get('visita_id')
    token = data.get('token')
    morador = Morador.query.filter_by(token=token).first_or_404()
    visita = Visita.query.get_or_404(visita_id)
    if visita.morador_id != morador.id:
        return jsonify({'erro': 'Acesso negado'}), 403
    if visita.status == 'AGUARDANDO_MORADOR':
        visita.status = 'EM_ROTA_ENTRADA'
        db.session.commit()
        
        # Notifica via WebSocket (condomínio 1)
        visita_liberada(1, visita)
        
        return jsonify({'status': 'liberado'})
    return jsonify({'erro': 'Visita não está aguardando liberação'}), 400

@app.route('/api/morador/rejeitar', methods=['POST'])
def rejeitar_visita():
    data = request.json
    visita_id = data.get('visita_id')
    token = data.get('token')
    morador = Morador.query.filter_by(token=token).first_or_404()
    visita = Visita.query.get_or_404(visita_id)
    if visita.morador_id != morador.id:
        return jsonify({'erro': 'Acesso negado'}), 403
    if visita.status == 'AGUARDANDO_MORADOR':
        visita.status = 'REJEITADO'
        db.session.commit()
        
        # Notifica via WebSocket (condomínio 1)
        visita_rejeitada(1, visita)
        
        return jsonify({'status': 'rejeitado'})
    return jsonify({'erro': 'Visita não está aguardando rejeição'}), 400

# rota iniciar retorno
@app.route('/api/visita/<int:visita_id>/iniciar_retorno', methods=['POST'])
def iniciar_retorno(visita_id):
    visita = Visita.query.get_or_404(visita_id)
    if visita.status == 'EM_ROTA_ENTRADA':
        visita.status = 'EM_ROTA_SAIDA'
        db.session.commit()
        
        # Notifica via WebSocket (condomínio 1)
        retorno_iniciado(1, visita)
        
        return jsonify({'status': 'retorno iniciado'})
    return jsonify({'erro': 'Status inválido'}), 400

# ========== MOTOR DE GEOFENCING ==========

RAIO_PORTARIA_METROS = 30
RAIO_DESTINO_METROS = 20

def haversine(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371000
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    a = sin(delta_phi/2)**2 + cos(phi1)*cos(phi2)*sin(delta_lambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def verificar_geofence(visita):
    if not visita.latitude or not visita.longitude:
        return
    lat_portaria = -23.5490
    lon_portaria = -46.6320
    dist_portaria = haversine(visita.latitude, visita.longitude, lat_portaria, lon_portaria)
    
    morador = Morador.query.get(visita.morador_id) if visita.morador_id else None
    if morador and visita.status == 'EM_ROTA_ENTRADA':
        dist_destino = haversine(visita.latitude, visita.longitude, morador.latitude, morador.longitude)
        if dist_destino < RAIO_DESTINO_METROS:
            # Visitante chegou ao destino
            visitante_chegou_destino(visita.id, {
                'nome': visita.nome_visitante,
                'destino': visita.destino
            }, morador.id)
    
    elif visita.status == 'EM_ROTA_SAIDA':
        if dist_portaria < RAIO_PORTARIA_METROS:
            # Geofencing de saída acionado (condomínio 1)
            geofence_acionado(1, visita, tipo='saida', distancia=dist_portaria)
            
            # Finaliza automaticamente
            visita.status = 'FINALIZADO'
            visita.horario_saida = datetime.now()
            db.session.commit()
            
            duracao = (visita.horario_saida - visita.horario_entrada).total_seconds() / 60
            visita_finalizada(1, visita, motivo='geofence_saida')
            
            print(f"Visita {visita.id} finalizada automaticamente por geofencing.")

# ========== WEBHOOKS DE NOTIFICAÇÃO ==========

@app.route('/api/webhook/whatsapp_resposta', methods=['POST'])
def webhook_whatsapp_resposta():
    """
    Webhook que recebe respostas do WhatsApp via Twilio
    Processa: SIM, NÃO, ou qualquer resposta do morador
    """
    try:
        data = request.form
        from_number = data.get('From', '').replace('whatsapp:', '')  # Remove prefixo whatsapp:
        body = data.get('Body', '').strip().upper()
        message_id = data.get('MessageSid', '')
        
        print(f"\n[📬] Webhook WhatsApp recebido!")
        print(f"    De: {from_number}")
        print(f"    Resposta: {body}")
        print(f"    Msg ID: {message_id}")
        
        # Encontrar visita pendente de resposta deste morador
        morador = Morador.query.filter_by(telefone=from_number).first()
        if not morador:
            print(f"[⚠️] Morador não encontrado: {from_number}")
            return jsonify({'erro': 'Morador não encontrado'}), 404
        
        # Encontrar visita mais recente em espera
        visita = Visita.query.filter_by(
            morador_id=morador.id,
            status_whatsapp='NOTIFICADO'
        ).order_by(Visita.horario_notificacao_zap.desc()).first()
        
        if not visita:
            print(f"[⚠️] Nenhuma visita pendente para este morador")
            return jsonify({'erro': 'Nenhuma visita pendente'}), 404
        
        # Processar resposta
        NotificacaoService.resposta_morador(visita.id, body, socketio)
        
        # Responder ao WhatsApp (confirmar recebimento)
        TwilioResponse = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message>Sua resposta foi registrada. Obrigado!</Message>
        </Response>"""
        
        return TwilioResponse, 200, {'Content-Type': 'application/xml'}
        
    except Exception as e:
        print(f"[❌] Erro no webhook WhatsApp: {e}")
        return jsonify({'erro': str(e)}), 500


# ========== ROTAS DO PORTEIRO PARA CONTROLE MANUAL ==========

@app.route('/api/porteiro/liberar_visita', methods=['POST'])
def porteiro_liberar_visita():
    """Porteiro autoriza manualmente uma visita (caso morador não tenha respondido)"""
    data = request.json
    visita_id = data.get('visita_id')
    
    if NotificacaoService.autorizar_visita_porteiro(visita_id, socketio):
        return jsonify({'status': 'liberada'})
    else:
        return jsonify({'erro': 'Falha ao liberar visita'}), 400


@app.route('/api/porteiro/rejeitar_visita', methods=['POST'])
def porteiro_rejeitar_visita():
    """Porteiro rejeita manualmente uma visita"""
    data = request.json
    visita_id = data.get('visita_id')
    
    if NotificacaoService.rejeitar_visita_porteiro(visita_id, socketio):
        return jsonify({'status': 'rejeitada'})
    else:
        return jsonify({'erro': 'Falha ao rejeitar visita'}), 400


@app.route('/api/porteiro/visitas_aguardando', methods=['GET'])
def porteiro_visitas_aguardando():
    """Lista visitas que estão aguardando decisão do porteiro (morador não respondeu)"""
    visitas = Visita.query.filter_by(status_whatsapp='TIMEOUT').all()
    
    resultado = []
    for v in visitas:
        morador = Morador.query.get(v.morador_id) if v.morador_id else None
        resultado.append({
            'visita_id': v.id,
            'nome': v.nome_visitante,
            'placa': v.placa,
            'destino': v.destino,
            'morador': morador.nome if morador else 'Desconhecido',
            'tempo_espera': (datetime.now() - v.horario_entrada).total_seconds() / 60,
            'horario': v.horario_entrada.strftime('%H:%M:%S')
        })
    
    return jsonify(resultado)


if __name__ == '__main__':
    # In production or during automated tests we disable the reloader to avoid
    # dropping active socket connections when files change. Setting debug=False
    # also prevents Werkzeug from restarting the process.
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, use_reloader=False)
