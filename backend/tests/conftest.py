"""Pytest fixtures."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middlewares.auth import require_auth
from app.middlewares.paid_access import require_paid_subscription

TEST_USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


@pytest.fixture(autouse=True)
def authenticated_api():
    app.dependency_overrides[require_auth] = lambda: TEST_USER
    # Contract tests remain database-independent. Paid-access tests remove this
    # override explicitly to exercise the real dependency.
    app.dependency_overrides[require_paid_subscription] = lambda: TEST_USER
    yield
    app.dependency_overrides.pop(require_paid_subscription, None)
    app.dependency_overrides.pop(require_auth, None)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def override_settings():
    # Mock settings for tests
    from app.core.config import settings
    return settings
