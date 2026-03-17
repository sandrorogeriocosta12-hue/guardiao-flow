import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def check_visitas_em_andamento(db: AsyncSession, manager):
    """Verifica periodicamente visitas ativas por tempo expirado."""
    while True:
        try:
            await asyncio.sleep(30)
            
            # Importar dentro da função para evitar circular imports
            from app.models import Visita, Alerta
            from geoalchemy2.functions import ST_MakePoint
            
            agora = datetime.utcnow()
            limite_tempo = agora - timedelta(minutes=10)
            
            # Busca visitas ativas com tempo excedido
            result = await db.execute(
                select(Visita).where(
                    Visita.status == "ativo",
                    Visita.horario_entrada < limite_tempo
                )
            )
            
            for visita in result.scalars():
                try:
                    alerta = Alerta(
                        visita_id=visita.id,
                        tipo_alerta="TEMPO",
                        coordenada=ST_MakePoint(
                            visita.ultima_longitude or 0,
                            visita.ultima_latitude or 0
                        )
                    )
                    db.add(alerta)
                    visita.status = "alerta_tempo"
                    await db.commit()
                    
                    # Notifica dashboard
                    await manager.broadcast_to_condominio(
                        str(visita.condominio_id),
                        {
                            "type": "novo_alerta",
                            "visita_id": str(visita.id),
                            "tipo": "TEMPO"
                        }
                    )
                    logger.info(f"Alerta de tempo gerado para visita {visita.id}")
                except Exception as e:
                    logger.error(f"Erro ao processar visita {visita.id}: {e}")
                    await db.rollback()
        except Exception as e:
            logger.error(f"Erro no motor de alertas: {e}")
            await db.rollback()

def start_alert_engine(db: AsyncSession, manager):
    """Inicia o motor de alertas em background."""
    task = asyncio.create_task(check_visitas_em_andamento(db, manager))
    logger.info("Motor de alertas iniciado")
    return task
