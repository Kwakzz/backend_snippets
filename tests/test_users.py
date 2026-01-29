import pytest
from httpx import AsyncClient
from typing import Dict


# Helper function to refresh auth headers after email update
async def refresh_auth_headers(async_client: AsyncClient, email: str, password: str) -> Dict[str, str]:
    """Get fresh auth headers by logging in with updated email"""
    user = {"email": email, "password": password}
    response = await async_client.post("/api/v1/auth/password-login", json=user)
    response.raise_for_status()
    token = response.json().get("token")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    user = {"email": "user1@example.com", "password": "password"}
    response = await async_client.post("/api/v1/auth/register", json=user)
    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    
 
@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    user = {"email": "user1@example.com", "password": "password"}
    response = await async_client.post("/api/v1/auth/password-login", json=user)
    assert response.status_code == 200
    body = response.json()
    assert "token" in body   


# PROTECTED ENDPOINTS
# TEST WITH test@example.com's token
@pytest.mark.asyncio
async def test_update_email_duplicate(async_client: AsyncClient, auth_headers: dict):
    updated_email = {"email": "test@example.com"}
    update_email_response = await async_client.patch(
        "/api/v1/users", 
        json=updated_email,
        headers=auth_headers
    )
    assert update_email_response.status_code == 422


@pytest.mark.asyncio
async def test_update_email(async_client: AsyncClient, auth_headers: dict, auth_state: Dict[str, str]):
    updated_email = {"email": "updatedtest@example.com"}
    update_response = await async_client.patch(
        "/api/v1/users", 
        json=updated_email,
        headers=auth_headers
    )
    assert update_response.status_code == 200
    
    # Update global token with new email
    new_headers = await refresh_auth_headers(
        async_client,
        "updatedtest@example.com",
        auth_state["password"],
    )
    auth_state["email"] = "updatedtest@example.com"
    auth_state["token"] = new_headers["Authorization"].split(" ", 1)[1]