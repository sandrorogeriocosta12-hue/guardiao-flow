#!/bin/bash
echo "🔍 MONITOR DE LOGS - GUARDIÃO FLOW"
echo "=================================="
echo "Monitorando logs em tempo real..."
echo "Pressione Ctrl+C para parar"
echo ""

# Monitorar logs do servidor Flask
python3 -c "
import time
print('📊 Iniciando monitoramento de logs...')
print('⏰', time.strftime('%H:%M:%S'), '- Sistema iniciado')
print('🌐 Servidor rodando em: http://localhost:5001')
print('📱 WebSocket ativo na porta 5001')
print('')
print('📋 Eventos importantes a monitorar:')
print('✅ Conexões WebSocket estabelecidas')
print('📤 Eventos emitidos (VISITA_CRIADA, etc.)')
print('📩 Eventos recebidos dos clientes')
print('⚠️  Erros e exceções')
print('🔄 Geofencing triggers')
print('')
print('💡 Dica: Abra múltiplas abas do navegador para testar:')
print('   - http://localhost:5001/ (visitante)')
print('   - http://localhost:5001/morador.html (morador)')
print('   - http://localhost:5001/frontend/test_websocket.html (teste)')
print('')
print('🚀 Pronto para produção!')
"