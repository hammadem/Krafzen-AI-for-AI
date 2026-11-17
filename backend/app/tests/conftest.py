import pytest

from app.main import app
from app.middlewares.auth import require_auth
from app.middlewares.paid_access import require_paid_subscription

TEST_USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


@pytest.fixture(autouse=True)
def authenticated_api():
    app.dependency_overrides[require_auth] = lambda: TEST_USER
    app.dependency_overrides[require_paid_subscription] = lambda: TEST_USER
    yield
    app.dependency_overrides.pop(require_paid_subscription, None)
    app.dependency_overrides.pop(require_auth, None)
