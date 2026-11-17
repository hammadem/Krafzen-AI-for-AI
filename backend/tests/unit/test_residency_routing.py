"""Fail-closed tests for region-bound Supabase and storage routing."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.services.database_router import RegionalDatabaseRouter
from app.utils.storage_service import StorageService


@pytest.fixture(autouse=True)
def clear_regional_client_cache():
    RegionalDatabaseRouter._regional_clients.clear()
    yield
    RegionalDatabaseRouter._regional_clients.clear()


def central_client(rows=None, error=None):
    client = MagicMock()
    response = client.table.return_value.select.return_value.eq.return_value.execute
    if error:
        response.side_effect = error
    else:
        response.return_value = SimpleNamespace(data=rows if rows is not None else [])
    return client


def test_unassigned_org_retains_legacy_central_routing():
    central = central_client()
    assert RegionalDatabaseRouter(central).resolve_for_organization(uuid4()) is central


def test_central_residency_lookup_failure_blocks_instead_of_fallback():
    central = central_client(error=RuntimeError("connection down"))
    with pytest.raises(HTTPException) as exc:
        RegionalDatabaseRouter(central).resolve_for_organization(uuid4())
    assert exc.value.status_code == 503


def test_active_us_residency_without_credentials_blocks(monkeypatch):
    central = central_client([{"region_code": "us", "status": "active"}])
    monkeypatch.setattr(settings, "SUPABASE_URL_US", None)
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY_US", None)
    with pytest.raises(HTTPException) as exc:
        RegionalDatabaseRouter(central).resolve_for_organization(uuid4())
    assert exc.value.status_code == 503


def test_same_us_and_central_endpoint_is_rejected(monkeypatch):
    central = central_client([{"region_code": "us", "status": "active"}])
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://central.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_URL_US", "https://central.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY_US", "dummy-test-key")
    with pytest.raises(HTTPException) as exc:
        RegionalDatabaseRouter(central).resolve_for_organization(uuid4())
    assert exc.value.status_code == 503


def test_active_us_residency_uses_dedicated_client(monkeypatch):
    central = central_client([{"region_code": "us", "status": "active"}])
    regional = MagicMock()
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://central.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_URL_US", "https://us-only.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY_US", "dummy-test-key")
    with patch("app.services.database_router.create_client", return_value=regional) as create:
        resolved = RegionalDatabaseRouter(central).resolve_for_organization(uuid4())
    create.assert_called_once_with("https://us-only.supabase.co", "dummy-test-key")
    assert resolved is regional
    assert resolved is not central


@pytest.mark.parametrize("state", ["provisioning", "suspended", "failed"])
def test_existing_nonactive_assignment_never_falls_back(state):
    central = central_client([{"region_code": "us", "status": state}])
    with pytest.raises(HTTPException) as exc:
        RegionalDatabaseRouter(central).resolve_for_organization(uuid4())
    assert exc.value.status_code == 503


def test_storage_registry_failure_blocks_instead_of_central_bucket():
    central = central_client(error=RuntimeError("residency lookup failed"))
    regional = MagicMock()
    with (
        patch("app.utils.storage_service.supabase_service") as service,
        patch.object(RegionalDatabaseRouter, "resolve_for_organization", return_value=regional),
    ):
        service.client = central
        with pytest.raises(HTTPException) as exc:
            StorageService.resolve_target_bucket_and_client(uuid4())
    assert exc.value.status_code == 503
