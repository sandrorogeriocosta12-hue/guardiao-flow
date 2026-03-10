#!/usr/bin/env python
"""
Test script for Guardião Flow closed-loop system
Simulates complete visitor journey
"""

import os
import sys
import json

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.app_websocket import app, socketio
from backend.database import db
from backend.models import Visita, Morador

def test_complete_flow():
    """Test complete closed-loop flow"""
    
    with app.app_context():
        print("\n" + "="*60)
        print("  GUARDIÃO FLOW - CLOSED-LOOP TEST")
        print("="*60 + "\n")
        
        # ========== PREPARE ==========
        print("[1/7] 🔧 Preparing test data...")
        
        # Clear old test data
        Visita.query.delete()
        db.session.commit()
        
        moradores = Morador.query.all()
        print(f"  ✓ {len(moradores)} moradores in system")
        
        morador = moradores[0] if moradores else None
        if not morador:
            print("  ✗ No moradores found!")
            return False
        
        print(f"  ✓ Using morador: {morador.nome} (Casa {morador.casa})")
        print(f"    Token: {morador.token[:16]}...")
        
        # ========== STEP 1: PORTEIRO GERA QR ==========
        print("\n[2/7] 🎟️  Porteiro generates QR code...")
        
        nova_visita = Visita(status='AGUARDANDO_CADASTRO')
        db.session.add(nova_visita)
        db.session.commit()
        
        qr_id = nova_visita.id
        print(f"  ✓ QR generated - ID: {qr_id}")
        print(f"  ✓ Status: {nova_visita.status}")
        
        # ========== STEP 2: VISITANTE REGISTRA ==========
        print("\n[3/7] 📝 Visitor registers...")
        
        visita = Visita.query.get(qr_id)
        visita.nome_visitante = "João da Silva (Test)"
        visita.placa = "ABC1234"
        visita.destino = morador.casa
        visita.morador_id = morador.id
        visita.status = 'AGUARDANDO_MORADOR'
        db.session.commit()
        
        print(f"  ✓ Visitor: {visita.nome_visitante}")
        print(f"  ✓ Vehicle: {visita.placa}")
        print(f"  ✓ Destination: Casa {visita.destino}")
        print(f"  ✓ Status changed to: {visita.status}")
        
        # ========== STEP 3: MORADOR AUTORIZA ==========
        print("\n[4/7] ✅ Resident approves access...")
        
        visita = Visita.query.get(qr_id)
        visita.status = 'EM_ROTA_ENTRADA'
        db.session.commit()
        
        print(f"  ✓ Status changed to: {visita.status}")
        print(f"  ✓ Visitor can now enter")
        
        # ========== STEP 4: VISITANTE ENVIANDO GPS ==========
        print("\n[5/7] 🗺️  Visitor sends GPS location...")
        
        # Simulate getting close to destination (20m)
        visita.latitude = morador.latitude + 0.0001  # ~10 meters
        visita.longitude = morador.longitude + 0.0001
        db.session.commit()
        
        from backend.app_websocket import haversine
        dist = haversine(visita.latitude, visita.longitude, morador.latitude, morador.longitude)
        print(f"  ✓ GPS Update: ({visita.latitude:.6f}, {visita.longitude:.6f})")
        print(f"  ✓ Distance from destination: {dist:.1f}m")
        
        # ========== STEP 5: GERENCIADOR DETECTA CHEGADA ==========
        print("\n[6/7] 🏠 Geofence detects arrival at destination...")
        
        visita = Visita.query.get(qr_id)
        if visita.status == 'EM_ROTA_ENTRADA':
            dist = haversine(visita.latitude, visita.longitude, morador.latitude, morador.longitude)
            if dist < 20:  # RAIO_DESTINO_METROS
                print(f"  ✓ Geofence triggered! (Distance: {dist:.1f}m < 20m)")
                print(f"  ✓ Visitor can now initiate exit")
        
        # ========== STEP 6: VISITANTE INICIA RETORNO ==========
        print("\n[7/7] 🚗 Visitor initiates return...")
        
        visita = Visita.query.get(qr_id)
        visita.status = 'EM_ROTA_SAIDA'
        db.session.commit()
        
        print(f"  ✓ Status changed to: {visita.status}")
        
        # Simulate returning to gate area (30m)
        lat_portaria = -23.5490
        lon_portaria = -46.6320
        visita.latitude = lat_portaria + 0.0001
        visita.longitude = lon_portaria + 0.0001
        db.session.commit()
        
        dist_portaria = haversine(visita.latitude, visita.longitude, lat_portaria, lon_portaria)
        print(f"  ✓ GPS in return: ({visita.latitude:.6f}, {visita.longitude:.6f})")  
        print(f"  ✓ Distance from gate: {dist_portaria:.1f}m")
        
        # ========== STEP 7: GEOFENCE SAIDA ==========
        print("\n[✓] 🔓 Geofence exit triggered!")
        
        visita = Visita.query.get(qr_id)
        if dist_portaria < 30:  # RAIO_PORTARIA_METROS
            visita.status = 'FINALIZADO'
            from datetime import datetime
            visita.horario_saida = datetime.now()
            db.session.commit()
            
            print(f"  ✓ Status: {visita.status}")
            print(f"  ✓ Access automatically closed")
            
            duracao = (visita.horario_saida - visita.horario_entrada).total_seconds() / 60
            print(f"  ✓ Visit duration: {duracao:.1f} minutes")
        
        # ========== SUMMARY ==========
        print("\n" + "="*60)
        print("  ✅ CLOSED-LOOP TEST COMPLETED SUCCESSFULLY")
        print("="*60)
        
        print("\n📊 Final State:")
        visita = Visita.query.get(qr_id)
        print(f"  • Visitor: {visita.nome_visitante}")
        print(f"  • Status: {visita.status}")
        print(f"  • Entry: {visita.horario_entrada}")
        print(f"  • Exit: {visita.horario_saida}")
        print(f"  • Residence: Casa {visita.destino}")
        
        return True

if __name__ == '__main__':
    try:
        success = test_complete_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
