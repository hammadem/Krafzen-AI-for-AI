"""Do not invent engineering code compliance provenance for infrastructure checks."""
import pytest

from app.routes.architecture_routes import (
    get_compliance_presets, get_jurisdiction_contracts,
)
from app.services.export_validation_service import run_postflight, run_preflight


@pytest.mark.asyncio
async def test_generic_export_issues_are_not_mislabeled_as_irc_compliance():
    report = await run_postflight({
        "id": "export-1", "format": "dxf", "artifact_file_id": None,
        "metadata": {"stage": "validation_precheck"},
    })
    assert report.passed is False
    assert report.issues
    for issue in report.issues:
        assert issue.jurisdiction is None
        assert issue.rule_version is None


@pytest.mark.asyncio
async def test_technical_preflight_checks_have_no_building_code_claims():
    report = await run_preflight({
        "id": "export-1", "format": "not-a-real-export-format",
        "idempotency_key": "test-123456",
    })
    assert report.can_proceed is False
    assert {i.code for i in report.issues} >= {
        "EXPORT_INVALID_FORMAT", "EXPORT_MISSING_PROJECT",
    }
    assert all(i.jurisdiction is None and i.rule_version is None for i in report.issues)


@pytest.mark.asyncio
async def test_unimplemented_irc_catalog_cannot_be_advertised_as_active():
    result = await get_jurisdiction_contracts()
    assert result.jurisdictions
    for jurisdiction in result.jurisdictions:
        assert jurisdiction.status == "not_implemented"
        assert jurisdiction.supported_exports == []
    presets = await get_compliance_presets()
    assert presets.presets
    for preset in presets.presets:
        assert preset.rule_version == "not_implemented"
        assert "No adopted jurisdiction" in preset.description


def test_public_contract_returns_unavailable_status_not_fake_rules(client):
    response = client.get("/api/v1/contracts/jurisdictions")
    assert response.status_code == 200
    record = response.json()["jurisdictions"][0]
    assert record["status"] == "not_implemented"
    assert record["supported_exports"] == []
