"""
Bot WhatsApp integrado com Twilio
- Envia mensagens de notificação
- Recebe respostas via webhook
- Gerencia comunicação em tempo real
"""

import os
from twilio.rest import Client

# Configuração via variáveis de ambiente
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # ex: whatsapp:+14155238886

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

print("""
╔════════════════════════════════════════════════════════════╗
║         🤖 GUARDIÃO FLOW - BOT WHATSAPP 🤖               ║
╚════════════════════════════════════════════════════════════╝

📋 CONFIGURAÇÃO TWILIO:
""")

if TWILIO_ACCOUNT_SID:
    print(f"  ✅ Account SID: {TWILIO_ACCOUNT_SID[:10]}...")
else:
    print("  ❌ Account SID não configurado")

if TWILIO_AUTH_TOKEN:
    print(f"  ✅ Auth Token: {TWILIO_AUTH_TOKEN[:10]}...")
else:
    print("  ❌ Auth Token não configurado")

if TWILIO_WHATSAPP_NUMBER:
    print(f"  ✅ WhatsApp Número: {TWILIO_WHATSAPP_NUMBER}")
else:
    print("  ❌ WhatsApp Número não configurado")

print("""
🔧 WEBHOOK CONFIGURATION:
  Endpoint: https://seu-app.com/api/webhook/whatsapp_resposta
  
📱 COMO CONFIGURAR NO TWILIO:
  1. Acesse: https://console.twilio.com
  2. Sandbox WhatsApp → Configurações
  3. Webhook URL: http://seu-host/api/webhook/whatsapp_resposta
  4. POST - Salvar
""")

def send_whatsapp(to_number: str, body: str):
    """
    Envia mensagem WhatsApp para o número informado.
    
    Args:
        to_number: Número com código de país, ex: '+5511999999999'
        body: Texto da mensagem
        
    Returns:
        message_sid: ID da mensagem se sucesso, None se falha
        
    Exemplos:
        send_whatsapp('+5511999999999', 'Olá! Você tem um visitante.')
    """
    
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        print("[⚠️] Credenciais Twilio não configuradas!")
        print("   Variáveis necessárias:")
        print("   - TWILIO_ACCOUNT_SID")
        print("   - TWILIO_AUTH_TOKEN")
        print("   - TWILIO_WHATSAPP_NUMBER")
        return None
    
    try:
        msg = client.messages.create(
            body=body,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{to_number}"
        )
        
        print(f"[✅] WhatsApp enviado!")
        print(f"    Para: {to_number}")
        print(f"    Msg ID: {msg.sid}")
        print(f"    Status: {msg.status}")
        
        return msg.sid
        
    except Exception as e:
        print(f"[❌] Erro ao enviar WhatsApp: {e}")
        return None


def formatar_mensagem_visita(visita, morador_nome: str = ""):
    """
    Formata mensagem padronizada para notificação de visita
    """
    return f"""
🚗 *VISITANTE AGUARDANDO!*

👤 *Visitante:* {visita.get('nome')}
🏎️ *Placa:* {visita.get('placa') or 'Não informada'}
🏠 *Casa:* {visita.get('destino')}
⏰ *Horário:* {visita.get('horario')}

Você autoriza esta visita?

Responda: *SIM* ou *NÃO*
    """.strip()

