"""Deterministic edition-bound calculations and fail-closed adoption requirements."""
from copy import deepcopy

import pytest

from app.services.building_code_measurement_rules import evaluate_building_code_measurements


CONTEXT = {
    "state": "Test State", "municipality": "Test City",
    "project_address": "1 Test Project Street", "occupancy": "B",
    "building_type": "office", "construction_type": "II-B",
    "building_height_ft": 24, "building_area_sqft": 8000,
    "ibc_edition": "2024", "nfpa101_edition": "2024",
    "ibc_applicability_confirmed": True, "nfpa101_applicability_confirmed": True,
    "local_amendments_reviewed_no_conflict": True,
    "adoption_reference": "Isolated QA fixture, not real ordinance",
    "reviewer_name": "Isolated QA reviewer fixture",
}
MEASURES = {
    "egress_factor_basis": "standard_confirmed",
    "other_egress_exceptions_excluded": True,
    "stair_occupant_load": 200, "stair_clear_width_in": 60,
    "other_occupant_load": 200, "other_clear_width_in": 39,
    "emergency_lighting_required_confirmed": True,
    "floor_level_egress_photometry_confirmed": True,
    "emergency_duration_minutes": 90,
    "initial_average_fc": 1.0, "initial_minimum_fc": 0.1,
    "final_average_fc": 0.6, "final_minimum_fc": 0.06,
    "measured_maximum_fc": 4, "measured_minimum_fc": 0.1,
}


def evaluate(context=None, measures=None, file_id="fixture-file"):
    return evaluate_building_code_measurements(
        context=deepcopy(CONTEXT) if context is None else context,
        measurements=deepcopy(MEASURES) if measures is None else measures,
        source_file_id=file_id,
    )


def finding(report, prefix):
    return next(f for f in report["rule_results"] if f["rule_id"].startswith(prefix))


def test_capacity_and_photometry_exact_boundaries_and_known_fail():
    r = evaluate()
    assert r["counts"] == {"pass": 7, "fail": 1, "unknown": 0}
    assert finding(r, "IBC-2024-1005.3.1")["threshold"] == 60
    assert finding(r, "IBC-2024-1005.3.2")["threshold"] == 40
    assert finding(r, "IBC-2024-1005.3.2")["result"] == "fail"
    assert r["complete_code_compliance_determined"] is False
    assert len(r["coverage"]) == 25
    assert all(x["full_category_compliance"] == "unknown" for x in r["coverage"])
    assert all(x["source_url"] and x["section_reference"] and x["evidence"]["source_file_id"]
               for x in r["rule_results"])


@pytest.mark.parametrize("key, value", [
    ("ibc_edition", "2021"), ("ibc_applicability_confirmed", False),
    ("local_amendments_reviewed_no_conflict", False), ("adoption_reference", ""),
    ("reviewer_name", ""), ("building_height_ft", None),
])
def test_unsafe_adoption_or_context_never_returns_ibc_pass(key, value):
    r = evaluate(context={**CONTEXT, key: value})
    assert all(x["result"] == "unknown" for x in r["rule_results"] if x["code_family"] == "IBC")


def test_no_project_evidence_means_unknown_not_pass():
    r = evaluate(file_id=None)
    assert r["counts"]["unknown"] == 8


def test_reduced_capacity_factor_requires_eligible_group_and_verified_systems():
    reduced = {
        **MEASURES, "egress_factor_basis": "sprinkler_voice_exception_confirmed",
        "qualifying_sprinkler_system_confirmed": True,
        "qualifying_voice_alarm_confirmed": True,
    }
    r = evaluate(measures=reduced)
    assert finding(r, "IBC-2024-1005.3.1")["threshold"] == 40
    assert finding(r, "IBC-2024-1005.3.2")["threshold"] == 30
    for group in ("I-2", "H", "H-1", "unverified mixed occupancy"):
        r = evaluate(context={**CONTEXT, "occupancy": group}, measures=reduced)
        assert finding(r, "IBC-2024-1005.3.1")["result"] == "unknown"
    r = evaluate(measures={**reduced, "qualifying_voice_alarm_confirmed": False})
    assert finding(r, "IBC-2024-1005.3.1")["result"] == "unknown"


def test_missing_photometry_and_insufficient_duration():
    r = evaluate(measures={
        **MEASURES, "emergency_duration_minutes": 89,
        "floor_level_egress_photometry_confirmed": False,
    })
    assert finding(r, "NFPA101-2024-7.9.2.1-emergency")["result"] == "fail"
    assert finding(r, "NFPA101-2024-7.9.2.1.1-initial_average")["result"] == "unknown"


@pytest.mark.parametrize("load", [float("nan"), float("inf"), -1, 1.5, True])
def test_invalid_occupant_load_is_not_a_valid_calculation(load):
    r = evaluate(measures={**MEASURES, "stair_occupant_load": load})
    assert finding(r, "IBC-2024-1005.3.1")["result"] == "unknown"


def test_pdf_uses_persisted_evidence_and_rejects_inconsistent_counts():
    from app.services.compliance_pdf_service import build_compliance_pdf
    report = evaluate()
    row = {"id": "fixture-assessment", "project_id": "fixture-project",
           "source_file_id": "fixture-file", "jurisdiction": CONTEXT,
           "measurements": MEASURES, "result": report}
    assert build_compliance_pdf(row).startswith(b"%PDF-")
    report["counts"]["pass"] = 99
    with pytest.raises(ValueError, match="count mismatch"):
        build_compliance_pdf(row)


def test_optional_straight_stair_rule_boundaries():
    measures={**MEASURES,"extended_stair_checks":True,"ordinary_straight_stair_no_exceptions_confirmed":True,
        "stair_min_riser_in":6.625,"stair_max_riser_in":7,"stair_min_tread_in":11,"stair_min_headroom_in":80}
    report=evaluate(measures=measures)
    assert report["rule_version"]=="ibc_nfpa_measurements_v2"
    assert finding(report,"IBC-2024-1011.5.4")["result"]=="pass"
    assert finding(report,"IBC-2024-1011.3")["result"]=="pass"
    bad=evaluate(measures={**measures,"stair_max_riser_in":7.01,"stair_min_tread_in":10.99,"stair_min_headroom_in":79.99})
    assert finding(bad,"IBC-2024-1011.5.2-stair_max")["result"]=="fail"
    assert finding(bad,"IBC-2024-1011.5.2-stair_min_tread")["result"]=="fail"
    assert finding(bad,"IBC-2024-1011.5.4")["result"]=="fail"
    assert finding(bad,"IBC-2024-1011.3")["result"]=="fail"
    unknown=evaluate(measures={**measures,"ordinary_straight_stair_no_exceptions_confirmed":False})
    assert all(f["result"]=="unknown" for f in unknown["rule_results"] if f["rule_id"].startswith("IBC-2024-1011"))
    assert bad["complete_code_compliance_determined"] is False
