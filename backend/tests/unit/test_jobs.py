"""Database-independent tests for the authenticated jobs HTTP contract."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.main import app

BASE_URL = "/api/v1/jobs"
PROJECT_ID = "00000000-0000-0000-0000-000000000001"
JOB_ID = "00000000-0000-0000-0000-000000000002"


@pytest.mark.asyncio
async def test_create_job():
    payload = {
        "project_id": PROJECT_ID,
        "status": "queued",
        "transcript": "This is a test transcript",
        "error_message": None,
    }
    created = {**payload, "id": JOB_ID, "created_at": None, "updated_at": None}
    with patch("app.routes.job_routes.create_job_query", AsyncMock(return_value=created)) as query:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(BASE_URL + "/", json=payload)
    assert response.status_code == 201
    assert response.json()["id"] == JOB_ID
    query.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_jobs():
    with patch("app.routes.job_routes.get_jobs", AsyncMock(return_value=[])) as query:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(BASE_URL + "/", params={"project_id": PROJECT_ID})
    assert response.status_code == 200
    assert response.json() == []
    query.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_single_job_returns_404_when_missing():
    with patch("app.routes.job_routes.get_job", AsyncMock(return_value=None)) as query:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(f"{BASE_URL}/{JOB_ID}")
    assert response.status_code == 404
    query.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_job_rejects_unsuccessful_delete():
    with patch("app.routes.job_routes.delete_job", AsyncMock(return_value=False)) as query:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.delete(f"{BASE_URL}/{JOB_ID}")
    assert response.status_code == 400
    assert "detail" in response.json()
    query.assert_awaited_once()
