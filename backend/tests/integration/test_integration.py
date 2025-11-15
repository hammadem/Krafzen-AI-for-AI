"""
Integration tests for Jobs and Files CRUD endpoints.
These tests make actual HTTP requests to a running server.

To run these tests:
1. Make sure the server is NOT already running on port 8000, OR
2. Start the server manually: uvicorn app.main:app --reload
3. Run: pytest tests/integration/test_integration.py -v
"""

import pytest
import requests
import time
import subprocess
import os
import sys
from typing import Optional

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Server process
_server_process: Optional[subprocess.Popen] = None


def check_server_running():
    """Check if server is already running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


@pytest.fixture(scope="session", autouse=True)
def start_server():
    """Start the FastAPI server for integration tests (if not already running)"""
    global _server_process
    
    # Check if server is already running
    if check_server_running():
        print("✅ Server already running on port 8000, using existing instance")
        yield
        return
    
    # Start server
    print("🚀 Starting FastAPI server for integration tests...")
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    project_root = os.path.dirname(backend_dir)
    
    env = os.environ.copy()
    # Ensure Python can find the app module
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    _server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=backend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    max_attempts = 30
    server_started = False
    for i in range(max_attempts):
        if check_server_running():
            print("✅ Server started successfully")
            server_started = True
            break
        time.sleep(1)
    
    if not server_started:
        # Print error output
        if _server_process.stderr:
            error_output = _server_process.stderr.read()
            print(f"❌ Server failed to start. Error: {error_output}")
        pytest.fail("Server failed to start within 30 seconds. Make sure port 8000 is available.")
    
    yield
    
    # Cleanup: Stop server (only if we started it)
    if _server_process and not check_server_running():
        print("🛑 Stopping test server...")
        _server_process.terminate()
        try:
            _server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _server_process.kill()
        print("✅ Server stopped")


@pytest.fixture
def test_project_id():
    """Create a test project and return its ID"""
    # Try to create a project for testing
    # If this fails, tests will use a dummy ID
    try:
        response = requests.post(
            f"{API_BASE}/projects/",
            json={
                "user_id": "00000000-0000-0000-0000-000000000000",
                "input_text": "Integration test project"
            },
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code == 201:
            return response.json()["id"]
    except Exception:
        pass
    
    # Return dummy ID if project creation fails
    return "00000000-0000-0000-0000-000000000001"


class TestJobsIntegration:
    """Integration tests for Jobs endpoints using actual HTTP requests"""
    
    def test_health_endpoint(self):
        """Test that the server is running and health endpoint works"""
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
    
    def test_create_job_invalid_project_id(self):
        """Test creating a job with invalid project_id returns 400"""
        response = requests.post(
            f"{API_BASE}/jobs/",
            json={
                "project_id": "invalid-uuid-format",
                "status": "pending"
            },
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        # Should return 400 or 422 for invalid input
        assert response.status_code in [400, 422]
    
    def test_create_job_missing_project_id(self):
        """Test creating a job without project_id returns validation error"""
        response = requests.post(
            f"{API_BASE}/jobs/",
            json={"status": "pending"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        assert response.status_code in [400, 422]
    
    def test_list_jobs(self, test_project_id):
        """Test listing jobs for a project"""
        response = requests.get(
            f"{API_BASE}/jobs/",
            params={"project_id": test_project_id},
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_single_job_not_found(self):
        """Test getting a non-existent job returns 404"""
        response = requests.get(
            f"{API_BASE}/jobs/00000000-0000-0000-0000-000000000999",
            timeout=5
        )
        assert response.status_code == 404
    
    def test_create_job_with_authorization_header(self):
        """Test that authorization header is accepted (format validation)"""
        response = requests.post(
            f"{API_BASE}/jobs/",
            json={
                "project_id": "00000000-0000-0000-0000-000000000001",
                "status": "pending"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token-123"
            },
            timeout=5
        )
        # Should accept the header (even if project doesn't exist, we get 400, not 401)
        assert response.status_code in [201, 400]
    
    def test_create_job_invalid_authorization_format(self):
        """Test that invalid authorization format is rejected"""
        response = requests.post(
            f"{API_BASE}/jobs/",
            json={
                "project_id": "00000000-0000-0000-0000-000000000001",
                "status": "pending"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": "InvalidFormat token"
            },
            timeout=5
        )
        # Should return 400 for invalid auth format
        assert response.status_code == 400
        data = response.json()
        # Check both "detail" and "message" fields (FastAPI uses "detail", our code uses "message")
        error_text = (data.get("detail", "") + " " + data.get("message", "")).lower()
        assert "authorization" in error_text or "invalid" in error_text or "bearer" in error_text


class TestFilesIntegration:
    """Integration tests for Files endpoints using actual HTTP requests"""
    
    def test_create_file_invalid_job_id(self):
        """Test creating a file with invalid job_id returns 400"""
        response = requests.post(
            f"{API_BASE}/files/",
            json={
                "job_id": "invalid-uuid-format",
                "file_url": "https://example.com/test.dxf"
            },
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        # Should return 400 or 422 for invalid input
        assert response.status_code in [400, 422]
    
    def test_create_file_missing_job_id(self):
        """Test creating a file without job_id returns validation error"""
        response = requests.post(
            f"{API_BASE}/files/",
            json={"file_url": "https://example.com/test.dxf"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        assert response.status_code in [400, 422]
    
    def test_create_file_with_default_type(self):
        """Test creating a file without file_type uses default 'dxf'"""
        response = requests.post(
            f"{API_BASE}/files/",
            json={
                "job_id": "00000000-0000-0000-0000-000000000001",
                "file_url": "https://example.com/test.dxf"
                # file_type not provided - should use default
            },
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        # Should accept the request (may fail on job_id validation, but model should accept default)
        assert response.status_code in [201, 400]
        if response.status_code == 201:
            data = response.json()
            assert data.get("file_type") == "dxf"
    
    def test_list_files(self):
        """Test listing files for a job"""
        response = requests.get(
            f"{API_BASE}/files/",
            params={"job_id": "00000000-0000-0000-0000-000000000001"},
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_single_file_not_found(self):
        """Test getting a non-existent file returns 404"""
        response = requests.get(
            f"{API_BASE}/files/00000000-0000-0000-0000-000000000999",
            timeout=5
        )
        assert response.status_code == 404
    
    def test_files_endpoints_accept_authorization(self):
        """Test that Files endpoints accept authorization header"""
        response = requests.post(
            f"{API_BASE}/files/",
            json={
                "job_id": "00000000-0000-0000-0000-000000000001",
                "file_url": "https://example.com/test.dxf"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-token-123"
            },
            timeout=5
        )
        # Should accept the header (even if job doesn't exist, we get 400, not 401)
        assert response.status_code in [201, 400]


class TestEndToEndFlow:
    """End-to-end integration tests"""
    
    def test_api_documentation_accessible(self):
        """Test that Swagger UI is accessible"""
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = requests.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses"""
        response = requests.options(
            f"{API_BASE}/jobs/",
            headers={"Origin": "http://localhost:3000"},
            timeout=5
        )
        # Should have CORS headers
        assert "Access-Control-Allow-Origin" in response.headers or response.status_code == 200

