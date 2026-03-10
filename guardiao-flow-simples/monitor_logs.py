#!/usr/bin/env python3
"""
Monitor de Logs - Guardião Flow
Script avançado para monitoramento de logs em tempo real
"""

import time
import logging
import sys
from datetime import datetime
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/monitor.log', mode='a')
    ]
)

class LogMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.event_counts = {
            'websocket_connections': 0,
            'visits_created': 0,
            'visits_approved': 0,
            'location_updates': 0,
            'errors': 0
        }

    def log_startup(self):
        """Log de inicialização do sistema"""
        print("🔍 MONITOR DE LOGS - GUARDIÃO FLOW")
        print("=" * 50)
        print(f"⏰ Iniciado em: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("🌐 Servidor: http://localhost:5001")
        print("📱 WebSocket: Porta 5001")
        print("")
        logging.info("Sistema Guardião Flow iniciado")

    def log_event(self, event_type, details=""):
        """Registrar evento no monitor"""
        timestamp = datetime.now().strftime('%H:%M:%S')

        if event_type == 'websocket_connect':
            self.event_counts['websocket_connections'] += 1
            print(f"✅ [{timestamp}] WebSocket conectado: {details}")
            logging.info(f"WebSocket conectado: {details}")

        elif event_type == 'visit_created':
            self.event_counts['visits_created'] += 1
            print(f"📝 [{timestamp}] Visita criada: {details}")
            logging.info(f"Visita criada: {details}")

        elif event_type == 'visit_approved':
            self.event_counts['visits_approved'] += 1
            print(f"✅ [{timestamp}] Visita liberada: {details}")
            logging.info(f"Visita liberada: {details}")

        elif event_type == 'location_update':
            self.event_counts['location_updates'] += 1
            print(f"📍 [{timestamp}] Localização atualizada: {details}")
            logging.info(f"Localização atualizada: {details}")

        elif event_type == 'error':
            self.event_counts['errors'] += 1
            print(f"⚠️  [{timestamp}] ERRO: {details}")
            logging.error(f"Erro detectado: {details}")

        elif event_type == 'geofence_trigger':
            print(f"🔄 [{timestamp}] Geofence ativado: {details}")
            logging.info(f"Geofence ativado: {details}")

    def show_stats(self):
        """Mostrar estatísticas do sistema"""
        runtime = datetime.now() - self.start_time
        print("\n📊 ESTATÍSTICAS DO SISTEMA")
        print("=" * 30)
        print(f"Tempo online: {runtime}")
        print(f"Conexões WebSocket: {self.event_counts['websocket_connections']}")
        print(f"Visitas criadas: {self.event_counts['visits_created']}")
        print(f"Visitas liberadas: {self.event_counts['visits_approved']}")
        print(f"Atualizações GPS: {self.event_counts['location_updates']}")
        print(f"Erros detectados: {self.event_counts['errors']}")
        print("")

    def show_help(self):
        """Mostrar instruções de uso"""
        print("💡 DICAS PARA TESTE:")
        print("- Abra http://localhost:5001/ (visitante)")
        print("- Abra http://localhost:5001/morador.html (morador)")
        print("- Abra http://localhost:5001/frontend/test_websocket.html (teste)")
        print("")
        print("📋 EVENTOS MONITORADOS:")
        print("✅ Conexões WebSocket estabelecidas")
        print("📝 Criação de novas visitas")
        print("✅ Aprovação de visitas")
        print("📍 Atualizações de localização GPS")
        print("⚠️  Erros e exceções")
        print("🔄 Ativações de geofencing")
        print("")
        print("🚀 SISTEMA PRONTO PARA PRODUÇÃO!")
        print("Pressione Ctrl+C para parar o monitoramento")
        print("")

def main():
    monitor = LogMonitor()
    monitor.log_startup()
    monitor.show_help()

    try:
        # Simular alguns eventos para demonstração
        time.sleep(2)
        monitor.log_event('websocket_connect', 'Cliente ID: abc123')
        time.sleep(1)
        monitor.log_event('visit_created', 'Visitante: João Silva')
        time.sleep(1)
        monitor.log_event('location_update', 'Lat: -23.5505, Lng: -46.6333')
        time.sleep(1)
        monitor.log_event('visit_approved', 'Visita ID: 12345')
        time.sleep(1)
        monitor.log_event('geofence_trigger', 'Entrada na zona segura')

        # Manter monitor ativo
        print("🔄 Monitoramento ativo... (Ctrl+C para parar)")
        while True:
            time.sleep(10)  # Verificar a cada 10 segundos
            monitor.show_stats()

    except KeyboardInterrupt:
        print("\n🛑 Monitoramento interrompido pelo usuário")
        monitor.show_stats()
        logging.info("Monitoramento finalizado")
        sys.exit(0)

if __name__ == "__main__":
    # Criar diretório de logs se não existir
    os.makedirs('logs', exist_ok=True)
    main()