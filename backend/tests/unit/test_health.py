"""Basic health tests."""
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    # Accept "healthy" or "degraded" (degraded is expected when Supabase credentials are missing)
    assert data["status"] in ["healthy", "degraded"]



def test_readiness_fails_closed_without_required_integration_secrets(client, monkeypatch):
    """A working HTTP server must not be mistaken for a functioning product."""
    from app.core.config import settings
    for field in (
        "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_PROJECT_ID", "SUPABASE_JWT_SECRET",
    ):
        monkeypatch.setattr(settings, field, "")
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["dependencies"]["database"] == "unavailable"
    assert response.json()["dependencies"]["authentication"] == "unavailable"
    assert "SUPABASE_SERVICE_ROLE_KEY" not in response.text


def test_detailed_health_not_healthy_when_database_disconnected(client):
    """Degraded database status must be visible to operations."""
    from unittest.mock import patch
    with patch(
        "app.api.health.supabase_service.test_connection",
        return_value={"connected": False, "status": "error", "message": "not configured"},
    ):
        response = client.get("/health/detailed")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["dependencies"]["database"] == "disconnected"
