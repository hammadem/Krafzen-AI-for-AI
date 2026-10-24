from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.middlewares.auth import require_auth

client = TestClient(app)


def test_health_and_openapi_are_available():
    health = client.get("/health")
    schema = client.get("/openapi.json")

    assert health.status_code == 200
    assert schema.status_code == 200
    assert "/api/v1/projects/" in schema.json()["paths"]
    assert "/api/v1/files/" in schema.json()["paths"]
    assert "/api/v1/jobs/" in schema.json()["paths"]


def test_protected_route_rejects_missing_token():
    override = app.dependency_overrides.pop(require_auth)
    try:
        response = client.get("/api/v1/projects/")
    finally:
        app.dependency_overrides[require_auth] = override

    assert response.status_code == 401


def test_projects_route_accepts_authenticated_request():
    with patch("app.routes.project_routes.get_projects", AsyncMock(return_value=[])):
        response = client.get("/api/v1/projects/")

    assert response.status_code == 200
    assert response.json() == []


def test_project_create_contract():
    project = {
        "id": "00000000-0000-0000-0000-000000000002",
        "user_id": "00000000-0000-0000-0000-000000000001",
        "input_text": "Draw a room",
        "parsed_json": None,
        "image_url": None,
        "dxf_url": None,
        "dwg_url": None,
        "created_at": "2026-07-05T00:00:00Z",
        "updated_at": None,
    }
    with patch("app.routes.project_routes.create_project_query", AsyncMock(return_value=project)):
        response = client.post("/api/v1/projects/", json={"input_text": "Draw a room"})

    assert response.status_code == 201
    assert response.json()["id"] == project["id"]


def test_file_create_contract():
    file_record = {
        "id": "00000000-0000-0000-0000-000000000003",
        "job_id": "00000000-0000-0000-0000-000000000004",
        "project_id": None,
        "bucket": "dxf-files",
        "path": "exports/test.dxf",
        "file_type": "dxf",
        "name": None,
        "mime_type": "application/dxf",
        "size_bytes": 100,
        "created_at": "2026-07-05T00:00:00Z",
    }
    with patch("app.routes.file_routes.create_file", AsyncMock(return_value=file_record)):
        response = client.post(
            "/api/v1/files/",
            json={
                "job_id": file_record["job_id"],
                "path": file_record["path"],
                "mime_type": file_record["mime_type"],
                "size_bytes": file_record["size_bytes"],
            },
        )

    assert response.status_code == 201
    assert response.json()["path"] == file_record["path"]


def test_invalid_job_status_is_rejected():
    response = client.post(
        "/api/v1/jobs/",
        json={
            "project_id": "00000000-0000-0000-0000-000000000002",
            "status": "pending",
        },
    )

    assert response.status_code == 422
