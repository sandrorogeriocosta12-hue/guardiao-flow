# Guardião Flow - Backend (Professional Edition)

Versão profissional e escalável do sistema de monitoramento de visitas em condomínios com rastreamento GPS e alertas em tempo real.

## Tecnologias

- **Framework**: FastAPI
- **Base de Dados**: PostgreSQL + PostGIS
- **ORM**: SQLAlchemy (async)
- **Autenticação**: JWT (python-jose)
- **Real-time**: WebSockets
- **Background Tasks**: Celery + Redis
- **Container**: Docker + Docker Compose
- **API Gateway**: Nginx
- **Testing**: Pytest

## Estrutura do Projeto

```
guardiao-flow-pro/
├── app/
│   ├── auth/                 # Autenticação e autorização
│   │   ├── __init__.py
│   │   ├── router.py        # Endpoints de login
│   │   ├── utils.py         # Funções de hash/JWT (do projeto base)
│   │   └── dependencies.py  # Verificação de tokens (do projeto base)
│   ├── routers/             # Endpoints da API
│   │   ├── __init__.py
│   │   ├── visitas.py       # Gerenciamento de visitas
│   │   └── condominios.py   # Gerenciamento de condomínios
│   ├── __init__.py
│   ├── main.py              # Aplicação FastAPI principal
│   ├── config.py            # Configurações por ambiente
│   ├── database.py          # Conexão com banco (do projeto base)
│   ├── models.py            # Modelos SQLAlchemy (do projeto base)
│   ├── schemas.py           # Schemas Pydantic (do projeto base)
│   ├── logging_config.py    # Logging estruturado (JSON)
│   ├── exceptions.py        # Tratamento global de exceções
│   ├── websocket_manager.py # Gerenciador de WebSockets
│   ├── alert_engine.py      # Motor de alertas em background
│   ├── celery_app.py        # Configuração do Celery
│   └── tasks.py             # Tarefas agendadas
├── tests/                   # Testes automatizados
│   ├── __init__.py
│   ├── conftest.py         # Fixtures do pytest
│   └── test_main.py        # Testes dos endpoints
├── migrations/             # Migrações Alembic (vazio)
├── Dockerfile              # Multi-stage para produção
├── docker-compose.yml      # Compose para desenvolvimento
├── docker-compose.prod.yml # Compose para produção
├── nginx.conf              # Configuração do proxy reverso
├── requirements.txt        # Dependências Python
├── .env.example           # Template de variáveis
├── .env.production        # Vars para produção
└── README.md              # Este arquivo
```

## Setup Rápido

### Pré-requisitos

- Docker e Docker Compose
- Python 3.11+ (para desenvolvimento local)
- Git

### Desenvolvimento

1. **Clone o repositório**
   ```bash
   git clone <seu-repo>
   cd guardiao-flow-pro
   ```

2. **Crie o arquivo `.env`**
   ```bash
   cp .env.example .env
   ```

3. **Suba os containers**
   ```bash
   docker-compose up --build
   ```

4. **A API estará disponível em** `http://localhost:8000`
   - Documentação interativa: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Produção

1. **Configure as variáveis de ambiente**
   ```bash
   cp .env.production .env
   # Edite .env com valores reais
   ```

2. **Suba com compose de produção**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Endpoints Principais

### Autenticação
- `POST /auth/login` - Autentica usuário e retorna JWT

### Visitas
- `POST /visitas/iniciar` - Cria nova visita
- `POST /visitas/localizacao` - Envia localização GPS
- `POST /visitas/finalizar/{visita_id}` - Encerra visita
- `GET /visitas/ativas` - Lista visitas ativas
- `WebSocket /visitas/ws/{condominio_id}` - Conexão tempo real

### Condomínios
- `POST /condominios/` - Cria condomínio (admin)
- `GET /condominios/` - Lista condomínios
- `GET /condominios/{id}` - Obtém detalhes
- `PUT /condominios/{id}` - Atualiza
- `DELETE /condominios/{id}` - Deleta (admin)

### Health
- `GET /health` - Status da API
- `GET /info` - Informações da aplicação

## Integração com Projeto Base

Este projeto foi pensado para integrar com os modelos, schemas, database.py e autenticação do projeto anterior. Certifique-se de:

1. Copiar `app/database.py` do projeto anterior
2. Copiar `app/models.py` (atualizar com campos necessários)
3. Copiar `app/schemas.py` (criar schemas para Pydantic)
4. Atualizar `app/auth/utils.py` e `dependencies.py`

## Logging

Os logs são estruturados em JSON e podem ser direcionados para:
- ELK Stack
- Datadog
- Splunk
- CloudWatch

Exemplo de log:
```json
{
  "timestamp": "2026-03-03T10:30:45Z",
  "level": "INFO",
  "name": "app.main",
  "message": "Iniciando Guardião Flow API",
  "environment": "production"
}
```

## Background Tasks

Tarefas agendadas com Celery:
- `check_visitas_expiradas` - A cada 5 minutos
- `notificar_alertas_pendentes` - A cada 10 minutos

Editor de agendamento: Celery Beat

## WebSocket

Conexão bidirecional para monitoramento em tempo real:
- Cliente conecta em `/visitas/ws/{condominio_id}`
- Recebe atualizações de visitas e alertas
- Pode enviar comandos (ex: ping/pong)

## Segurança

- CORS restringido
- Rate limiting por IP
- JWT com expiração
- Senhas com bcrypt
- Headers HTTP de segurança
- Usuário não-root no Docker

## Monitoramento

- Health check: `GET /health`
- Métricas de WebSocket: `GET /info`
- Logs JSON estruturados
- TraceID em requisições

## Deployment

### AWS
```bash
# Usar ECR para imagem
# Deploy em ECS ou Fargate
```

### DigitalOcean
```bash
# App Platform ou Droplet com Docker
```

### Kubernetes
```bash
# Gerar manifests com template
```

## Contribuindo

1. Crie uma branch: `git checkout -b feature/sua-feature`
2. Commit: `git commit -am 'Adiciona feature'`
3. Push: `git push origin feature/sua-feature`
4. Abra um Pull Request

## Licença

MIT

## Suporte

Para dúvidas ou problemas, abra uma issue no repositório.
