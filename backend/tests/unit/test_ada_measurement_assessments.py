"""Official 2010 ADA numerical thresholds and recorded evidence, never code approval."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from fastapi import HTTPException
import pytest

from app.services.ada_measurement_rules import evaluate_ada_measurements
from app.routes import compliance_assessment_routes as routes

PROJECT = "00000000-0000-0000-0000-000000000002"
FILE = "00000000-0000-0000-0000-000000000003"
USER = {"user_id": "00000000-0000-0000-0000-000000000001"}
CONTEXT = {
    "state": "California", "municipality": "San Francisco",
    "project_address": "123 Example Street",
    "occupancy": "Assembly", "building_type": "Commercial",
    "standard_edition": "2010_ADA",
    "ada_applicability_confirmed": True,
}


def checks(**overrides):
    data = {
        "door_kind": "manual_swinging",
        "door_clear_width_in": 32,
        "doorway_depth_in": 12,
        "door_measured_at_90_degrees": True,
        "accessible_route_clear_width_in": 36,
        "route_exception_applies": False,
        "ramp_rise_in": 6,
        "ramp_horizontal_run_in": 72,
        "new_construction": True,
        "ramp_alteration_exception_applies": False,
    }
    data.update(overrides)
    return data


def result_by_section(report, section):
    return next(f for f in report["rule_results"] if f["section_reference"] == section)


def test_exact_ada_door_clear_width_at_threshold():
    report = evaluate_ada_measurements(context=CONTEXT, measurements=checks())
    door = result_by_section(report, "404.2.3")
    assert door["result"] == "pass"
    assert door["threshold"] == 32
    assert door["measured"] == 32
    assert door["source_url"].startswith("https://www.ada.gov/")
    assert report["counts"]["pass"] == 3
    assert report["overall_status"] == "pending_qualified_review"
    assert report["complete_code_compliance_determined"] is False
    assert report["verified_against_drawing_geometry"] is False


def test_deep_doorway_needs_36_inch_clear_width():
    report = evaluate_ada_measurements(
        context=CONTEXT,
        measurements=checks(doorway_depth_in=25, door_clear_width_in=33),
    )
    door = result_by_section(report, "404.2.3")
    assert door["threshold"] == 36
    assert door["result"] == "fail"


@pytest.mark.parametrize("width,result", [(35.99, "fail"), (36, "pass"), (42, "pass")])
def test_walking_route_numerical_width(width, result):
    report = evaluate_ada_measurements(
        context=CONTEXT, measurements=checks(accessible_route_clear_width_in=width)
    )
    assert result_by_section(report, "403.5.1")["result"] == result


@pytest.mark.parametrize("run,result", [(60, "fail"), (72, "pass"), (100, "pass")])
def test_ramp_rise_to_horizontal_run_ratio(run, result):
    report = evaluate_ada_measurements(
        context=CONTEXT,
        measurements=checks(ramp_rise_in=6, ramp_horizontal_run_in=run),
    )
    ramp = result_by_section(report, "405.2")
    assert ramp["result"] == result
    assert ramp["calculation_method"].startswith("running slope")


@pytest.mark.parametrize("override", [
    {"door_kind": "sliding"},
    {"door_measured_at_90_degrees": False},
    {"doorway_depth_in": None},
])
def test_door_unsupported_or_unmeasured_never_returns_pass(override):
    report = evaluate_ada_measurements(context=CONTEXT, measurements=checks(**override))
    assert result_by_section(report, "404.2.3")["result"] == "unknown"


def test_exception_is_unknown_not_false_positive_or_false_negative():
    report = evaluate_ada_measurements(
        context=CONTEXT,
        measurements=checks(
            accessible_route_clear_width_in=31,
            route_exception_applies=True,
            ramp_alteration_exception_applies=True,
        ),
    )
    assert result_by_section(report, "403.5.1")["result"] == "unknown"
    assert result_by_section(report, "405.2")["result"] == "unknown"


def test_unknown_jurisdiction_and_edition_all_fail_closed():
    info = {**CONTEXT, "standard_edition": "2024_IBC", "ada_applicability_confirmed": False}
    report = evaluate_ada_measurements(context=info, measurements=checks())
    assert report["counts"]["pass"] == 0
    assert report["counts"]["fail"] == 0
    assert report["counts"]["unknown"] == 3
    assert "supported standard_edition=2010_ADA" in report["missing_information"]


def test_missing_measurements_never_pretend_compliance():
    report = evaluate_ada_measurements(context=CONTEXT, measurements={})
    assert report["counts"]["unknown"] == 3
    assert report["complete_code_compliance_determined"] is False


def request(file_id=FILE):
    return routes.NewAssessment(
        project_id=UUID(PROJECT),
        source_file_id=UUID(file_id) if file_id else None,
        jurisdiction=routes.JurisdictionInput(**CONTEXT),
        measurements=routes.MeasurementsInput(**checks()),
    )


@pytest.mark.asyncio
async def test_assessment_requires_source_file_in_owned_project():
    with (
        patch.object(routes, "_owned_nonsovereign_project", AsyncMock(return_value={"id": PROJECT})),
        patch.object(routes, "get_file", AsyncMock(return_value={
            "id": FILE, "project_id": "00000000-0000-0000-0000-000000000099"
        })),
        patch.object(routes, "db", MagicMock()) as db,
    ):
        with pytest.raises(HTTPException) as error:
            await routes.create_ada_measurement_assessment(request(), user=USER)
    assert error.value.status_code == 404
    db.table.assert_not_called()


@pytest.mark.asyncio
async def test_ada_assessment_is_persisted_with_actual_source_and_created_by():
    query = MagicMock()
    query.insert.return_value = query
    query.execute.return_value = SimpleNamespace(
        data=[{
            "id": "saved-assessment-1", "project_id": PROJECT,
            "created_by": USER["user_id"], "result": {"counts": {"pass": 3}}
        }]
    )
    db = MagicMock()
    db.table.return_value = query

    async def inline(fn):
        return fn()

    with (
        patch.object(routes, "_owned_nonsovereign_project", AsyncMock(return_value={"id": PROJECT})),
        patch.object(routes, "get_file", AsyncMock(return_value={"id": FILE, "project_id": PROJECT})),
        patch.object(routes, "db", db),
        patch.object(routes, "run_in_threadpool", inline),
    ):
        result = await routes.create_ada_measurement_assessment(request(), user=USER)
    assert result["id"] == "saved-assessment-1"
    payload = query.insert.call_args.args[0]
    assert payload["source_file_id"] == FILE
    assert payload["created_by"] == USER["user_id"]
    assert payload["review_status"] == "pending_qualified_review"
    assert payload["result"]["counts"]["pass"] == 3
    assert payload["result"]["complete_code_compliance_determined"] is False


@pytest.mark.asyncio
async def test_sovereign_workspace_assessments_fail_closed():
    with patch.object(
        routes, "get_project", AsyncMock(return_value={
            "id": PROJECT, "workspace_id": "00000000-0000-0000-0000-000000000010"
        })
    ):
        with pytest.raises(HTTPException) as error:
            await routes._owned_nonsovereign_project(PROJECT, USER)
    assert error.value.status_code == 503


@pytest.mark.asyncio
async def test_failed_persistence_must_not_report_succeeded_rule_assessment():
    query = MagicMock()
    query.insert.return_value = query
    query.execute.side_effect = RuntimeError("database authentication unavailable")
    db = MagicMock()
    db.table.return_value = query

    async def inline(fn):
        return fn()

    with (
        patch.object(routes, "_owned_nonsovereign_project", AsyncMock(return_value={"id": PROJECT})),
        patch.object(routes, "get_file", AsyncMock(return_value={"id": FILE, "project_id": PROJECT})),
        patch.object(routes, "db", db),
        patch.object(routes, "run_in_threadpool", inline),
    ):
        with pytest.raises(HTTPException) as error:
            await routes.create_ada_measurement_assessment(request(), user=USER)
    assert error.value.status_code == 503

def test_extended_rules_exact_boundaries_and_unknown_scope():
    data=checks(extended_checks=True,extended_scope_confirmed=True,
        circular_turn_diameter_in=60,clear_floor_width_in=30,clear_floor_length_in=48,
        walking_running_slope_pct=5,walking_cross_slope_pct=100/48,
        ramp_run_clear_width_in=36,ramp_single_run_rise_in=30,ramp_landing_clear_length_in=60)
    report=evaluate_ada_measurements(context=CONTEXT,measurements=data)
    assert report["counts"]=={"pass":11,"fail":0,"unknown":0}
    report=evaluate_ada_measurements(context=CONTEXT,measurements={**data,"walking_cross_slope_pct":2.1,"clear_floor_length_in":47.99})
    assert report["counts"]["fail"]==2
    report=evaluate_ada_measurements(context=CONTEXT,measurements={**data,"extended_scope_confirmed":False})
    assert report["counts"]["unknown"]==8
    assert report["complete_code_compliance_determined"] is False
    report=evaluate_ada_measurements(context=CONTEXT,measurements={**data,"walking_cross_slope_pct":0})
    assert report["counts"]["pass"]==11
