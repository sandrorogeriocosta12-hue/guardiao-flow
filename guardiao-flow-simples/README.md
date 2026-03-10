# Guardião Flow - Sistema de Controle de Acesso Inteligente

## 🎯 Overview

Guardião Flow é um **sistema de controle de acesso de ponta a ponta completo** com ciclo fechado (closed-loop), Web Sockets em tempo real, geofencing automático e integração WhatsApp.

### Arquitetura do Sistema

O sistema é orquestrado por **Flask-SocketIO** que atua como "maestro", sincronizando em tempo real:

1. **Porteiro (Dashboard)** - Gera QR codes dinamicamente
2. **Interfone (Tablet)** - Exibe QR code gigante
3. **Visitante (Navegador)** - Escaneia QR, preenche dados, segue rota com GPS
4. **Morador (Link via WhatsApp)** - Aprova ou rejeita acesso com um clique

---

## 🏗️ Arquitetura Técnica

### Stack

- **Backend:** Flask 2.3 + Flask-SocketIO + SQLAlchemy ORM
- **Frontend:** HTML5 + Leaflet Maps + Vanilla JavaScript
- **Database:** SQLite3
- **Notificações:** Twilio WhatsApp API
- **Localização:** HTML5 Geolocation API + Haversine Geofencing
- **Tempo Real:** WebSockets (Socket.IO)

### Estrutura de Arquivos

```
guardiao-flow-simples/
├── backend/
│   ├── __init__.py                 # Exports app + socketio
│   ├── app.py                      # Rotas REST (mantido para compatibilidade)
│   ├── app_websocket.py            # App com Flask-SocketIO (USAR ESTE)
│   ├── database.py                 # SQLAlchemy setup
│   ├── models.py                   # Modelos: Visita, Morador, etc
│   ├── websocket_manager.py        # Gerenciador de eventos WebSocket
│   ├── whatsapp_bot.py             # Integração Twilio
│   └── requirements.txt            # Dependências Python
├── frontend/
│   ├── index.html                  # Tela do Visitante (multi-estado)
│   ├── morador.html                # Tela do Morador (aprovação)
│   ├── monitor.html                # Tela do Porteiro (dashboard)
│   ├── interfone.html              # Tela do Interfone (QR dinâmico)
│   └── script.js                   # Compartilhado (antigo, não usar)
├── WEBSOCKET_PROTOCOL.md           # Documento completo do protocolo
└── database.db                     # SQLite (criado automaticamente)
```

---

## 🚀 Como Usar

### 1. Instalação de Dependências

```bash
cd backend
pip install -r requirements.txt
```

Certifique-se de ter:
- `Flask-SocketIO==5.3.5`
- `python-socketio==5.9.0`
- `twilio==8.10.0`

### 2. Variáveis de Ambiente (Opcional - para WhatsApp)

```bash
export TWILIO_ACCOUNT_SID="seu_account_sid"
export TWILIO_AUTH_TOKEN="seu_auth_token"
export TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"
```

### 3. Executar o Sistema

**Opção A: Use o app_websocket.py (RECOMENDADO - com WebSockets)**

```bash
cd backend
python -c "from app_websocket import app, socketio; socketio.run(app, host='0.0.0.0', port=5001, debug=True)"
```

Ou configure no seu IDE para rodar:
```bash
python app_websocket.py
```

**Opção B: Use o app.py original (sem WebSockets em tempo real)**

```bash
cd backend
python app.py
```

### 4. Acessar as Telas

| Tela | URL | Descrição |
|------|-----|-----------|
| **Visitante** | `http://localhost:5001/` | Escaneia QR e registra |
| **Porteiro** | `http://localhost:5001/monitor.html` | Dashboard de controle |
| **Interfone** | `http://localhost:5001/interfone.html` | Tablet na guarita |
| **Morador** | `http://localhost:5001/morador.html?token=xxx` | Link da notificação WhatsApp |

---

## 📱 Fluxo Completo de Uma Visita (Closed-Loop)

### Fase 1: Preparação (T0:00 a T0:05)

1. **Porteiro** abre `monitor.html`
2. Clica em **"+ Gerar QR"**
3. API cria novo registro de `Visita` com `status='AGUARDANDO_CADASTRO'`
4. WebSocket emite `QR_CODE_GERADO` para a sala `'interfone'`
5. **Interfone** na tela recebe via Socket.IO e exibe QR grande

### Fase 2: Registro (T0:06 a T0:20)

1. **Visitante** aponta celular para a tela do interfone
2. Abre `index.html?qr_id=123`
3. Preenche: Nome, Placa, Destino (Casa 1719)
4. Clica "Solicitar Entrada"
5. Backend:
   - Valida QR
   - Atualiza status para `AGUARDANDO_MORADOR`
   - Identifica morador pelo destino
   - **Envia WhatsApp** com link de autorização
   - Emite `VISITA_CRIADA` para porteiro e morador

### Fase 3: Aprovação (T0:21 a T0:30)

1. **Morador** recebe notificação WhatsApp
2. Clica no link: `morador.html?token=abc123xyz`
3. Tela carrega visitas **aguardando autorização**
4. Morador vê: Nome, Placa, Casa
5. Clica **"Liberar"** ou **"Recusar"**
6. Backend:
   - Valida token
   - Atualiza status para `EM_ROTA_ENTRADA` ou `REJEITADO`
   - Emite `VISITA_LIBERADA` ou `VISITA_REJEITADA`

### Fase 4: Entrada com Rota (T0:31 a T1:00)

1. **Visitante** vê mapa com rota: Portaria → Casa 1719
2. Inicia rastreamento GPS automático
3. A cada 10 segundos:
   - Celular envia: `{lat, lng, accuracy}`
   - Backend processa geofencing
   - **Porteiro** vê marcador se movendo no mapa em tempo real
4. Quando fica a 20m da casa:
   - Backend detecta geofence
   - Emite `VISITANTE_CHEGOU_DESTINO`
   - Tela do visitante ativa botão **"Iniciar Saída"**

### Fase 5: Retorno (T1:01 a T1:30)

1. **Visitante** clica **"Iniciar Saída"**
2. Mapa muda para rota inversa: Casa 1719 → Portaria
3. Continua enviando GPS
4. Quando fica a 30m da portaria:
   - Backend detecta geofence de SAÍDA
   - Emite `GEOFENCE_ACIONADO`
   - **Finaliza automaticamente** o acesso
   - Status: `FINALIZADO`

### Fase 6: Encerramento (T1:31+)

1. **Visitante** vê: ✓ "Acesso Encerrado. Obrigado!"
2. GPS é desativado (economiza bateria)
3. **Porteiro** vê visita sair do painel "Ativos" e ir para "Histórico"
4. Visita registrada no banco de dados

---

## 🔌 Protocolo WebSocket

Consulte `WEBSOCKET_PROTOCOL.md` para:

- **Estrutura completa** de payloads JSON
- **Nomeclatura de eventos** (VISITA_CRIADA, LOCALIZACAO_ATUALIZADA, etc)
- **Salas (Rooms)** para diferentes tipos de usuário
- **Máquina de estado** do visitante (6 estados)

### Eventos Principais

```
Cliente                  Backend

Porteiro:
  GERAR_QR      →→→     
                         QR_CODE_GERADO  →→→ Interfone
                
Visitante:
  REGISTRAR_VISITA →→→
                         VISITA_CRIADA   →→→ Porteiro + Morador
                         
Morador:
  AUTORIZAR_VISITA →→→
                         VISITA_LIBERADA →→→ Visitante + Porteiro
                         
Visitante (GPS):
  ENVIAR_GPS ⟲⟲⟲        (a cada 10s)
                         LOCALIZACAO_ATUALIZADA →→→ Porteiro
                         [Geofence Check]
                         VISITANTE_CHEGOU_DESTINO
```

---

## 📊 Estado do Visitante (State Machine)

Cada tela do visitante renderiza baseado no status:

```
Status da Visita          Tela do Visitante            Ações

AGUARDANDO_CADASTRO  →   [Tela 1: Formulário]        Preencher dados
AGUARDANDO_MORADOR   →   [Tela 2: Relógio]            Aguardar ⏳
REJEITADO            →   [Tela Erro]                  Acesso Negado ✕
EM_ROTA_ENTRADA      →   [Tela Mapa 1]               Navegar para casa
AGUARDANDO_SAIDA     →   ["Iniciar Saída" btn]       Prontos para sair
EM_ROTA_SAIDA        →   [Tela Mapa 2]               Navegar para portaria
GEOFENCE_SAIDA       →   [Spinner]                   Encerrando... ⟲
FINALIZADO           →   [Tela Final]                ✓ Acesso Encerrado
```

---

## 🗄️ Modelos de Dados

### Tabela `visitas`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | PK |
| `nome_visitante` | String | Nome do visitante |
| `placa` | String | Placa do veículo |
| `destino` | String | Casa de destino (ex: "1719") |
| `morador_id` | Integer | FK para morador que autorizou |
| `status` | String | Estado do ciclo de vida |
| `horario_entrada` | DateTime | Quando registrou |
| `horario_saida` | DateTime | Quando saiu |
| `latitude` | Float | Posição GPS atual |
| `longitude` | Float | Posição GPS atual |
| `ultima_atualizacao` | DateTime | Último GPS recebido |

### Tabela `moradores`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | PK |
| `nome` | String | Nome do morador |
| `telefone` | String | +5511999999999 (para WhatsApp) |
| `email` | String | Email de contato |
| `casa` | String | Número da casa (ex: "1719") |
| `latitude` | Float | Coordenada GPS da casa |
| `longitude` | Float | Coordenada GPS da casa |
| `token` | String | UUID único para acesso sem login |

---

## 🎨 Componentes Frontend

### Tela do Visitante (`index.html`)

- **Multiestado:** Une QR scanner, formulário, mapa e confirmação
- **Gerenciamento GPS:** Ativa/desativa automático baseado no status
- **Animações:** Transições suaves entre telas
- **Offline-safe:** Rota básica salva em cache

### Tela do Morador (`morador.html`)

- **Notificação bonita:** Toast notifications em tempo real
- **Design responsivo:** Funciona em celular/tablet
- **Validação:** Token verificado no backend
- **Privacidade:** Apenas vê visitas para sua casa

### Painel do Porteiro (`monitor.html`)

- **2-painel layout:** Left sidebar com lista, right com mapa
- **Botão "Gerar QR":** Cria novo código dinâmico
- **Seleção:** Click em visitante atualiza mapa
- **Auto-refresh:** Recarrega a cada 5 segundos

### Interfone (`interfone.html`)

- **Full-screen:** Optimizado para tablet em moldura
- **Auto-renovação:** QR muda a cada 2 minutos
- **Sem interação:** Apenas exibe (touchscreen proof)
- **Keep-Alive:** Previne lock de tela

---

## 🚨 Geofencing

### Lógica de Cercas Virtuais

O backend calcula a **distância Haversine** entre GPS do visitante e pontos de interesse:

```python
def haversine(lat1, lon1, lat2, lon2):
    # Retorna distância em metros entre 2 pontos GPS
    R = 6371000  # raio da Terra em metros
    # ... cálculo matemático ...
```

### Cercas Implementadas

| Cerca | Raio | Evento | Ação |
|-------|------|--------|------|
| **Entrada na Casa** | 20m | `VISITANTE_CHEGOU_DESTINO` | Muda tela: "Iniciar Saída" |
| **Saída da Portaria** | 30m | `GEOFENCE_ACIONADO` | Finaliza visita automaticamente |

---

## 🔐 Segurança

### Validações

- ✅ Token de morador validado em cada request
- ✅ QR Code expira em 2 minutos
- ✅ Visitante só vê sua própria visita
- ✅ Morador só vê visitas para sua casa
- ✅ GPS só é enviado em status corretos

### CORS

```python
CORS(app)  # Permite requisições cross-origin
```

### Rate Limiting

Não implementado ainda. Considere adicionar para produção.

---

## 📈 Como Testar

### Cenário 1: Fluxo Completo Rápido (5 min)

1. Abra 4 abas do navegador:
   - Tab 1: `http://localhost:5001/monitor.html` (Porteiro)
   - Tab 2: `http://localhost:5001/interfone.html` (Interfone)
   - Tab 3: `http://localhost:5001/morador.html?token=ce7da19c-073f-4535-822c-c9d03e996564` (Morador)
   - Tab 4: Pronta para escanear

2. No Porteiro, clique **"+ Gerar QR"**

3. No Interfone, veja o QR aparecer

4. No Tab 4, abra o QR code URL (ou digitalmente: `http://localhost:5001/?qr_id=1`)

5. Preencha no formulário: Nome, Placa, Destino = "Casa 1719"

6. No Morador, veja a visita aparecer

7. Clique **"Liberar"**

8. No Visitante, veja mapa aparecer

9. Aguarde ~10s, veja GPS se movimentar (simulado próx à casa)

10. Veja "Iniciar Saída" ativar

11. Clique "Iniciar Saída"

12. Veja mapa de retorno e "Acesso Encerrado" após 30s

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'app_websocket'"

```bash
# Certifique-se que está no diretório guardiao-flow-simples
cd guardiao-flow-simples

# Run usando Python module notation
python -m backend.app_websocket
```

### WebSocket não conectando

- Verifique se Flask-SocketIO está instalado: `pip list | grep socketio`
- Verifique CORS: `CORS(app)` está no código
- Browser console (F12): pode haver erro de conexão

### WhatsApp não enviando

- Variáveis de ambiente não configuradas
- Credenciais Twilio inválidas
- Número de telefone em formato errado (deve incluir +55 e código de área)

### GPS não funcionando

- Apenas funciona em HTTPS or localhost
- Solicite permissão ao usuário
- Verifique precisão (pode demorar alguns segundos)

---

## � Monitoramento e Logs

### Scripts de Monitoramento

O sistema inclui ferramentas avançadas para monitoramento em tempo real:

#### `monitor_logs.py` - Monitor Avançado
```bash
# Executar monitoramento em tempo real
python3 monitor_logs.py

# Ou como background process
python3 monitor_logs.py &
```

**Funcionalidades:**
- ✅ Monitora conexões WebSocket em tempo real
- 📊 Estatísticas automáticas (conexões, visitas, erros)
- 📝 Log estruturado com timestamps
- 🔄 Detecção de eventos importantes
- 💾 Logs salvos em `logs/monitor.log`

#### `monitor_logs.sh` - Monitor Básico
```bash
# Executar script simples
./monitor_logs.sh
```

### Eventos Monitorados

| Evento | Descrição | Importância |
|--------|-----------|-------------|
| `websocket_connect` | Cliente conectou via WebSocket | Alta |
| `visit_created` | Nova visita registrada | Alta |
| `visit_approved` | Visita liberada pelo morador | Alta |
| `location_update` | GPS atualizado | Média |
| `geofence_trigger` | Entrada/saída de zona segura | Alta |
| `error` | Erro detectado | Crítica |

### Dashboard de Produção

Para produção no Railway, use o dashboard integrado:
1. Acesse seu projeto no [Railway Dashboard](https://railway.app)
2. Vá para "Logs" na aba lateral
3. Visualize logs em tempo real
4. Configure alertas para erros críticos

### Teste do Sistema

```bash
# 1. Iniciar servidor
python3 backend/app_websocket.py

# 2. Iniciar monitoramento (em outro terminal)
python3 monitor_logs.py

# 3. Testar funcionalidades:
# - Visitante: http://localhost:5001/
# - Morador: http://localhost:5001/morador.html
# - Porteiro: http://localhost:5001/monitor.html
# - Interfone: http://localhost:5001/interfone.html
```

---

## �📝 Próximos Passos

- [ ] Integrar socket.io com JavaScript do frontend
- [ ] Histórico persisstido de visitas
- [ ] Dashboard analytics (gráficos)
- [ ] Notificação push no celular
- [ ] Autenticação de porteiro/morador
- [ ] Rate limiting e throttling GPS
- [ ] Suporte a múltiplos condominios
- [ ] Integração com bloqueio de portões via HTTP

---

## 📞 Suporte

Documentação completa do protocolo WebSocket: `WEBSOCKET_PROTOCOL.md`

---

**Guardião Flow - Transformando a Segurança em Experiência** 🚪✨
