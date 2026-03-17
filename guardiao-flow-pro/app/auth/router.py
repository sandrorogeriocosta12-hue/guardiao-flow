from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

# Importações que serão do projeto base
from app.database import get_db
from app.schemas import UsuarioLogin, Token
from app.auth.utils import verify_password, create_access_token

# Placeholder - será necessário importar Usuario do models
# from app.models import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=Token)
async def login(
    login_data: UsuarioLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica usuário e retorna JWT token.
    """
    try:
        # NOTA: Descomente e ajuste conforme seus models
        # from app.models import Usuario
        # result = await db.execute(select(Usuario).where(Usuario.email == login_data.email))
        # user = result.scalar_one_or_none()
        
        # if not user or not verify_password(login_data.senha, user.senha_hash):
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Email ou senha incorretos",
        #         headers={"WWW-Authenticate": "Bearer"},
        #     )
        
        # if not user.ativo:
        #     raise HTTPException(status_code=400, detail="Usuário inativo")
        
        # access_token = create_access_token(
        #     data={"sub": str(user.id), "role": user.role.value}
        # )
        # return {"access_token": access_token, "token_type": "bearer"}
        
        # Temporariamente retorna erro
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Módulo em desenvolvimento"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
