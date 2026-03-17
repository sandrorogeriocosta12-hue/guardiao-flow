from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

from app.database import get_db

router = APIRouter(prefix="/condominios", tags=["Condomínios"])

@router.post("/")
async def create_condominio(
    dados: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo condomínio.
    NOTA: Requer autenticação e role admin
    """
    try:
        logger.info(f"Criando condomínio {dados.get('nome')}")
        
        # TODO: Implementar com autenticação
        # from app.models import Condominio
        # from app.auth.dependencies import get_current_active_user
        # from app.models import Usuario
        
        # cond = Condominio(**dados)
        # db.add(cond)
        # await db.commit()
        
        return {"status": "ok", "message": "Endpoint em desenvolvimento"}
    except Exception as e:
        logger.error(f"Erro ao criar condomínio: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar condomínio")

@router.get("/")
async def list_condominios(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista condomínios com paginação.
    """
    try:
        logger.info(f"Listando condomínios (skip={skip}, limit={limit})")
        
        # TODO: Implementar query
        # from app.models import Condominio
        # result = await db.execute(
        #     select(Condominio).offset(skip).limit(limit)
        # )
        # return result.scalars().all()
        
        return []
    except Exception as e:
        logger.error(f"Erro ao listar condomínios: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar condomínios")

@router.get("/{condominio_id}")
async def get_condominio(
    condominio_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém detalhes de um condomínio específico.
    """
    try:
        logger.info(f"Obtendo condomínio {condominio_id}")
        
        # TODO: Implementar
        # from app.models import Condominio
        # from uuid import UUID
        
        # cond = await db.get(Condominio, UUID(condominio_id))
        # if not cond:
        #     raise HTTPException(status_code=404, detail="Condomínio não encontrado")
        # return cond
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro ao obter condomínio: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter condomínio")

@router.put("/{condominio_id}")
async def update_condominio(
    condominio_id: str,
    dados: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza dados de um condomínio.
    """
    try:
        logger.info(f"Atualizando condomínio {condominio_id}")
        
        # TODO: Implementar atualização
        
        return {"status": "ok", "message": "Endpoint em desenvolvimento"}
    except Exception as e:
        logger.error(f"Erro ao atualizar condomínio: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar condomínio")

@router.delete("/{condominio_id}")
async def delete_condominio(
    condominio_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deleta um condomínio (apenas admin).
    """
    try:
        logger.info(f"Deletando condomínio {condominio_id}")
        
        # TODO: Implementar deleção
        
        return {"message": "Condomínio deletado"}
    except Exception as e:
        logger.error(f"Erro ao deletar condomínio: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar condomínio")
