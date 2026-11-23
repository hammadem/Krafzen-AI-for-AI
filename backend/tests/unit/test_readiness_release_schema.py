"""Release readiness checks every required AEC and billing database contract.

These are isolated PostgREST mocks; they do not claim any live deployment or
completion of residential/commercial/BIM/as-built/paid E2E acceptance tests.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


SECURITY = (
    "branding_rls_and_privileges",
    "paid_only_signup_function",
    "signup_trigger_enabled",
    "no_free_trial_balances",
)


REQUIRED = {
    "ifc_import_schema": ("files", "import_metadata"),
    "paid_webhook_ledger_schema": ("payment_webhook_events", "event_id"),
    "paid_subscription_schema": ("user_subscriptions", "last_paid_at"),
    "project_archive_schema": ("projects", "archived_at"),
    "asbuilt_comparison_schema": ("asbuilt_comparisons", "id"),
    "drawing_redline_schema": ("drawing_redlines", "id"),
    "field_inspection_schema": ("field_inspections", "id"),
    "ada_assessment_schema": ("compliance_assessments", "id"),
    "field_photo_schema": ("field_photos", "id"),
    "bim_spatial_screen_schema": ("bim_spatial_screenings", "id"),
}


def _configured(monkeypatch):
    from app.core.config import settings

    for field in (
        "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_PROJECT_ID", "SUPABASE_JWT_SECRET",
    ):
        monkeypatch.setattr(settings, field, "ci-nonsecret")


def _db(missing=None, insecure=None, unavailable_rpc=False):
    fake = MagicMock()
    observed = []

    def table(table_name):
        query = MagicMock()

        def select(column):
            observed.append((table_name, column))
            return query

        query.select.side_effect = select
        query.limit.return_value = query
        def execute():
            if observed[-1] == missing:
                raise RuntimeError("internal database secret: missing schema")
            return SimpleNamespace(data=[])

        query.execute.side_effect = execute
        return query

    fake.table.side_effect = table

    def rpc(name):
        assert name == "krafzen_release_security_probe"
        if unavailable_rpc:
            raise RuntimeError("internal database secret: missing readiness function")
        query = MagicMock()
        report = {key: key != insecure for key in SECURITY}
        report["ready"] = all(report.values())
        query.execute.return_value = SimpleNamespace(data=report)
        return query
    fake.rpc.side_effect = rpc
    return fake, observed


def test_all_critical_schema_contracts_are_probed(client, monkeypatch):
    _configured(monkeypatch)
    fake, observed = _db()
    with (
        patch("app.api.health.supabase_service.test_connection",
              return_value={"connected": True}),
        patch("app.api.health.db", fake),
    ):
        response = client.get("/health/ready")

    deps = response.json()["dependencies"]
    for dependency, pair in REQUIRED.items():
        assert deps[dependency] == "ready"
        assert pair in observed
    assert len(observed) == len(REQUIRED)
    assert all(deps[name] == "ready" for name in SECURITY)
    fake.rpc.assert_called_once_with("krafzen_release_security_probe")


@pytest.mark.parametrize("dependency", sorted(REQUIRED))
def test_missing_any_critical_schema_blocks_release(client, monkeypatch, dependency):
    _configured(monkeypatch)
    fake, _ = _db(missing=REQUIRED[dependency])
    with (
        patch("app.api.health.supabase_service.test_connection",
              return_value={"connected": True}),
        patch("app.api.health.db", fake),
    ):
        response = client.get("/health/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["dependencies"]["database"] == "ready"
    assert payload["dependencies"][dependency] == "unavailable"
    assert "internal database secret" not in response.text
    for other in REQUIRED:
        if other != dependency:
            assert payload["dependencies"][other] == "ready"


def test_unreachable_database_skips_all_schema_probes(client, monkeypatch):
    _configured(monkeypatch)
    fake, observed = _db()
    with (
        patch("app.api.health.supabase_service.test_connection",
              return_value={"connected": False}),
        patch("app.api.health.db", fake),
    ):
        response = client.get("/health/ready")

    assert response.status_code == 503
    dependencies = response.json()["dependencies"]
    assert dependencies["database"] == "unavailable"
    assert all(dependencies[dependency] == "unavailable" for dependency in REQUIRED)
    assert observed == []
    fake.rpc.assert_not_called()
    assert all(dependencies[check] == "unavailable" for check in SECURITY)



@pytest.mark.parametrize("insecure", SECURITY)
def test_security_drift_fails_release_readiness(client, monkeypatch, insecure):
    _configured(monkeypatch)
    fake, _ = _db(insecure=insecure)
    with (
        patch("app.api.health.supabase_service.test_connection",
              return_value={"connected": True}),
        patch("app.api.health.db", fake),
    ):
        response = client.get("/health/ready")
    assert response.status_code == 503
    dependencies = response.json()["dependencies"]
    assert dependencies["database"] == "ready"
    assert dependencies[insecure] == "unavailable"
    assert all(dependencies[other] == "ready" for other in SECURITY
               if other != insecure)


def test_missing_security_rpc_never_passes_release(client, monkeypatch):
    _configured(monkeypatch)
    fake, _ = _db(unavailable_rpc=True)
    with (
        patch("app.api.health.supabase_service.test_connection",
              return_value={"connected": True}),
        patch("app.api.health.db", fake),
    ):
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert all(response.json()["dependencies"][check] == "unavailable"
               for check in SECURITY)
    assert "internal database secret" not in response.text
