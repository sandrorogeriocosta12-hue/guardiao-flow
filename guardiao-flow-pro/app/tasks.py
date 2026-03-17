import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task
def check_visitas_expiradas():
    """
    Tarefa agendada para verificar visitas com tempo expirado.
    Executada periodicamente pelo Celery Beat.
    """
    logger.info("Executando tarefa: check_visitas_expiradas")
    
    # TODO: Implementar com acesso ao banco de dados
    # from app.database import AsyncSessionLocal
    # from app.models import Visita, Alerta
    # from geoalchemy2.functions import ST_MakePoint
    
    # async def _check():
    #     async with AsyncSessionLocal() as db:
    #         agora = datetime.utcnow()
    #         limite = agora - timedelta(minutes=15)
    #         result = await db.execute(
    #             select(Visita).where(
    #                 Visita.status == "ativo",
    #                 Visita.horario_entrada < limite
    #             )
    #         )
    #         for visita in result.scalars():
    #             alerta = Alerta(...)
    #             db.add(alerta)
    #         await db.commit()
    
    # asyncio.run(_check())
    return {"status": "completed"}

@celery_app.task
def notificar_alertas_pendentes():
    """
    Tarefa para reenviar alertas pendentes que não foram recebidos.
    """
    logger.info("Executando tarefa: notificar_alertas_pendentes")
    
    # TODO: Implementar lógica de reenvio de alertas
    
    return {"status": "completed"}

# Configuração do Celery Beat (agendador)
celery_app.conf.beat_schedule = {
    'check-visitas-expiradas': {
        'task': 'app.tasks.check_visitas_expiradas',
        'schedule': timedelta(minutes=5),  # A cada 5 minutos
    },
    'notificar-alertas': {
        'task': 'app.tasks.notificar_alertas_pendentes',
        'schedule': timedelta(minutes=10),  # A cada 10 minutos
    },
}
