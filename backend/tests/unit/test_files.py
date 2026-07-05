"""
Test suite for Files CRUD endpoints
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app

BASE_URL = "/api/v1/files"


@pytest.mark.asyncio
async def test_create_file():
    """Test file creation"""
    payload = {
        "job_id": "00000000-0000-0000-0000-000000000001",
        "path": "test/test.dxf",
        "file_type": "dxf"
    }
    created = {
        "id": "00000000-0000-0000-0000-000000000002",
        **payload,
        "bucket": "dxf-files",
    }
    with patch("app.routes.file_routes.create_file", AsyncMock(return_value=created)):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(BASE_URL + "/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["path"] == payload["path"]
    assert data["job_id"] == payload["job_id"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_file_with_default_type():
    """Test file creation without file_type (should use default 'dxf')"""
    payload = {
        "job_id": "00000000-0000-0000-0000-000000000001",
        "path": "test/test.dxf"
    }
    created = {
        "id": "00000000-0000-0000-0000-000000000002",
        **payload,
        "bucket": "dxf-files",
        "file_type": "dxf",
    }
    with patch("app.routes.file_routes.create_file", AsyncMock(return_value=created)):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(BASE_URL + "/", json=payload)

    assert response.status_code == 201
    assert response.json()["file_type"] == "dxf"


@pytest.mark.asyncio
async def test_get_files():
    """Test file list retrieval"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(BASE_URL + "/", params={"job_id": "00000000-0000-0000-0000-000000000001"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_single_file():
    """Test retrieving a single file"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        file_id = "00000000-0000-0000-0000-000000000001"  # Use dummy UUID
        response = await ac.get(f"{BASE_URL}/{file_id}")
        assert response.status_code in [200, 404]  # 404 if not found


@pytest.mark.asyncio
async def test_update_file():
    """Test updating a file"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        file_id = "00000000-0000-0000-0000-000000000001"
        update_data = {
            "file_url": "https://example.com/updated.dxf",
            "file_type": "pdf"
        }
        response = await ac.patch(f"{BASE_URL}/{file_id}", json=update_data)
        assert response.status_code in [200, 400, 404]


@pytest.mark.asyncio
async def test_delete_file():
    """Test deleting a file"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        file_id = "00000000-0000-0000-0000-000000000001"
        response = await ac.delete(f"{BASE_URL}/{file_id}")
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
