from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.services.database_router import RegionalDatabaseRouter
from app.services.residency_evidence import platform_evidence
from app.services.region_registry import RegionRegistryService


def test_region_catalog_does_not_advertise_unverified_us_as_active():
    region = next(r for r in RegionRegistryService.get_public_regions() if r["region_code"] == "us")
    assert region["is_available"] is False


def test_provider_evidence_cannot_be_inherited_by_another_project(monkeypatch):
    monkeypatch.setattr(settings, "RESIDENCY_EVIDENCE_PROJECT_ID", "recorded")
    monkeypatch.setattr(settings, "RESIDENCY_EVIDENCE_DATABASE_REGION", "us-east-1")
    monkeypatch.setattr(settings, "SUPABASE_PROJECT_ID", "different")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://different.supabase.co")
    report = platform_evidence()
    assert report["residency_verified"] is False
    assert report["paths"][0]["status"] == "unverified"
    monkeypatch.setattr(settings, "SUPABASE_PROJECT_ID", "recorded")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://recorded.supabase.co")
    report = platform_evidence()
    assert report["paths"][0]["location"] == "AWS us-east-1"
    assert report["residency_verified"] is False


@pytest.mark.parametrize("response", [None, SimpleNamespace(data=None), SimpleNamespace(data=[{}, {}])])
def test_invalid_assignment_lookup_never_falls_back(response):
    central = MagicMock()
    central.table.return_value.select.return_value.eq.return_value.execute.return_value = response
    with pytest.raises(HTTPException) as exc:
        RegionalDatabaseRouter(central).resolve_context(uuid4())
    assert exc.value.status_code == 503
