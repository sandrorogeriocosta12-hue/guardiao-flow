from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

# Importações do projeto
from app.database import get_db
from app.websocket_manager import manager

router = APIRouter(prefix="/visitas", tags=["Visitas"])

@router.post("/iniciar")
async def iniciar_visita(
    dados: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Registra entrada de visitante e inicia monitoramento.
    NOTA: Implementar com seus modelos e schemas
    """
    try:
        logger.info(f"Iniciando visita para {dados.get('nome_visitante')}")
        
        # TODO: Implementar com modelos do projeto
        # from app.models import Visita
        # from app.schemas import VisitaIniciar
        
        # nova_visita = Visita(**dados)
        # db.add(nova_visita)
        # await db.commit()
        # await db.refresh(nova_visita)
        
        # Notifica dashboard via WebSocket
        # await manager.broadcast_to_condominio(
        #     str(dados.condominio_id),
        #     {"type": "nova_visita", "visita_id": str(nova_visita.id)}
        # )
        
        return {"status": "ok", "message": "Endpoint em desenvolvimento"}
    except Exception as e:
        logger.error(f"Erro ao iniciar visita: {e}")
        raise HTTPException(status_code=500, detail="Erro ao iniciar visita")

@router.post("/localizacao")
async def receber_localizacao(
    dados: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Recebe coordenadas do visitante e atualiza rota em tempo real.
    """
    try:
        logger.debug(f"Recebendo localização: {dados}")
        
        # TODO: Implementar salvamento de rastreamento
        # from app.models import Rastreamento, Visita
        # from geoalchemy2.functions import ST_MakePoint
        
        # visita = await db.get(Visita, dados.visita_id)
        # if not visita:
        #     raise HTTPException(status_code=404, detail="Visita não encontrada")
        
        # ponto = Rastreamento(
        #     visita_id=dados.visita_id,
        #     localizacao=ST_MakePoint(dados.longitude, dados.latitude)
        # )
        # db.add(ponto)
        # await db.commit()
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro ao receber localização: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar localização")

@router.post("/finalizar/{visita_id}")
async def finalizar_visita(
    visita_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Registra saída do visitante.
    """
    try:
        logger.info(f"Finalizando visita {visita_id}")
        
        # TODO: Implementar finalização
        # from app.models import Visita
        
        # visita = await db.get(Visita, visita_id)
        # if not visita:
        #     raise HTTPException(status_code=404, detail="Visita não encontrada")
        
        # visita.horario_saida = datetime.utcnow()
        # visita.status = "finalizado"
        # await db.commit()
        
        # await manager.broadcast_to_condominio(
        #     str(visita.condominio_id),
        #     {"type": "visita_finalizada", "visita_id": str(visita_id)}
        # )
        
        return {"message": "Visita finalizada"}
    except Exception as e:
        logger.error(f"Erro ao finalizar visita: {e}")
        raise HTTPException(status_code=500, detail="Erro ao finalizar visita")

@router.get("/ativas")
async def visitas_ativas(db: AsyncSession = Depends(get_db)):
    """
    Lista todas as visitas ativas.
    """
    try:
        logger.info("Listando visitas ativas")
        
        # TODO: Implementar query
        # from app.models import Visita
        # result = await db.execute(select(Visita).where(Visita.status == "ativo"))
        # return result.scalars().all()
        
        return []
    except Exception as e:
        logger.error(f"Erro ao listar visitas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar visitas")

@router.websocket("/ws/{condominio_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    condominio_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket para comunicação em tempo real do painel de monitoramento.
    """
    await manager.connect(websocket, condominio_id)
    try:
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Mensagem WebSocket recebida: {data}")
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            # TODO: Implementar lógica de recebimento e processamento de localizações
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, condominio_id)
        logger.info(f"WebSocket desconectado para condominio {condominio_id}")
    except Exception as e:
        logger.error(f"Erro no WebSocket: {e}")
        manager.disconnect(websocket, condominio_id)
