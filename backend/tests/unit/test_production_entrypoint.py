from app.main import app as canonical_app
from main import app as production_app


def test_production_entrypoint_uses_canonical_application():
    assert production_app is canonical_app


def test_production_entrypoint_registers_week2_routes():
    paths = {route.path for route in production_app.routes}

    assert "/api/v1/dashboard/activity" in paths
    assert "/api/v1/dashboard/workspace-summary" in paths
    assert "/api/v1/activity/workspace/{workspace_id}" in paths
    assert "/api/v1/notifications/" in paths
    assert "/api/v1/exports/" in paths
    assert "/health/dwg" in paths
