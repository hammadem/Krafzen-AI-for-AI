"""Paid, owner-scoped measurements screening with immutable evidence history."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.db.queries.file_queries import get_file
from app.db.queries.project_queries import get_project
from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.services.ada_measurement_rules import evaluate_ada_measurements
from app.services.building_code_measurement_rules import evaluate_building_code_measurements

router = APIRouter(prefix="/compliance", tags=["Measured Compliance"])


class JurisdictionInput(BaseModel):
    state: str = Field(min_length=2, max_length=100)
    municipality: str = Field(min_length=2, max_length=100)
    project_address: str = Field(min_length=5, max_length=250)
    occupancy: str = Field(min_length=2, max_length=100)
    building_type: str = Field(min_length=2, max_length=100)
    standard_edition: str
    ada_applicability_confirmed: bool = False


class MeasurementsInput(BaseModel):
    door_kind: Literal["manual_swinging", "sliding", "automatic"] | None = None
    door_clear_width_in: float | None = Field(default=None, gt=0, le=1000, allow_inf_nan=False)
    doorway_depth_in: float | None = Field(default=None, gt=0, le=1000, allow_inf_nan=False)
    door_measured_at_90_degrees: bool | None = None
    accessible_route_clear_width_in: float | None = Field(default=None, gt=0, le=1000, allow_inf_nan=False)
    route_exception_applies: bool | None = None
    ramp_rise_in: float | None = Field(default=None, gt=0, le=1000, allow_inf_nan=False)
    ramp_horizontal_run_in: float | None = Field(default=None, gt=0, le=100000, allow_inf_nan=False)
    new_construction: bool | None = None
    ramp_alteration_exception_applies: bool | None = None


class NewAssessment(BaseModel):
    project_id: UUID
    source_file_id: UUID | None = None
    jurisdiction: JurisdictionInput
    measurements: MeasurementsInput


async def _owned_nonsovereign_project(project_id: str, user: dict) -> dict:
    project = await get_project(project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("workspace_id"):
        raise HTTPException(
            status_code=503,
            detail="Organization compliance evidence needs verified regional processing",
        )
    return project


@router.post("/ada-measurements", status_code=201)
async def create_ada_measurement_assessment(
    body: NewAssessment, user: dict = Depends(require_auth),
):
    project_id = str(body.project_id)
    await _owned_nonsovereign_project(project_id, user)
    if body.source_file_id is not None:
        source_file = await get_file(str(body.source_file_id), user)
        if not source_file or str(source_file.get("project_id") or "") != project_id:
            raise HTTPException(
                status_code=404, detail="Evidence file not found in the selected project"
            )
        if source_file.get("archived_at"):
            raise HTTPException(status_code=409, detail="Cannot cite an archived evidence file")

    # No LLM, no jurisdiction assumptions; results cite the official reference
    # and retain full user-entered measurement provenance in the DB row.
    context = body.jurisdiction.model_dump()
    measures = body.measurements.model_dump()
    result = evaluate_ada_measurements(context=context, measurements=measures)
    payload = {
        "project_id": project_id,
        "source_file_id": str(body.source_file_id) if body.source_file_id else None,
        "created_by": user["user_id"],
        "jurisdiction": context,
        "measurements": measures,
        "result": result,
        "review_status": "pending_qualified_review",
    }
    try:
        response = await run_in_threadpool(
            lambda: db.table("compliance_assessments").insert(payload).execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail="Compliance assessment could not be persisted"
        ) from exc
    if not response or not response.data:
        raise HTTPException(status_code=503, detail="Assessment was not saved")
    return response.data[0]


@router.get("/projects/{project_id}/ada-measurements")
async def list_ada_measurement_assessments(
    project_id: UUID, user: dict = Depends(require_auth),
    limit: int = Query(default=40, ge=1, le=100),
):
    pid = str(project_id)
    await _owned_nonsovereign_project(pid, user)
    try:
        response = await run_in_threadpool(
            lambda: db.table("compliance_assessments")
            .select("*")
            .eq("project_id", pid)
            .eq("created_by", user["user_id"])
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Assessment history unavailable") from exc
    return response.data if response and response.data else []


@router.get("/ada-measurements/{assessment_id}")
async def get_ada_measurement_assessment(
    assessment_id: UUID, user: dict = Depends(require_auth),
):
    try:
        response = await run_in_threadpool(
            lambda: db.table("compliance_assessments")
            .select("*")
            .eq("id", str(assessment_id))
            .eq("created_by", user["user_id"])
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Assessment unavailable") from exc
    record = response.data if response else None
    if not record:
        raise HTTPException(status_code=404, detail="Assessment not found")
    await _owned_nonsovereign_project(str(record["project_id"]), user)
    return record


class BuildingCodeJurisdiction(BaseModel):
    state: str = Field(min_length=2, max_length=100)
    municipality: str = Field(min_length=2, max_length=100)
    project_address: str = Field(min_length=5, max_length=250)
    occupancy: str = Field(min_length=1, max_length=100)
    building_type: str = Field(min_length=2, max_length=100)
    construction_type: str = Field(min_length=1, max_length=100)
    building_height_ft: float | None = Field(default=None, gt=0, le=10000, allow_inf_nan=False)
    building_area_sqft: float | None = Field(default=None, gt=0, le=1e9, allow_inf_nan=False)
    ibc_edition: str = Field(max_length=30)
    nfpa101_edition: str = Field(max_length=30)
    ibc_applicability_confirmed: bool = False
    nfpa101_applicability_confirmed: bool = False
    local_amendments_reviewed_no_conflict: bool = False
    adoption_reference: str = Field(default="", max_length=1000)
    reviewer_name: str = Field(default="", max_length=150)


class BuildingCodeMeasurements(BaseModel):
    egress_factor_basis: Literal["standard_confirmed", "sprinkler_voice_exception_confirmed", "unknown_or_other"] = "unknown_or_other"
    qualifying_sprinkler_system_confirmed: bool | None = None
    qualifying_voice_alarm_confirmed: bool | None = None
    other_egress_exceptions_excluded: bool | None = None
    stair_occupant_load: int | None = Field(default=None, gt=0, le=1000000, strict=True)
    stair_clear_width_in: float | None = Field(default=None, gt=0, le=100000, allow_inf_nan=False)
    other_occupant_load: int | None = Field(default=None, gt=0, le=1000000, strict=True)
    other_clear_width_in: float | None = Field(default=None, gt=0, le=100000, allow_inf_nan=False)
    emergency_lighting_required_confirmed: bool | None = None
    floor_level_egress_photometry_confirmed: bool | None = None
    emergency_duration_minutes: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    initial_average_fc: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    initial_minimum_fc: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    final_average_fc: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    final_minimum_fc: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    measured_maximum_fc: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)
    measured_minimum_fc: float | None = Field(default=None, ge=0, le=100000, allow_inf_nan=False)


class NewBuildingCodeAssessment(BaseModel):
    project_id: UUID
    source_file_id: UUID | None = None
    jurisdiction: BuildingCodeJurisdiction
    measurements: BuildingCodeMeasurements


@router.post("/building-code-measurements", status_code=201)
async def create_building_code_measurement_assessment(
    body: NewBuildingCodeAssessment, user: dict = Depends(require_auth),
):
    """Save versioned IBC/NFPA numerical findings for professional review."""
    pid = str(body.project_id)
    await _owned_nonsovereign_project(pid, user)
    source_id = str(body.source_file_id) if body.source_file_id else None
    if source_id:
        evidence = await get_file(source_id, user)
        if not evidence or str(evidence.get("project_id") or "") != pid:
            raise HTTPException(status_code=404, detail="Evidence file not found in this project")
        if evidence.get("archived_at"):
            raise HTTPException(status_code=409, detail="Cannot cite an archived evidence file")
    context = body.jurisdiction.model_dump()
    measurements = body.measurements.model_dump()
    result = evaluate_building_code_measurements(
        context=context, measurements=measurements, source_file_id=source_id,
    )
    payload = {
        "project_id": pid, "source_file_id": source_id,
        "created_by": user["user_id"], "jurisdiction": context,
        "measurements": measurements, "result": result,
        "review_status": "pending_qualified_review",
    }
    try:
        response = await run_in_threadpool(
            lambda: db.table("compliance_assessments").insert(payload).execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Code assessment could not be saved") from exc
    if not response or not response.data:
        raise HTTPException(status_code=503, detail="Code assessment was not persisted")
    return response.data[0]
