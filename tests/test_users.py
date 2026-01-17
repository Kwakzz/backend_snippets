import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    user = {"email": "user1@example.com", "password": "password"}
    response = await async_client.post("/api/v1/users", json=user)
    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    

@pytest.mark.asyncio
async def test_update_email(async_client: AsyncClient):
    user = {"email": "user2@example.com", "password": "password"}
    register_response = await async_client.post("/api/v1/users", json=user)
    assert register_response.status_code == 200
    
    body = register_response.json()
    token = body.get("token")
    
    print(token)
    
    updated_email = {"email": "user2updated@example.com"}
    update_email_response = await async_client.patch(
        "/api/v1/users", 
        json=updated_email,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_email_response.status_code == 200
    