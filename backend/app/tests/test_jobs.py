"""
Test suite for Jobs CRUD endpoints
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.main import app

BASE_URL = "/api/v1/jobs"


@pytest.mark.asyncio
async def test_create_job():
    """Test job creation"""
    payload = {
        "project_id": "00000000-0000-0000-0000-000000000001",
        "status": "queued",
        "transcript": "This is a test transcript",
        "error_message": None,
    }
    created_job = {
        "id": "00000000-0000-0000-0000-000000000002",
        **payload,
        "created_at": None,
        "updated_at": None,
    }

    with patch("app.routes.job_routes.create_job_query", AsyncMock(return_value=created_job)):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(BASE_URL + "/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == payload["project_id"]


@pytest.mark.asyncio
async def test_get_jobs():
    """Test job list retrieval"""
    with patch("app.routes.job_routes.get_jobs", AsyncMock(return_value=[])) as query:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(BASE_URL + "/", params={"project_id": "00000000-0000-0000-0000-000000000001"})
    assert response.status_code == 200
    assert response.json() == []
    query.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_single_job():
    """Test retrieving a single job"""
    job_id = "00000000-0000-0000-0000-000000000001"
    with patch("app.routes.job_routes.get_job", AsyncMock(return_value=None)) as query:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(f"{BASE_URL}/{job_id}")
    assert response.status_code == 404
    query.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_job():
    """Test deleting a job"""
    job_id = "00000000-0000-0000-0000-000000000001"
    with patch("app.routes.job_routes.delete_job", AsyncMock(return_value=False)) as query:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.delete(f"{BASE_URL}/{job_id}")
    assert response.status_code == 400
    assert "detail" in response.json()
    query.assert_awaited_once()
