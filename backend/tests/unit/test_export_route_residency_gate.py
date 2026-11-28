"""Prevent sovereign export jobs from silently degrading to global routing."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.routes.export_routes import _resolve_active_assignment


@pytest.mark.parametrize("state", ["provisioning", "suspended", "failed", ""])
def test_existing_inactive_assignment_fails_closed(state):
    with pytest.raises(HTTPException) as exc:
        _resolve_active_assignment({"region_code": "us", "status": state})
    assert exc.value.status_code == 503


@pytest.mark.parametrize("region", ["", "global", None])
def test_active_but_missing_sovereign_region_fails_closed(region):
    with pytest.raises(HTTPException) as exc:
        _resolve_active_assignment({"region_code": region, "status": "active"})
    assert exc.value.status_code == 503


def test_unknown_region_fails_closed():
    with patch("app.routes.export_routes.RegionRegistryService.get_region", return_value=None):
        with pytest.raises(HTTPException) as exc:
            _resolve_active_assignment({"region_code": "unsupported", "status": "active"})
    assert exc.value.status_code == 503


def test_active_us_assignment_uses_registered_pool():
    entry = SimpleNamespace(processing_config={"worker_pool": "us-dedicated-workers"})
    with patch("app.routes.export_routes.RegionRegistryService.get_region", return_value=entry):
        region, pool = _resolve_active_assignment({"region_code": " US ", "status": " ACTIVE "})
    assert region == "us"
    assert pool == "us-dedicated-workers"


def test_active_assignment_without_worker_pool_fails_closed():
    entry = SimpleNamespace(processing_config={})
    with patch("app.routes.export_routes.RegionRegistryService.get_region", return_value=entry):
        with pytest.raises(HTTPException) as exc:
            _resolve_active_assignment({"region_code": "us", "status": "active"})
    assert exc.value.status_code == 503
