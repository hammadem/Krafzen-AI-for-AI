import pytest

from app.main import app
from app.middlewares.auth import require_auth

TEST_USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


@pytest.fixture(autouse=True)
def authenticated_api():
    app.dependency_overrides[require_auth] = lambda: TEST_USER
    yield
    app.dependency_overrides.pop(require_auth, None)
