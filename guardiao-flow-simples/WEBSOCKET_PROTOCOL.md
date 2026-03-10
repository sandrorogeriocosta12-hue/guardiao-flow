"""
GUARDIÃO FLOW - WEBSOCKET MESSAGE PROTOCOL
==========================================

Toda comunicação em tempo real entre Backend, Interfone, Visitante e Morador
usa este protocolo JSON padronizado via WebSocket.

O Backend é o "maestro" - envia eventos que sincronizam todas as telas.

NAMESPACES (Salas):
- 'porteiro': Dashboard do porteiro/guarita
- 'interfone': Tela do interfone (QR dinâmico)
- 'visitante_<visita_id>': Rastreamento do visitante específico
- 'morador_<morador_id>': Notificações do morador
- 'admin': Logs e monitoramento geral

====================================================================
PARTE 1: EVENTOS DO BACKEND (Emit - envia para os clientes)
====================================================================

1. EVENTO: QR_CODE_GERADO
   Quando porteiro clica em "Gerar Acesso"
   
   Destinatário: 'interfone'
   Payload:
   {
     "event": "QR_CODE_GERADO",
     "data": {
       "qr_id": 123,
       "qr_data": "http://192.168.1.10:5001/?qr_id=123",
       "expires_in": 120,
       "timestamp": "2026-03-04T10:30:00Z"
     }
   }

---

2. EVENTO: VISITA_CRIADA
   Quando visitante preenche formulário
   
   Destinatário: 'porteiro', 'morador_<morador_id>'
   Payload:
   {
     "event": "VISITA_CRIADA",
     "data": {
       "visita_id": 456,
       "nome_visitante": "João Silva",
       "placa": "ABC1234",
       "destino": "Casa 1719",
       "morador_id": 2,
       "morador_nome": "Carlos",
       "status": "AGUARDANDO_MORADOR",
       "timestamp": "2026-03-04T10:30:30Z",
       "qr_id": 123
     }
   }

---

3. EVENTO: VISITANTE_AGUARDANDO
   Estado contínuo enquanto aguarda liberação
   
   Destinatário: 'porteiro', 'morador_<morador_id>'
   Payload:
   {
     "event": "VISITANTE_AGUARDANDO",
     "data": {
       "visita_id": 456,
       "nome": "João Silva",
       "destino": "Casa 1719",
       "tempo_espera": 45,
       "status": "AGUARDANDO_MORADOR"
     }
   }

---

4. EVENTO: VISITA_LIBERADA
   Quando morador clica em "Liberar"
   
   Destinatário: 'visitante_456', 'porteiro', 'interfone'
   Payload:
   {
     "event": "VISITA_LIBERADA",
     "data": {
       "visita_id": 456,
       "nome": "João Silva",
       "status": "EM_ROTA_ENTRADA",
       "rota": {
         "origem": { "lat": -23.5490, "lng": -46.6320 },
         "destino": { "lat": -23.5505, "lng": -46.6333, "casa": "1719" },
         "pontos_interesse": []
       },
       "timestamp": "2026-03-04T10:31:00Z"
     }
   }

---

5. EVENTO: LOCALIZACAO_ATUALIZADA
   GPS em tempo real (a cada 10-15 segundos)
   
   Destinatário: 'porteiro', 'visitante_456' (feedback)
   Payload:
   {
     "event": "LOCALIZACAO_ATUALIZADA",
     "data": {
       "visita_id": 456,
       "latitude": -23.5495,
       "longitude": -46.6325,
       "accuracy": 8.5,
       "velocidade": 0,
       "timestamp": "2026-03-04T10:31:30Z",
       "geofence_status": "DENTRO_CONDOMINIO"
     }
   }

---

6. EVENTO: VISITANTE_CHEGOU_DESTINO
   Quando GPS detecta geofence de 20m ao redor da casa
   
   Destinatário: 'visitante_456', 'porteiro', 'morador_2'
   Payload:
   {
     "event": "VISITANTE_CHEGOU_DESTINO",
     "data": {
       "visita_id": 456,
       "nome": "João Silva",
       "casa": "1719",
       "status": "AGUARDANDO_SAIDA",
       "timestamp": "2026-03-04T10:32:00Z",
       "latitude": -23.5505,
       "longitude": -46.6333
     }
   }

---

7. EVENTO: RETORNO_INICIADO
   Quando visitante clica em "Iniciar Saída"
   
   Destinatário: 'visitante_456', 'porteiro', 'morador_2'
   Payload:
   {
     "event": "RETORNO_INICIADO",
     "data": {
       "visita_id": 456,
       "status": "EM_ROTA_SAIDA",
       "destino_saida": { "lat": -23.5490, "lng": -46.6320 },
       "timestamp": "2026-03-04T10:33:00Z"
     }
   }

---

8. EVENTO: GEOFENCE_ACIONADO
   Visitante cruzou a cerca virtual de 30m da portaria
   
   Destinatário: 'visitante_456', 'porteiro', 'morador_2'
   Payload:
   {
     "event": "GEOFENCE_ACIONADO",
     "data": {
       "visita_id": 456,
       "tipo": "SAIDA",
       "raio": 30,
       "latitude": -23.5490,
       "longitude": -46.6320,
       "timestamp": "2026-03-04T10:34:00Z"
     }
   }

---

9. EVENTO: VISITA_FINALIZADA
   Acesso encerrado automaticamente
   
   Destinatário: 'visitante_456', 'porteiro', 'morador_2'
   Payload:
   {
     "event": "VISITA_FINALIZADA",
     "data": {
       "visita_id": 456,
       "nome": "João Silva",
       "duracao_minutos": 5,
       "status": "FINALIZADO",
       "motivo": "GEOFENCE_SAIDA",
       "timestamp": "2026-03-04T10:34:30Z"
     }
   }

---

10. EVENTO: VISITA_REJEITADA
    Quando morador clica em "Recusar"
    
    Destinatário: 'visitante_456', 'porteiro', 'interfone'
    Payload:
    {
      "event": "VISITA_REJEITADA",
      "data": {
        "visita_id": 456,
        "motivo": "MORADOR_RECUSOU",
        "timestamp": "2026-03-04T10:31:15Z"
      }
    }

---

====================================================================
PARTE 2: EVENTOS DO CLIENTE (On - cliente faz uma ação)
====================================================================

1. EVENTO: CLIENTE_CONECTOU
   Cliente se conecta ao WebSocket
   
   Origem: Cliente
   Payload:
   {
     "event": "CLIENTE_CONECTOU",
     "data": {
       "tipo": "porteiro" | "interfone" | "visitante" | "morador",
       "id_sessao": "abc123",
       "visita_id": 456,  // se visitante ou morador
       "morador_id": 2,   // se morador
       "token": "xyz789"  // se morador
     }
   }

---

2. EVENTO: GERAR_QR (Porteiro)
   
   Origem: Porteiro clica botão
   Payload:
   {
     "event": "GERAR_QR",
     "data": {
       "timestamp": "2026-03-04T10:30:00Z"
     }
   }
   
   Resposta do Backend: QR_CODE_GERADO

---

3. EVENTO: REGISTRAR_VISITA (Visitante)
   
   Origem: Visitante preenche formulário
   Payload:
   {
     "event": "REGISTRAR_VISITA",
     "data": {
       "qr_id": 123,
       "nome": "João Silva",
       "placa": "ABC1234",
       "destino": "Casa 1719"
     }
   }
   
   Resposta do Backend: VISITA_CRIADA

---

4. EVENTO: ENVIAR_GPS (Visitante)
   
   Origem: GPS do navegador (a cada 10s)
   Payload:
   {
     "event": "ENVIAR_GPS",
     "data": {
       "visita_id": 456,
       "latitude": -23.5495,
       "longitude": -46.6325,
       "accuracy": 8.5,
       "velocidade": 0,
       "timestamp": "2026-03-04T10:31:30Z"
     }
   }
   
   Resposta do Backend: LOCALIZACAO_ATUALIZADA (broadcast)

---

5. EVENTO: AUTORIZAR_VISITA (Morador)
   
   Origem: Morador clica "Liberar"
   Payload:
   {
     "event": "AUTORIZAR_VISITA",
     "data": {
       "visita_id": 456,
       "token": "ce7da19c-073f-4535-822c-c9d03e996564",
       "acao": "LIBERAR",
       "timestamp": "2026-03-04T10:31:00Z"
     }
   }
   
   Resposta do Backend: VISITA_LIBERADA (broadcast)

---

6. EVENTO: REJEITAR_VISITA (Morador)
   
   Origem: Morador clica "Recusar"
   Payload:
   {
     "event": "REJEITAR_VISITA",
     "data": {
       "visita_id": 456,
       "token": "ce7da19c-073f-4535-822c-c9d03e996564",
       "acao": "RECUSAR",
       "timestamp": "2026-03-04T10:31:00Z"
     }
   }
   
   Resposta do Backend: VISITA_REJEITADA (broadcast)

---

7. EVENTO: INICIAR_RETORNO (Visitante)
   
   Origem: Visitante clica botão "Iniciar Saída"
   Payload:
   {
     "event": "INICIAR_RETORNO",
     "data": {
       "visita_id": 456,
       "timestamp": "2026-03-04T10:33:00Z"
     }
   }
   
   Resposta do Backend: RETORNO_INICIADO (broadcast)

---

8. EVENTO: CLIENTE_DESCONECTOU
   
   Origem: Cliente fecha página ou sai
   Payload:
   {
     "event": "CLIENTE_DESCONECTOU",
     "data": {
       "visita_id": 456,
       "tipo": "visitante",
       "timestamp": "2026-03-04T10:35:00Z"
     }
   }

---

====================================================================
PARTE 3: FLUXO COMPLETO DE UMA VISITA
====================================================================

T0:00 - Porteiro clica "Gerar Acesso"
  └─> Porteiro envia: GERAR_QR
  └─> Backend emite para 'interfone': QR_CODE_GERADO

T0:01 - Interfone exibe QR grande e dinâmico

T0:05 - Visitante escaneia QR e preenche dados
  └─> Visitante envia: REGISTRAR_VISITA
  └─> Backend emite para 'porteiro', 'morador_2': VISITA_CRIADA
  └─> Status agora: AGUARDANDO_MORADOR

T0:06 - Backend envia WhatsApp para morador com link

T0:10 - Morador recebe notificação via WhatsApp

T0:15 - Morador abre link e se conecta
  └─> Morador envia: CLIENTE_CONECTOU
  └─> Backend carrega visitas pendentes

T0:20 - Morador clica "Liberar"
  └─> Morador envia: AUTORIZAR_VISITA
  └─> Backend valida token e autoriza
  └─> Backend emite para 'visitante_456': VISITA_LIBERADA
  └─> Status agora: EM_ROTA_ENTRADA

T0:21 - Tela do visitante muda e mostra mapa com rota

T0:22 - Visitante começa a enviar GPS contínuamente
  └─> Visitante envia: ENVIAR_GPS (a cada 10s)
  └─> Backend emite para 'porteiro': LOCALIZACAO_ATUALIZADA

T0:45 - Visitante chega próximo à Casa 1719
  └─> Backend detecta geofence de 20m
  └─> Backend emite: VISITANTE_CHEGOU_DESTINO
  └─> Status agora: AGUARDANDO_SAIDA
  └─> Tela do visitante ativa botão "Iniciar Saída"

T1:00 - Visitante clica "Iniciar Saída"
  └─> Visitante envia: INICIAR_RETORNO
  └─> Backend emite: RETORNO_INICIADO
  └─> Status agora: EM_ROTA_SAIDA
  └─> Tela mostra novo mapa: destino = portaria

T1:10 - Visitante sai e GPS continua ativo

T1:20 - Visitante cruza a cerca virtual de 30m na portaria
  └─> Backend detecta geofence de saída
  └─> Backend emite: GEOFENCE_ACIONADO
  └─> Backend desativa rastreamento

T1:21 - Backend finaliza visita automaticamente
  └─> Backend emite para 'visitante_456', 'porteiro': VISITA_FINALIZADA
  └─> Status agora: FINALIZADO
  └─> Tela do visitante desativa GPS e mostra "Acesso Encerrado"
  └─> Histórico porteiro atualiza

====================================================================
PARTE 4: ESTRUTURA DO CLIENTE VISITANTE (State-Based)
====================================================================

Estados (status) da máquina de estado:

[QR_SCANNED]  ->  [FORMULARIO]  ->  [AGUARDANDO_MORADOR]
                                            ↓
[RECUSADO] <-                          [LIBERADO_ENTRADA]
                                            ↓
                                      [EM_ROTA_ENTRADA]
                                            ↓
                                      [CHEGOU_DESTINO]
                                            ↓
                                      [AGUARDANDO_SAIDA]
                                            ↓
                                      [EM_ROTA_SAIDA]
                                            ↓
                                      [GEOFENCE_SAIDA]
                                            ↓
                                      [FINALIZADO]

Cada estado renderiza um componente diferente:
- QR_SCANNED: Spinner
- FORMULARIO: Form de entrada (nome, placa, destino)
- AGUARDANDO_MORADOR: Clock com contador de espera
- LIBERADO_ENTRADA: Button "Iniciar", depois mapa aparece
- EM_ROTA_ENTRADA: Mapa com rota, marcador em movimento
- CHEGOU_DESTINO: Button "Iniciar Saída"
- EM_ROTA_SAIDA: Mapa com rota de volta
- GEOFENCE_SAIDA: Spinner "Encerrando..."
- FINALIZADO: "Acesso Encerrado. Obrigado!"

====================================================================
"""
