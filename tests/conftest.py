from typing import Dict
import pytest_asyncio
import os

from sqlalchemy import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from main import app
from app.db.session import get_session

from dotenv import load_dotenv

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

async_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool
)


@pytest_asyncio.fixture(scope="session")
async def init_db():
    """Create tables once per session"""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield async_engine
    
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        
        
@pytest_asyncio.fixture(scope="function")
async def async_db(init_db):
    """Provide database session for each test"""
    async_session = async_sessionmaker(
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        bind=init_db,
        class_=AsyncSession,
    )

    async with async_session() as session:
        yield session
        
        
@pytest_asyncio.fixture(scope="function") 
async def async_client(async_db):
    """Provide HTTP client with test database"""
    async def _override_get_db():
        yield async_db
    
    app.dependency_overrides[get_session] = _override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://testserver"
    ) as ac:
        yield ac
        
    app.dependency_overrides.pop(get_session, None)
    
    
async def create_session_resource(endpoint: str, data: dict, token: str = None) -> dict:
    """Helper to create resources that persist across test session"""
    async_session = async_sessionmaker(
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        bind=async_engine,
        class_=AsyncSession,
    )
    
    async with async_session() as session:
        async with session.begin():
            async def _override_get_db():
                yield session
            
            original_override = app.dependency_overrides.get(get_session)
            app.dependency_overrides[get_session] = _override_get_db
            
            try:
                async with AsyncClient(
                    transport=ASGITransport(app=app), 
                    base_url="http://testserver"
                ) as client:
                    headers = {"Authorization": f"Bearer {token}"} if token else {}
                    response = await client.post(endpoint, json=data, headers=headers)
                    response.raise_for_status()
                    return response.json()
            finally:
                if original_override:
                    app.dependency_overrides[get_session] = original_override
                else:
                    app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture(scope="session")
async def test_user_token(init_db): 
    """Create a user once per session and return token"""
    user_data = {"email": "test@example.com", "password": "testpassword123"}
    body = await create_session_resource("/api/v1/auth/register", user_data)
    return body.get("token")


@pytest_asyncio.fixture(scope="session")
async def test_profile_id(init_db, test_user_token: str):  
    """Create a profile once per session and return its ID"""
    profile_data = {
        "first_name": "Test User", 
        "last_name": "Test Last", 
        "date_of_birth": "2015-01-01"
    }
    body = await create_session_resource(
        "/api/v1/profiles", 
        profile_data, 
        token=test_user_token
    )
    return body.get("id")


@pytest_asyncio.fixture(scope="session")
async def auth_state(test_user_token: str, test_profile_id: str) -> Dict[str, str]:
    """Mutable auth state shared across tests in a session.

    Tests can update this dict (e.g. after email change) to keep subsequent
    authenticated requests working.
    """
    return {
        "token": test_user_token,
        "email": "test@example.com",
        "password": "testpassword123",
        "profile_id": test_profile_id
    }


@pytest_asyncio.fixture(scope="function")
async def auth_headers(auth_state: Dict[str, str]) -> Dict[str, str]:
    """Provide auth headers for authenticated requests"""
    return {"Authorization": f"Bearer {auth_state['token']}"}