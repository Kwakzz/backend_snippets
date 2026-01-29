import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_profile(async_client: AsyncClient, auth_headers: dict):
    profile_data = {
        "first_name": "first",
        "last_name": "last",
        "date_of_birth": "2025-01-01"
    }
    response = await async_client.post("/api/v1/profiles", headers=auth_headers, json=profile_data)
    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    assert body["first_name"] == "first"
    assert body["last_name"] == "last"
    assert body["date_of_birth"] == "2025-01-01"


@pytest.mark.asyncio
async def test_get_profiles(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.get("/api/v1/profiles", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    if body:
        assert "id" in body[0]
        
        
@pytest.mark.asyncio
async def test_update_profile(async_client: AsyncClient, auth_headers: dict, auth_state: dict):
    response = await async_client.patch(
        f"/api/v1/profiles/{auth_state['profile_id']}", 
        headers=auth_headers,
        json={
            "first_name": "updated_first",
            "last_name": "updated_last",
            "date_of_birth": "2025-01-02"
        }
    )
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "updated_first"
    assert body["last_name"] == "updated_last"
    assert body["date_of_birth"] == "2025-01-02"
