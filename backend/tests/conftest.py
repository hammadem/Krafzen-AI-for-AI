"""Pytest fixtures."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def override_settings():
    # Mock settings for tests
    from app.core.config import settings
    return settings
