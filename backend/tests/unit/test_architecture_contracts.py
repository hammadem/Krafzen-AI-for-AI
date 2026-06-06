"""Contract endpoint tests for Week 1 architecture alignment."""


def test_export_lifecycle_contract(client):
    response = client.get("/api/v1/contracts/export-lifecycle")
    assert response.status_code == 200
    data = response.json()

    assert "states" in data
    assert "terminal_states" in data
    assert "retryable_states" in data
    assert "queued" in data["states"]
    assert "validating" in data["states"]
    assert "requires_review" in data["states"]
    assert "completed" in data["terminal_states"]


def test_validation_template_contract(client):
    response = client.get("/api/v1/contracts/validation-template")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "validating"
    assert data["format"] == "dxf"
    assert "issues" in data
    assert isinstance(data["issues"], list)


def test_jurisdiction_contracts(client):
    response = client.get("/api/v1/contracts/jurisdictions")
    assert response.status_code == 200
    data = response.json()

    assert "jurisdictions" in data
    assert len(data["jurisdictions"]) >= 1
    first = data["jurisdictions"][0]
    assert first["jurisdiction_id"] == "US_IRC_BASELINE"
    assert "dwg" in first["supported_exports"]
    assert "ifc" in first["supported_exports"]
    assert "dxf" in first["supported_exports"]


def test_compliance_presets_contract(client):
    response = client.get("/api/v1/contracts/compliance-presets")
    assert response.status_code == 200
    data = response.json()

    assert "presets" in data
    assert len(data["presets"]) >= 1
    first = data["presets"][0]
    assert first["preset_id"] == "us-irc-baseline-v1"
    assert first["jurisdiction_id"] == "US_IRC_BASELINE"
    assert first["default_approval_state"] == "pending_review"


def test_export_model_contract(client):
    response = client.get("/api/v1/contracts/export-model")
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["schema_version"] == 1
    assert data["metadata"]["project_id"]
    assert len(data["elements"]) >= 1
    assert data["elements"][0]["krafzen_id"]


def test_workflow_spec_contract(client):
    response = client.get("/api/v1/contracts/workflow-spec")
    assert response.status_code == 200
    data = response.json()

    assert "pipeline_stages" in data
    assert "status_machine" in data
    assert "retry_policy" in data
    assert "supported_formats" in data
    assert "dxf" in data["supported_formats"]
    assert "ifc" in data["supported_formats"]
    assert "dwg" in data["supported_formats"]

