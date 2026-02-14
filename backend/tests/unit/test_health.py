"""Basic health tests."""
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    # Accept "healthy" or "degraded" (degraded is expected when Supabase credentials are missing)
    assert data["status"] in ["healthy", "degraded"]
