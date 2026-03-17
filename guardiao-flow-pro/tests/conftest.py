import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

# Nota: Descomente quando os modelos estiverem prontos
# from app.database import Base, get_db
# from app.main import app

# TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# @pytest.fixture(scope="session")
# def event_loop():
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()

# @pytest.fixture(scope="session")
# async def engine():
#     engine = create_async_engine(TEST_DATABASE_URL, echo=False)
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     yield engine
#     await engine.dispose()

# @pytest.fixture
# async def db_session(engine):
#     async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
#     async with async_session() as session:
#         yield session

# @pytest.fixture
# async def client(db_session):
#     async def override_get_db():
#         yield db_session
#     app.dependency_overrides[get_db] = override_get_db
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         yield ac
#     app.dependency_overrides.clear()

@pytest.fixture
def mock_settings(monkeypatch):
    """Mock de settings para testes."""
    monkeypatch.setenv("ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
