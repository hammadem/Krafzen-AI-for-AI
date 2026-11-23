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
