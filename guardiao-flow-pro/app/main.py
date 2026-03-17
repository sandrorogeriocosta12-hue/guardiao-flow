from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.config import settings
from app.logging_config import setup_logging
from app.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler
)
from app.routers import visitas, condominios
from app.auth import router as auth_router
from app.websocket_manager import manager

# Setup logging
logger = setup_logging()

# Criar app FastAPI
app = FastAPI(
    title="Guardião Flow API",
    version="0.1.0",
    description="API para monitoramento de visitas em condomínios com rastreamento GPS e alertas em tempo real"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Rotas
app.include_router(auth_router.router)
app.include_router(visitas.router)
app.include_router(condominios.router)

@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a aplicação."""
    logger.info(f"Iniciando Guardião Flow API em modo {settings.ENV}")
    logger.info(f"Banco de dados: {settings.DATABASE_URL}")
    # TODO: Descomentar após configuração completa
    # from app.database import AsyncSessionLocal
    # async with AsyncSessionLocal() as db:
    #     from app.alert_engine import start_alert_engine
    #     start_alert_engine(db, manager)

@app.on_event("shutdown")
async def shutdown_event():
    """Executado ao desligar a aplicação."""
    logger.info("Desligando Guardião Flow API")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Guardião Flow API",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "environment": settings.ENV
    }

@app.get("/info")
async def info():
    """Informações da API."""
    return {
        "name": "Guardião Flow",
        "version": "0.1.0",
        "environment": settings.ENV,
        "websocket_connections": len(manager.active_connections)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENV == "development"
    )
