"""Project API tests (provisional)."""
def test_create_project(client):
    response = client.post(
        "/api/v1/projects/",
        json={"user_id": "test-uuid", "input_text": "Test input"}
    )
    assert response.status_code == 200
    assert "id" in response.json()

def test_list_projects(client):
    response = client.get("/api/v1/projects/?user_id=test-uuid")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
