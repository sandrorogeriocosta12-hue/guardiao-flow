# 📡 WebSocket Payloads - Especificação Completa

## Overview
Comunicação em tempo real entre backend Flask-SocketIO e 4 tipos de clientes via WebSocket usando Socket.IO protocol.

---

## 🔄 Estrutura de Rooms (Salas)

```
porteiro_[condominio_id]        → Dashboard do porteiro
interfone_[condominio_id]       → Tablet no interfone
visita_[visita_id]              → Visitante em rota
morador_[morador_token]         → Morador no app/browser
```

---

## 📨 Eventos do Servidor → Clientes

### 1. `QR_CODE_GERADO`
**Destinatário:** `interfone_*`, `porteiro_*`
**Descrição:** QR Code criado e pronto para exibição
```json
{
  "qr_id": 1,
  "qr_url": "http://localhost:5001/?qr_id=1",
  "qr_image_base64": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "expira_em_segundos": 120,
  "gerado_em": "2026-03-04T12:00:00Z"
}
```

### 2. `VISITA_CRIADA`
**Destinatário:** `porteiro_*`
**Descrição:** Nova visita registrada no sistema
```json
{
  "visita_id": 1,
  "nome_visitante": "João da Silva",
  "placa": "ABC1234",
  "destino": "Casa 1719",
  "status": "AGUARDANDO_CADASTRO",
  "horario_entrada": "2026-03-04T12:00:00Z",
  "morador_id": 1,
  "morador_nome": "João Silva"
}
```

### 3. `VISITA_LIBERADA`
**Destinatário:** `visita_*`, `porteiro_*`
**Descrição:** Morador aprovou entrada do visitante
```json
{
  "visita_id": 1,
  "status": "EM_ROTA_ENTRADA",
  "morador_nome": "João Silva",
  "autorizado_em": "2026-03-04T12:01:00Z",
  "mapa_destino": {
    "nome": "Casa 1719",
    "latitude": -23.5505,
    "longitude": -46.6333,
    "geofence_raio_metros": 20
  }
}
```

### 4. `LOCALIZACAO_ATUALIZADA`
**Destinatário:** `porteiro_*`
**Descrição:** GPS do visitante atualizado (enviado a cada ~10s)
```json
{
  "visita_id": 1,
  "latitude": -23.5510,
  "longitude": -46.6335,
  "precisao_metros": 5,
  "timestamp": "2026-03-04T12:02:00Z",
  "distancia_destino_metros": 250,
  "status": "EM_ROTA_ENTRADA"
}
```

### 5. `VISITANTE_CHEGOU_DESTINO`
**Destinatário:** `visita_*`, `morador_*`, `porteiro_*`
**Descrição:** Geofence acionado na chegada ao destino
```json
{
  "visita_id": 1,
  "evento": "chegada",
  "latitude": -23.5505,
  "longitude": -46.6333,
  "distancia_final_metros": 15,
  "timestamp": "2026-03-04T12:05:00Z",
  "mensagem": "Visitante chegou ao destino. Portão será aberto automaticamente."
}
```

### 6. `RETORNO_INICIADO`
**Destinatário:** `porteiro_*`, `morador_*`
**Descrição:** Visitante iniciou retorno para portaria
```json
{
  "visita_id": 1,
  "status": "EM_ROTA_SAIDA",
  "timestamp": "2026-03-04T12:15:00Z",
  "iniciado_por": "visitante",
  "mensagem": "Visitante iniciando retorno à portaria"
}
```

### 7. `GEOFENCE_ACIONADO`
**Destinatário:** `porteiro_*`, `visita_*`
**Descrição:** Visitante cruzou portaria (saída ou entrada confirmada)
```json
{
  "visita_id": 1,
  "tipo": "saida",
  "latitude": -23.5480,
  "longitude": -46.6320,
  "distancia_portaria_metros": 28,
  "timestamp": "2026-03-04T12:20:00Z",
  "mensagem": "Visitante saindo do condomínio - Acesso finalizado"
}
```

### 8. `VISITA_FINALIZADA`
**Destinatário:** `visitante_*`, `porteiro_*`, `morador_*`
**Descrição:** Visita encerrada (por saída de geofence ou timeout)
```json
{
  "visita_id": 1,
  "status": "FINALIZADO",
  "nome_visitante": "João da Silva",
  "horario_entrada": "2026-03-04T12:00:00Z",
  "horario_saida": "2026-03-04T12:20:00Z",
  "duracao_minutos": 20,
  "motivo": "geofence_saida",
  "timestamp": "2026-03-04T12:20:05Z"
}
```

### 9. `VISITA_REJEITADA`
**Destinatário:** `visita_*`, `porteiro_*`
**Descrição:** Morador recusou entrada do visitante
```json
{
  "visita_id": 1,
  "status": "REJEITADA",
  "recusada_por": "João Silva",
  "motivo": "Não foi autorizado",
  "timestamp": "2026-03-04T12:01:30Z",
  "mensagem_visitante": "Sua entrada foi recusada. Por favor, contate o morador."
}
```

### 10. `NOTIFICACAO_WHATSAPP_ENVIADA`
**Destinatário:** `morador_*`
**Descrição:** WhatsApp enviado ao morador com link de aprovação
```json
{
  "visita_id": 1,
  "telefone": "11999999999",
  "timestamp": "2026-03-04T12:00:05Z",
  "status_envio": "enviado",
  "link_aprovacao": "http://localhost:5001/morador.html?token=abc123",
  "mensagem": "Nova visita aguardando autorização"
}
```

---

## 🔵 Eventos Clientes → Servidor

### 1. `REGISTRAR_VISITA`
**Origem:** Visitante (após escanear QR)
**Descrição:** Registra dados do visitante
```json
{
  "qr_id": 1,
  "nome": "João da Silva",
  "placa": "ABC1234",
  "destino": "Casa 1719",
  "telefone": "11987654321"
}
```
**Resposta esperada:** `VISITA_CRIADA` (broadcast)

### 2. `AUTORIZAR_VISITA`
**Origem:** Morador (botão Liberar)
**Descrição:** Aprova entrada do visitante
```json
{
  "visita_id": 1,
  "morador_token": "ce7da19c-073f-45f6-9d5e-abc123def456",
  "timestamp": "2026-03-04T12:01:00Z"
}
```
**Resposta esperada:** `VISITA_LIBERADA` (broadcast)

### 3. `REJEITAR_VISITA`
**Origem:** Morador (botão Recusar)
**Descrição:** Recusa entrada do visitante
```json
{
  "visita_id": 1,
  "morador_token": "ce7da19c-073f-45f6-9d5e-abc123def456",
  "motivo": "Não foi autorizado",
  "timestamp": "2026-03-04T12:01:00Z"
}
```
**Resposta esperada:** `VISITA_REJEITADA` (broadcast)

### 4. `ENVIAR_GPS`
**Origem:** Visitante (continuamente durante rota)
**Descrição:** Atualiza posição GPS
```json
{
  "visita_id": 1,
  "latitude": -23.5510,
  "longitude": -46.6335,
  "precisao_metros": 5,
  "timestamp": "2026-03-04T12:02:00Z"
}
```
**Resposta esperada:** `LOCALIZACAO_ATUALIZADA` (para porteiro) ou `VISITANTE_CHEGOU_DESTINO` (se geofence acionado)

### 5. `INICIAR_RETORNO`
**Origem:** Visitante (botão Sair)
**Descrição:** Visitante inicia retorno à portaria
```json
{
  "visita_id": 1,
  "timestamp": "2026-03-04T12:15:00Z"
}
```
**Resposta esperada:** `RETORNO_INICIADO` (broadcast)

### 6. `ENTRAR_SALA`
**Origem:** Qualquer cliente
**Descrição:** Conecta cliente a uma room específica
```json
{
  "room": "visita_1",
  "cliente_tipo": "visitante",
  "timestamp": "2026-03-04T12:00:00Z"
}
```
**Efeito:** Cliente passa a receber eventos daquela room

### 7. `SAIR_SALA`
**Origem:** Qualquer cliente
**Descrição:** Desconecta cliente de uma room
```json
{
  "room": "visita_1",
  "timestamp": "2026-03-04T12:25:00Z"
}
```

### 8. `PING`
**Origem:** Qualquer cliente (keepalive)
**Descrição:** Verifica conectividade
```json
{
  "timestamp": "2026-03-04T12:00:00Z"
}
```
**Resposta esperada:** `PONG`

---

## 🔐 Autenticação via Room

**Visitante** se conecta a: `visita_{id}` (já sabe o ID do QR)
**Morador** se conecta a: `morador_{token}` (token enviado via WhatsApp)
**Porteiro** se conecta a: `porteiro_{condominio_id}` (autenticado via login)
**Interfone** se conecta a: `interfone_{condominio_id}` (sem auth, apenas broadcast)

---

## 📊 Fluxo de Estados e Eventos

```
1. PORTEIRO: clica "Gerar QR"
   ↓
   Backend: cria Visita(status=AGUARDANDO_CADASTRO)
   ↓
   Broadcast: QR_CODE_GERADO → interfone
   Broadcast: VISITA_CRIADA → porteiro

2. VISITANTE: escaneia QR e preenche formulário
   ↓
   Emit: REGISTRAR_VISITA → servidor
   ↓
   Backend: atualiza Visita(status=AGUARDANDO_MORADOR)
   ↓
   Broadcast: VISITA_CRIADA → porteiro
   WhatsApp: envia link para morador

3. MORADOR: recebe WhatsApp e abre link
   ↓
   Emit: AUTORIZAR_VISITA → servidor
   ↓
   Backend: atualiza Visita(status=EM_ROTA_ENTRADA)
   ↓
   Broadcast: VISITA_LIBERADA → visitante, porteiro

4. VISITANTE: recebe aprovação e vê mapa de rota
   ↓
   Emit: ENVIAR_GPS (continuamente)
   ↓
   Backend: recebe GPS, calcula distance, checa geofence
   ↓
   Broadcast: LOCALIZACAO_ATUALIZADA → porteiro
   Se geofence < 20m: VISITANTE_CHEGOU_DESTINO

5. VISITANTE: clica botão "Sair"
   ↓
   Emit: INICIAR_RETORNO → servidor
   ↓
   Backend: atualiza Visita(status=EM_ROTA_SAIDA)
   ↓
   Broadcast: RETORNO_INICIADO → porteiro, morador

6. GPS monitoring (check geofence saída)
   ↓
   Se distance > 30m da portaria:
   ↓
   Broadcast: GEOFENCE_ACIONADO → porteiro, visitante
   Backend: atualiza Visita(status=FINALIZADO)
   Broadcast: VISITA_FINALIZADA → todos

7. FINAL
   Visitante reconhecido como saído
   Acesso encerrado automaticamente
```

---

## 🧪 Exemplo de Teste - Fluxo Completo

```
Timing: 0:00 - Porteiro gera QR (5s)
         ↓
Timing: 0:05 - Visitante escaneia, preenche form (15s)
         ↓
Timing: 0:20 - Morador recebe WhatsApp com link (5s)
         ↓
Timing: 0:25 - Morador clica "Liberar" (2s)
         ↓
Timing: 0:27 - Visitante autorizado, vê mapa (5-60s viagem)
         ↓
Timing: 1:00 - Visitante chega, geofence acionado (5s)
         ↓
Timing: 1:05 - Visitante clica "Sair" (10s viagem de volta)
         ↓
Timing: 1:15 - Geofence saída acionado, acesso finalizado
         ↓
Total: ~75 segundos
```

---

## 🛠️ Implementação no Cliente (JavaScript)

```javascript
const socket = io('http://localhost:5001');

// Conectar e entrar na room
socket.on('connect', () => {
  socket.emit('ENTRAR_SALA', { room: `visita_${visitaId}` });
});

// Ouvir eventos do servidor
socket.on('VISITA_LIBERADA', (data) => {
  console.log('Aprovado! Dados:', data);
  mostrarMapa(data.mapa_destino);
});

socket.on('VISITANTE_CHEGOU_DESTINO', (data) => {
  console.log('Chegou ao destino!', data);
});

socket.on('VISITA_FINALIZADA', (data) => {
  console.log('Visita finalizada', data);
  socket.disconnect();
});

// Enviar GPS
function enviarGPS(lat, lng, precisao) {
  socket.emit('ENVIAR_GPS', {
    visita_id: visitaId,
    latitude: lat,
    longitude: lng,
    precisao_metros: precisao,
    timestamp: new Date().toISOString()
  });
}

// Iniciar retorno
function iniciarRetorno() {
  socket.emit('INICIAR_RETORNO', {
    visita_id: visitaId,
    timestamp: new Date().toISOString()
  });
}

// Keepalive
setInterval(() => {
  socket.emit('PING', { timestamp: new Date().toISOString() });
}, 30000);
```

---

## 📋 Checklist de Implementação

- [ ] Backend emite `QR_CODE_GERADO` com base64 da imagem
- [ ] Backend emite `VISITA_CRIADA` ao registrar visitante
- [ ] Backend ouve `REGISTRAR_VISITA` e atualiza status
- [ ] Backend ouve `AUTORIZAR_VISITA` e emite `VISITA_LIBERADA`
- [ ] Cliente visitante ouve `VISITA_LIBERADA` e mostra mapa
- [ ] Visitante emite `ENVIAR_GPS` continuamente
- [ ] Backend calcula geofence e emite `VISITANTE_CHEGOU_DESTINO`
- [ ] Visitante pode clicar "Sair" e emitir `INICIAR_RETORNO`
- [ ] Backend monitora geofence de saída
- [ ] Backend emite `VISITA_FINALIZADA` ao detectar saída
- [ ] Morador ouve eventos em tempo real
- [ ] Porteiro dashboard atualiza em tempo real
- [ ] Todos os eventos têm timestamp
- [ ] Sistema trata desconexões gracefully
- [ ] Rate limiting em GPS updates (máx 1/segundo)

