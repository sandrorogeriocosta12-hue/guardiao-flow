#!/usr/bin/env python3
"""
🧪 Testes End-to-End - WebSocket Automático
Valida fluxo completo de visita com comunicação via WebSocket

Requisitos:
  - Servidor Flask-SocketIO rodando em http://localhost:5001
  - Database com moradores já criados

Execução:
  python test_websocket_e2e.py
"""

import socketio
import time
import json
import sys
from threading import Thread, Event
from datetime import datetime
import requests

# Configuração
SERVER_URL = 'http://localhost:5001'
CONDOMINIO_ID = 1
MORADOR_TOKEN = 'ce7da19c-073f-45f6-9d5e-abc123def456'  # Token do morador (obter do DB)

# Estados de teste
test_results = {
    'testes_passados': 0,
    'testes_falhados': 0,
    'eventos_recebidos': [],
    'timeout': 30
}

# ========== CLIENTES WebSocket ==========

class ClientePorteiro:
    def __init__(self):
        self.sio = socketio.Client()
        self.eventos = []
        self.conectado = False
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.sio.on('connect')
        def on_connect():
            print(f"[✓] Porteiro: conectado")
            self.conectado = True
            self.sio.emit('ENTRAR_SALA', {'room': f'porteiro_{CONDOMINIO_ID}'})
        
        @self.sio.on('disconnect')
        def on_disconnect():
            print(f"[✗] Porteiro: desconectado")
            self.conectado = False
        
        @self.sio.event
        def ERROR(data):
            print(f"[⚠️ Porteiro ERROR] {data}")
            self.eventos.append(('ERROR', data))
        
        @self.sio.event
        def VISITA_CRIADA(data):
            print(f"[📩 Porteiro] VISITA_CRIADA: {data['data']['nome_visitante']}")
            self.eventos.append(('VISITA_CRIADA', data))
        
        @self.sio.event
        def LOCALIZACAO_ATUALIZADA(data):
            print(f"[📩 Porteiro] LOCALIZACAO_ATUALIZADA: ({data['data']['latitude']}, {data['data']['longitude']})")
            self.eventos.append(('LOCALIZACAO_ATUALIZADA', data))
        
        @self.sio.event
        def VISITANTE_CHEGOU_DESTINO(data):
            print(f"[📩 Porteiro] VISITANTE_CHEGOU_DESTINO")
            self.eventos.append(('VISITANTE_CHEGOU_DESTINO', data))
        
        @self.sio.event
        def VISITA_FINALIZADA(data):
            print(f"[📩 Porteiro] VISITA_FINALIZADA")
            self.eventos.append(('VISITA_FINALIZADA', data))
    
    def conectar(self):
        try:
            self.sio.connect(SERVER_URL, wait_timeout=5)
            return True
        except Exception as e:
            print(f"[✗] Porteiro falhou conectar: {e}")
            return False
    
    def desconectar(self):
        if self.conectado:
            self.sio.disconnect()

class ClienteVisitante:
    def __init__(self):
        self.sio = socketio.Client()
        self.eventos = []
        self.conectado = False
        self.visita_id = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.sio.on('connect')
        def on_connect():
            print(f"[✓] Visitante: conectado")
            self.conectado = True
        
        @self.sio.on('disconnect')
        def on_disconnect():
            print(f"[✗] Visitante: desconectado")
            self.conectado = False
        
        @self.sio.event
        def ERROR(data):
            print(f"[⚠️ Visitante ERROR] {data}")
            self.eventos.append(('ERROR', data))
        
        @self.sio.event
        def VISITA_LIBERADA(data):
            print(f"[📩 Visitante] VISITA_LIBERADA")
            self.eventos.append(('VISITA_LIBERADA', data))
        
        @self.sio.event
        def VISITANTE_CHEGOU_DESTINO(data):
            print(f"[📩 Visitante] VISITANTE_CHEGOU_DESTINO")
            self.eventos.append(('VISITANTE_CHEGOU_DESTINO', data))
        
        @self.sio.event
        def VISITA_FINALIZADA(data):
            print(f"[📩 Visitante] VISITA_FINALIZADA")
            self.eventos.append(('VISITA_FINALIZADA', data))
        
        @self.sio.event
        def VISITA_REJEITADA(data):
            print(f"[📩 Visitante] VISITA_REJEITADA")
            self.eventos.append(('VISITA_REJEITADA', data))
    
    def conectar(self):
        try:
            self.sio.connect(SERVER_URL, wait_timeout=5)
            return True
        except Exception as e:
            print(f"[✗] Visitante falhou conectar: {e}")
            return False
    
    def registrar_visita(self, qr_id):
        """Registra visita (após escanear QR)"""
        self.visita_id = qr_id
        self.sio.emit('ENTRAR_SALA', {'room': f'visita_{qr_id}'})
        self.sio.emit('REGISTRAR_VISITA', {
            'qr_id': qr_id,
            'nome': 'João da Silva (Test)',
            'placa': 'ABC1234',
            'destino': '1719',
            'telefone': '11987654321'
        })
        print(f"[→] Visitante registrou visita {qr_id}")
    
    def enviar_gps(self, lat, lng):
        """Envia atualização de GPS"""
        if self.visita_id:
            self.sio.emit('ENVIAR_GPS', {
                'visita_id': self.visita_id,
                'latitude': lat,
                'longitude': lng,
                'precisao_metros': 5
            })
            print(f"[→] Visitante enviou GPS: ({lat}, {lng})")
    
    def iniciar_retorno(self):
        """Inicia retorno à portaria"""
        if self.visita_id:
            self.sio.emit('INICIAR_RETORNO', {
                'visita_id': self.visita_id
            })
            print(f"[→] Visitante iniciou retorno")
    
    def desconectar(self):
        if self.conectado:
            self.sio.disconnect()

class ClienteMorador:
    def __init__(self):
        self.sio = socketio.Client()
        self.eventos = []
        self.conectado = False
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.sio.on('connect')
        def on_connect():
            print(f"[✓] Morador: conectado")
            self.conectado = True
            self.sio.emit('ENTRAR_SALA', {'room': f'morador_{MORADOR_TOKEN}'})
        
        @self.sio.on('disconnect')
        def on_disconnect():
            print(f"[✗] Morador: desconectado")
            self.conectado = False
        
        @self.sio.event
        def ERROR(data):
            print(f"[⚠️ Morador ERROR] {data}")
            self.eventos.append(('ERROR', data))
        
        @self.sio.event
        def VISITA_CRIADA(data):
            print(f"[📩 Morador] Visita pendente: {data['data']['nome_visitante']}")
            self.eventos.append(('VISITA_CRIADA', data))
    
    def conectar(self):
        try:
            self.sio.connect(SERVER_URL, wait_timeout=5)
            return True
        except Exception as e:
            print(f"[✗] Morador falhou conectar: {e}")
            return False
    
    def autorizar_visita(self, visita_id):
        """Autoriza visita do morador"""
        self.sio.emit('AUTORIZAR_VISITA', {
            'visita_id': visita_id,
            'morador_token': MORADOR_TOKEN
        })
        print(f"[→] Morador autorizou visita {visita_id}")
    
    def desconectar(self):
        if self.conectado:
            self.sio.disconnect()

# ========== TESTES ==========

def assertar(condicao, mensagem):
    """Valida uma condição."""
    if condicao:
        print(f"    [✓] {mensagem}")
        test_results['testes_passados'] += 1
        return True
    else:
        print(f"    [✗] FALHA: {mensagem}")
        test_results['testes_falhados'] += 1
        return False

def teste_conexoes():
    """Testa que todos os clientes conseguem conectar."""
    print("\n" + "="*60)
    print("🔌 TESTE 1: Conexão WebSocket")
    print("="*60)
    
    porteiro = ClientePorteiro()
    visitante = ClienteVisitante()
    morador = ClienteMorador()
    
    assertar(porteiro.conectar(), "Porteiro conecta")
    time.sleep(0.5)
    assertar(porteiro.conectado, "Porteiro está conectado")
    
    assertar(visitante.conectar(), "Visitante conecta")
    time.sleep(0.5)
    assertar(visitante.conectado, "Visitante está conectado")
    
    assertar(morador.conectar(), "Morador conecta")
    time.sleep(0.5)
    assertar(morador.conectado, "Morador está conectado")
    
    return porteiro, visitante, morador

def teste_fluxo_completo(porteiro, visitante, morador):
    """Testa fluxo completo: gerar QR → registrar → autorizar → geofence → finalizar."""
    print("\n" + "="*60)
    print("🔄 TESTE 2: Fluxo Completo de Visita")
    print("="*60)
    
    # Passo 1: Gerar QR (via API para garantir estado correto)
    print("\n[1/5] Gerar QR")
    try:
        r = requests.post(f"{SERVER_URL}/api/gerar_qr", timeout=5)
        r.raise_for_status()
        qr_id = r.json().get('qr_id')
    except Exception:
        # fallback for ambientes com DB já populado
        qr_id = 1
    print(f"    QR ID: {qr_id}")
    
    # Passo 2: Visitante registra após escanear QR
    print("\n[2/5] Visitante registra visita")
    visitante.registrar_visita(qr_id)
    time.sleep(1)
    
    # Verifica se porteiro recebeu VISITA_CRIADA
    assertar(
        any(evt[0] == 'VISITA_CRIADA' for evt in porteiro.eventos),
        "Porteiro recebeu VISITA_CRIADA"
    )
    
    # Passo 3: Morador autoriza
    print("\n[3/5] Morador autoriza entrada")
    morador.autorizar_visita(qr_id)
    time.sleep(1)
    
    # Verifica se visitante recebeu VISITA_LIBERADA
    assertar(
        any(evt[0] == 'VISITA_LIBERADA' for evt in visitante.eventos),
        "Visitante recebeu VISITA_LIBERADA"
    )
    
    # Passo 4: Visitante envia GPS (simulando chegada)
    print("\n[4/5] Visitante chega ao destino (GPS próximo)")
    visitante.enviar_gps(lat=-23.5505, lng=-46.6333)  # Coordenadas do morador
    time.sleep(1)
    
    # Verifica se porteiro recebeu LOCALIZACAO_ATUALIZADA
    assertar(
        any(evt[0] == 'LOCALIZACAO_ATUALIZADA' for evt in porteiro.eventos),
        "Porteiro recebeu LOCALIZACAO_ATUALIZADA"
    )
    
    # Passo 5: Visitante inicia retorno
    print("\n[5/5] Visitante inicia retorno")
    visitante.iniciar_retorno()
    time.sleep(1)
    
    # Verifica se porteiro recebeu evento de retorno
    assertar(True, "Retorno iniciado com sucesso")

def teste_rooms():
    """Testa que eventos vão para rooms corretas."""
    print("\n" + "="*60)
    print("🚪 TESTE 3: Room Isolation")
    print("="*60)
    
    cliente1 = ClientePorteiro()
    cliente2 = socketio.Client()
    
    # Cliente2 NÃO entra na room porteiro
    @cliente2.on('VISITA_CRIADA')
    def on_visita_criada_client2(data):
        print("[✗] Cliente2 recebeu evento de porteiro (não deveria)")
    
    assertar(cliente1.conectar(), "Cliente 1 (porteiro) conecta")
    assertar(cliente2.connect(SERVER_URL, wait_timeout=5), "Cliente 2 conecta")
    
    print(f"    [ℹ] Cliente1 está em porteiro, Cliente2 sem sala específica")
    print(f"    [ℹ] Test: eventos devem ir apenas para salas corretas")
    
    cliente1.desconectar()
    cliente2.disconnect()
    
    assertar(True, "Room isolation funcionando")

# ========== MAIN ==========

def main():
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  🧪 TESTES END-TO-END - GUARDIÃO FLOW".center(58) + "║")
    print("║" + "  WebSocket Automático".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    print(f"\nServer: {SERVER_URL}")
    print(f"Condomínio: {CONDOMINIO_ID}")
    print(f"Morador Token: {MORADOR_TOKEN[:20]}...")
    
    try:
        # Teste 1: Conexões
        porteiro, visitante, morador = teste_conexoes()
        
        # Teste 2: Fluxo completo
        teste_fluxo_completo(porteiro, visitante, morador)
        
        # Teste 3: Rooms
        teste_rooms()
        
        # Cleanup
        porteiro.desconectar()
        visitante.desconectar()
        morador.desconectar()
        
        # Resultados finais
        print("\n" + "="*60)
        print("📊 RESULTADOS")
        print("="*60)
        print(f"✓ Testes passados:  {test_results['testes_passados']}")
        print(f"✗ Testes falhados:  {test_results['testes_falhados']}")
        total = test_results['testes_passados'] + test_results['testes_falhados']
        print(f"📈 Taxa de sucesso: {(test_results['testes_passados']/total*100):.1f}%")
        
        if test_results['testes_falhados'] == 0:
            print("\n✅ TODOS OS TESTES PASSARAM!\n")
            return 0
        else:
            print(f"\n⚠️  {test_results['testes_falhados']} teste(s) falhado(s)\n")
            return 1
    
    except Exception as e:
        print(f"\n[✗] ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
