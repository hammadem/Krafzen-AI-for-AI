"""Health gates require the import scanner and a migrated database."""

from unittest.mock import AsyncMock, patch

from app.main import app


def test_import_diagnostics_report_missing_scanner(client):
    with patch("app.api.health.shutil.which", return_value=None):
        response = client.get("/health/imports")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "incomplete"
    assert data["dependencies"]["scanner_binary_detected"] is False
    assert data["scanner_signatures_verified"] is False
    assert data["storage_upload_verified"] is False


def test_import_diagnostics_never_claim_scanning_verified(client):
    with patch("app.api.health.shutil.which", return_value="/usr/bin/clamscan"):
        response = client.get("/health/imports")
    assert response.status_code == 200
    assert response.json()["scanner_signatures_verified"] is False


def test_readiness_reports_ifc_migration_missing(client, monkeypatch):
    from app.core.config import settings

    # Pretend secrets are present but the IFC metadata schema is absent.
    for name in (
        "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_PROJECT_ID", "SUPABASE_JWT_SECRET",
    ):
        monkeypatch.setattr(settings, name, "test-value")

    with (
        patch("app.api.health.supabase_service.test_connection", return_value={"connected": True}),
        patch(
            "app.api.health.run_in_threadpool",
            new_callable=AsyncMock,
            side_effect=[{"connected": True}, RuntimeError("column missing")],
        ),
    ):
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["dependencies"]["database"] == "ready"
    assert response.json()["dependencies"]["ifc_import_schema"] == "unavailable"
