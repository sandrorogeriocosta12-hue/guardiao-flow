import pytest

@pytest.mark.asyncio
async def test_health_check():
    """Teste do endpoint de health check."""
    from app.main import app
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_root():
    """Teste do endpoint raiz."""
    from app.main import app
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

# TODO: Adicionar testes para endpoints de visitas, condomínios, auth, etc
# conforme os modelos forem implementados
