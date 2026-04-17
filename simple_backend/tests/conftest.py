import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from src.database import init_db


@pytest.fixture(scope="session")
async def client():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
