"""Production readiness must fail closed on actual live database schema drift."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _configured(monkeypatch):
    from app.core.config import settings
    for field in ("SUPABASE_URL","SUPABASE_SERVICE_ROLE_KEY","SUPABASE_PROJECT_ID","SUPABASE_JWT_SECRET"):
        monkeypatch.setattr(settings, field, "ci-probe-nonsecret")


def _fake_db(missing=None):
    db = MagicMock()
    seen = []
    def table(name):
        seen.append(name)
        q = MagicMock()
        q.select.return_value = q
        q.limit.return_value = q
        if name == missing:
            q.execute.side_effect = RuntimeError("missing required table")
        else:
            q.execute.return_value = SimpleNamespace(data=[])
        return q
    db.table.side_effect = table
    return db, seen


def test_readiness_reports_each_required_schema_check_when_connected(client, monkeypatch):
    _configured(monkeypatch)
    db, tables = _fake_db(missing=None)
    with (
        patch("app.api.health.supabase_service.test_connection",
              return_value={"connected": True}),
        patch("app.api.health.db", db),
    ):
        response = client.get("/health/ready")

    details = response.json()["dependencies"]
    expected = {
        "ifc_import_schema","payment_webhook_schema","paid_subscription_schema",
        "project_archive_schema","asbuilt_comparison_schema",
        "drawing_redline_schema","field_inspection_schema",
    }
    assert expected <= set(details)
    assert all(details[key] == "ready" for key in expected)
    assert "payment_webhook_events" in tables
    assert "asbuilt_comparisons" in tables
    assert "drawing_redlines" in tables
    assert "field_inspections" in tables
    assert "projects" in tables


def test_readiness_rejects_missing_review_migration_and_stays_503(client, monkeypatch):
    _configured(monkeypatch)
    db, seen = _fake_db(missing="drawing_redlines")
    with (
        patch("app.api.health.supabase_service.test_connection",
              return_value={"connected": True}),
        patch("app.api.health.db", db),
    ):
        response = client.get("/health/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["dependencies"]["database"] == "ready"
    assert data["dependencies"]["drawing_redline_schema"] == "unavailable"
    assert data["dependencies"]["payment_webhook_schema"] == "ready"
    assert data["dependencies"]["field_inspection_schema"] == "ready"
    assert data["dependencies"]["project_archive_schema"] == "ready"
    assert "drawing_redlines" in seen


def test_readiness_skips_schema_probes_when_database_unreachable(client, monkeypatch):
    _configured(monkeypatch)
    db, seen = _fake_db()
    with (
        patch("app.api.health.supabase_service.test_connection",
              return_value={"connected": False}),
        patch("app.api.health.db", db),
    ):
        response = client.get("/health/ready")
    assert response.status_code == 503
    details = response.json()["dependencies"]
    assert details["database"] == "unavailable"
    assert details["asbuilt_comparison_schema"] == "unavailable"
    assert details["paid_subscription_schema"] == "unavailable"
    assert seen == []
