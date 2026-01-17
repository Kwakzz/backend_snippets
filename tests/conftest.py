from typing import Any, Dict
import pytest_asyncio

from sqlalchemy import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from main import app
from app.db.session import get_session

from dotenv import load_dotenv

import os


load_dotenv()


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


async_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool
)

@pytest_asyncio.fixture(scope="session")
async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
    yield async_engine
    
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        
        
@pytest_asyncio.fixture(scope="function")
async def async_db(async_db_engine):

    async_session = async_sessionmaker(
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        bind=async_db_engine,
        class_=AsyncSession,
    )

    async with async_session() as session:
        await session.begin()
        yield session
        await session.rollback()
        
        
	
@pytest_asyncio.fixture(scope="function", autouse=True)
async def async_client(async_db):
    async def _override_get_db():
        yield async_db
    app.dependency_overrides[get_session] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://testserver"
    ) as ac:
        yield ac
        
    app.dependency_overrides.pop(get_session, None)
    
    
@pytest_asyncio.fixture
async def get_user(async_client: AsyncClient):
    async def _create(
        user: Dict[str, Any] = None
    ) -> str:
        if user is None:
            user = {
                "email": "admin@example.com", 
                "password": "password"
            }
        response = await async_client.post("/api/v1/users", json=user)
        
        if response.status_code == 200:
            body = response.json()
            return body.get("token"), user
        
        # If already exists / registration failed, fallback to login
        login = await async_client.post("/api/v1/users/password-login", json=user)
        login.raise_for_status()
        body = login.json()
        return body.get("token"), user

    return _create


@pytest_asyncio.fixture
async def get_token(get_user) -> str:
    token, _ = await get_user()
    return token


@pytest_asyncio.fixture
async def auth_headers(get_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {get_token}"}