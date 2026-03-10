import os
import qrcode
import uuid
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from .database import db
from .models import Visita, Morador

app = Flask(__name__, static_folder='../frontend', static_url_path='')
# permite servir html/js/css diretamente do diretório frontend
CORS(app)

@app.route('/')
def root():
    return app.send_static_file('index.html')

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

# ========== Rotas Públicas / Visitante ==========

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

    # enviar WhatsApp avisando morador que existe visitante aguardando liberação
    if morador and morador.telefone:
        try:
            from .whatsapp_bot import send_whatsapp
            link = f"http://{request.host}/morador.html?token={morador.token}"
            body = (
                f"Olá {morador.nome}, você tem um visitante aguardando: "
                f"{visita.nome_visitante} ({visita.placa}) para a casa {visita.destino}. "
                f"Acesse {link} para liberar."
            )
            send_whatsapp(morador.telefone, body)
        except Exception as e:
            print("Erro enviando WhatsApp:", e)
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
        verificar_geofence(visita)
    return jsonify({'status': 'ok'})

@app.route('/api/finalizar_visita/<int:visita_id>', methods=['POST'])
def finalizar_visita(visita_id):
    visita = Visita.query.get_or_404(visita_id)
    visita.horario_saida = datetime.now()
    visita.status = 'FINALIZADO'
    db.session.commit()
    return jsonify({'status': 'finalizado'})

# ========== Rotas para o Porteiro (Interfone) ==========

@app.route('/api/gerar_qr', methods=['POST'])
def gerar_qr():
    nova_visita = Visita(status='AGUARDANDO_CADASTRO')
    db.session.add(nova_visita)
    db.session.commit()
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

# ========== Rotas para o Morador ==========

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
        return jsonify({'status': 'liberado'})
    return jsonify({'erro': 'Visita não está aguardando liberação'}), 400

# rota iniciar retorno
@app.route('/api/visita/<int:visita_id>/iniciar_retorno', methods=['POST'])
def iniciar_retorno(visita_id):
    visita = Visita.query.get_or_404(visita_id)
    if visita.status == 'EM_ROTA_ENTRADA':
        visita.status = 'EM_ROTA_SAIDA'
        db.session.commit()
        return jsonify({'status': 'retorno iniciado'})
    return jsonify({'erro': 'Status inválido'}), 400

# ========== Motor de Geofencing ==========

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
    if visita.status == 'EM_ROTA_ENTRADA':
        pass
    elif visita.status == 'EM_ROTA_SAIDA':
        if dist_portaria < RAIO_PORTARIA_METROS:
            visita.status = 'FINALIZADO'
            visita.horario_saida = datetime.now()
            db.session.commit()
            print(f"Visita {visita.id} finalizada automaticamente por geofencing.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
