import os
from twilio.rest import Client

# configuração via variáveis de ambiente
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # ex: whatsapp:+14155238886

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp(to_number: str, body: str):
    """Envia mensagem WhatsApp para o número informado.
    `to_number` deve incluir código de país, ex '+5511999999999'.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_NUMBER:
        print("[whatsapp_bot] credenciais não configuradas, pulando envio")
        return None

    msg = client.messages.create(
        body=body,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f"whatsapp:{to_number}"
    )
    return msg.sid
