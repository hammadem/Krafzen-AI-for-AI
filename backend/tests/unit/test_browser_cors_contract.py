"""Actual FastAPI preflight regression for the browser's authenticated API client."""
import pytest

@pytest.mark.parametrize("origin", ["http://127.0.0.1:3000","http://localhost:3000"])
def test_workspace_browser_preflight_allows_actual_api_headers(client, origin):
    result = client.options("/api/v1/projects/", headers={
        "Origin": origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type,apikey",
    })
    assert result.status_code == 200
    assert result.headers["access-control-allow-origin"] == origin
    allowed = {value.strip().lower() for value in result.headers["access-control-allow-headers"].split(",")}
    assert {"authorization", "content-type", "apikey"} <= allowed
    assert "Origin" in result.headers["vary"]
    assert "content-disposition" in result.headers["access-control-expose-headers"].lower()

def test_untrusted_origin_cannot_use_browser_credentials(client):
    result = client.options("/api/v1/projects/", headers={
        "Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type,apikey",
    })
    assert "access-control-allow-origin" not in result.headers
    assert "access-control-allow-credentials" not in result.headers
