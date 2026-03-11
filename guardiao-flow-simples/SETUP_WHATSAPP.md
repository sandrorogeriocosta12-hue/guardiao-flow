# 📱 Sistema WhatsApp com Fallback - Guia de Setup

## 🎯 Arquitetura

```
VISITANTE ESCANEIA QR
    ↓
PORTEIRO CRIA VISITA
    ↓
SISTEMA ENVIA WHATSAPP → MORADOR
    ↓
    ├─📱 MORADOR RESPONDE (SIM/NÃO)
    │  └─ Visita é LIBERADA ou REJEITADA ✅
    │
    └─⏰ MORADOR NÃO RESPONDE (30s timeout)
       └─ Visita vai pro PORTEIRO 👮
          ├─ PORTEIRO LIBERA (Manual)
          └─ PORTEIRO REJEITA (Manual)
```

---

## 🔧 Configuração do Twilio

### 1. Criar Conta Twilio

1. Acesse: [https://www.twilio.com/console](https://www.twilio.com/console)
2. Crie uma conta nova (ou use existente)
3. Confirme email + telefone

### 2. Ativar WhatsApp Sandbox

1. Dashboard → **WhatsApp** → **Sandbox**
2. Confira se está ativo (deve estar verde)
3. Você receberá um número tipo: `+14155238886`

### 3. Obter Credenciais

Na seção "Auth", copie:
- **Account SID** → `AC...`
- **Auth Token** → `abcd1234...`

### 4. Configurar Seu Número

1. No Sandbox WhatsApp, vá em **Senders**
2. Adicione seu número WhatsApp pessoal
3. Confirme a mensagem de verificação que chegará

### 5. Configurar Webhook

**IMPORTANTE:** O webhook só funciona com HTTPS em produção!

#### Para Desenvolvimento (Local com ngrok):

```bash
# 1. Instale ngrok: https://ngrok.com/download
# 2. Rode o servidor
python3 backend/app_websocket.py

# 3. Em outro terminal, execute:
ngrok http 5001

# 4. Você receberá algo como:
# Forwarding https://abc123.ngrok.io -> http://localhost:5001

# 5. Use isso no Twilio:
# https://abc123.ngrok.io/api/webhook/whatsapp_resposta
```

#### Para Produção (Railway):

```
https://seu-app.up.railway.app/api/webhook/whatsapp_resposta
```

**Para Configurar no Twilio:**
1. Dashboard → **Messaging** → **Settings**
2. Vá em **WhatsApp**
3. Em "Incoming Messages", coloque sua URL de webhook
4. Confirme que é POST
5. Salve

---

## 🌍 Variáveis de Ambiente

Crie um arquivo `.env` ou configure no Railway:

```bash
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Timeout (em segundos)
TIMEOUT_MORADOR=30
```

---

## 📊 Fluxo de Dados

### 1. Visitante Cria Visita

```
POST /api/iniciar_visita
{
    "qr_id": 123,
    "nome": "João Silva",
    "placa": "ABC-1234",
    "destino": "1719"
}
```

### 2. Sistema Envia WhatsApp

```python
NotificacaoService.notificar_morador(visita_id, socketio)
```

**Mensagem:**
```
🚗 *Nova Visita Aguardando!*

*Visitante:* João Silva
*Placa:* ABC-1234
*Destino:* Casa 1719
*Horário:* 14:30:00

Você autoriza esta visita?
Responda: *SIM* ou *NÃO*

(Você tem 30s para responder)
```

### 3. Morador Responde no WhatsApp

Escreve no WhatsApp:
- ✅ `SIM` → Visita LIBERADA
- ❌ `NÃO` → Visita REJEITADA

### 4. Webhook Recebe Resposta

```
POST /api/webhook/whatsapp_resposta
From: whatsapp:+5511999999999
Body: SIM
```

### 5. Sistema Processa

```python
NotificacaoService.resposta_morador(visita_id, "SIM", socketio)
```

---

## ⏰ Timeout em Ação

Se o morador **não responder em 30 segundos**:

1. Timer dispara
2. Visita muda status para `TIMEOUT`
3. WebSocket envia: `VISITA_AGUARDANDO_VERIFICACAO_PORTEIRO`
4. **Porteiro vê no Dashboard** e pode:
   - ✅ Liberar manualmente
   - ❌ Rejeitar manualmente

### Endpoints do Porteiro

```bash
# Ver visitas aguardando decisão
GET /api/porteiro/visitas_aguardando

# Liberar visita
POST /api/porteiro/liberar_visita
{"visita_id": 123}

# Rejeitar visita
POST /api/porteiro/rejeitar_visita
{"visita_id": 123}
```

---

## 🧪 Testar Localmente

### 1. Setup Completo

```bash
# Terminal 1: Servidor
cd guardiao-flow-simples
source /caminho/para/.venv/bin/activate
python3 -m backend.app_websocket

# Terminal 2: Ngrok (tunnel HTTPS)
ngrok http 5001
# Copie a URL https://...
```

### 2. Configurar .env

```bash
# Na raiz de guardiao-flow-simples/
export TWILIO_ACCOUNT_SID=ACxxxxx
export TWILIO_AUTH_TOKEN=xxxxx
export TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 3. Testar

```bash
# Terminal 3: Teste manual
curl -X POST http://localhost:5001/api/iniciar_visita \
  -H "Content-Type: application/json" \
  -d '{
    "qr_id": 1,
    "nome": "João",
    "placa": "ABC-1234",
    "destino": "1719"
  }'

# Você receberá WhatsApp em seu celular!
# Responda: SIM ou NÃO
# O sistema processará automaticamente
```

### 4. Monitorar Logs

```bash
# Ver logs em tempo real
tail -f guardiao-flow-simples/logs/monitor.log
```

---

## 🚀 Deploy no Railway

### 1. Configurar Variáveis

No Railway Dashboard:
1. **Settings** → **Variables**
2. Adicione:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_NUMBER`
   - `TIMEOUT_MORADOR=30`

### 2. Update railway.json

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python3 -m backend.app_websocket",
    "restartPolicyMaxRetries": 5,
    "restartPolicyWindowMs": 60000
  }
}
```

### 3. Update Webhook no Twilio

Mude a URL de:
```
https://abc123.ngrok.io/api/webhook/whatsapp_resposta
```

Para:
```
https://seu-app.up.railway.app/api/webhook/whatsapp_resposta
```

---

## 📊 Estados da Visita

| Status | Significado |
|--------|-----------|
| `AGUARDANDO_CADASTRO` | Visitante escaneou QR, aguardando dados |
| `AGUARDANDO_MORADOR` | Dados preenchidos, WhatsApp enviado |
| `NOTIFICADO` | WhatsApp foi enviado para morador |
| `SIM` | Morador respondeu SIM |
| `NAO` | Morador respondeu NÃO |
| `TIMEOUT` | Morador não respondeu, aguardando porteiro |
| `AUTORIZADO_PORTEIRO` | Porteiro liberou manualmente |
| `REJEITADO_PORTEIRO` | Porteiro rejeitou manualmente |
| `LIBERADA` | Visita foi liberada |
| `REJEITADA` | Visita foi rejeitada |
| `EM_ROTA_ENTRADA` | Visitante em rota de entrada (GPS) |
| `CHEGOU_DESTINO` | Visitante chegou no destino |
| `EM_ROTA_SAIDA` | Visitante deixando condomínio |
| `FINALIZADO` | Visita finalizada |

---

## 🔍 Troubleshooting

### ❌ WhatsApp não é enviado

**Causa:** Credenciais não configuradas

```bash
# Verificar:
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN
echo $TWILIO_WHATSAPP_NUMBER
```

### ❌ Webhook não recebe respostas

**Causa:** URL não está configurada ou ngrok caiu

```bash
# Restart ngrok:
ngrok http 5001

# Update Twilio com nova URL
```

### ❌ Timeout não funciona

**Causa:** Threads não estão rodando

```bash
# Verificar logs:
tail -f guardiao-flow-simples/logs/monitor.log | grep TIMEOUT
```

### ❌ Visita não muda de status

**Causa:** Banco de dados corrompido ou ID errado

```bash
# Resetar:
rm guardiao-flow-simples/database.db
python3 -m backend.app_websocket
```

---

## 📝 Exemplo de Integração Completa

```python
from backend.notificacao_service import NotificacaoService
from backend.database import db
from backend.models import Visita, Morador

# 1. Visitante preenche dados
visita = Visita(
    nome_visitante="João Silva",
    placa="ABC-1234",
    destino="1719",
    morador_id=1
)
db.session.add(visita)
db.session.commit()

# 2. Sistema envia WhatsApp (com timeout automático)
NotificacaoService.notificar_morador(visita.id, socketio)

# 3. Se morador responder (webhook):
# NotificacaoService.resposta_morador(visita.id, "SIM", socketio)

# 4. Se timeout (30s):
# NotificacaoService.mover_para_porteiro(visita.id, socketio)

# 5. Porteiro autoriza manualmente:
# NotificacaoService.autorizar_visita_porteiro(visita.id, socketio)
```

---

## 📚 Referências

- [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp)
- [Webhook Docs](https://www.twilio.com/docs/sms/tutorials/how-to-receive-and-reply-python-flask)
- [ngrok Documentation](https://ngrok.com/docs)

---

**Status:** ✅ Pronto para Produção

Sistema de notificação WhatsApp com fallback automático totalmente integrado!
