"""Paid, authenticated parametric drawing generation from explicit dimensions."""
import hashlib
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.db.queries.file_queries import create_file, get_file
from app.routes.asbuilt_routes import _read_dxf
from app.services.cad_command_service import propose_room_edit
from app.db.queries.job_queries import get_job
from app.db.queries.project_queries import get_project
from app.middlewares.auth import require_auth
from app.services.activity_service import record_audit_event
from app.services.parametric_cad_service import build_room_dxf
from app.utils.storage_service import storage_service

router = APIRouter(prefix="/cad", tags=["CAD Generation"])


class OpeningRequest(BaseModel):
    kind: str
    side: str
    offset_m: float = Field(gt=0, allow_inf_nan=False)
    clear_width_m: float = Field(gt=0, allow_inf_nan=False)


class RoomRequest(BaseModel):
    project_id: UUID
    job_id: UUID
    room_name: str = Field(min_length=1, max_length=80)
    exterior_width_m: float = Field(ge=1, le=100, allow_inf_nan=False)
    exterior_length_m: float = Field(ge=1, le=100, allow_inf_nan=False)
    wall_thickness_m: float = Field(gt=0, le=5, allow_inf_nan=False)
    openings: list[OpeningRequest] = Field(default_factory=list, max_length=20)


@router.post("/rooms", status_code=201)
async def create_parametric_room_drawing(
    payload: RoomRequest,
    user: dict = Depends(require_auth),
):
    """Generate, persist and return real unit-tagged DXF modelspace geometry."""
    return await _persist_room(payload,user)


async def _persist_room(payload: RoomRequest, user: dict, source: dict | None = None):
    project_id = str(payload.project_id)
    job_id = str(payload.job_id)
    job = await get_job(job_id, user)
    if not job or str(job.get("project_id") or "") != project_id:
        raise HTTPException(status_code=404, detail="Project job not found")
    project = await get_project(project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("archived_at"):
        raise HTTPException(status_code=409, detail="Restore the project before generating a drawing")
    if project.get("workspace_id"):
        raise HTTPException(
            status_code=503,
            detail="Organization CAD generation requires verified regional processing",
        )

    try:
        raw, geometry = await run_in_threadpool(
            build_room_dxf,
            name=payload.room_name,
            width_m=payload.exterior_width_m,
            length_m=payload.exterior_length_m,
            wall_thickness_m=payload.wall_thickness_m,
            openings=[opening.model_dump() for opening in payload.openings],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Generated DXF exceeds file limit")
    user_id = str(user["user_id"])
    filename = f"room_{uuid4().hex}.dxf"
    path = f"{user_id}/{project_id}/generated/{job_id}/{filename}"
    client, bucket, region = storage_service.resolve_target_bucket_and_client(None)
    if region != "global":
        raise HTTPException(status_code=503, detail="Unexpected CAD storage region")
    try:
        await run_in_threadpool(
            lambda: client.storage.from_(bucket).upload(
                path=path,
                file=raw,
                file_options={"content-type": "application/dxf", "upsert": "false"},
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="CAD drawing storage unavailable") from exc

    geometry["source_sha256"] = hashlib.sha256(raw).hexdigest()
    if source:
        geometry["parent_file_id"] = str(source["id"])
        geometry["parent_source_sha256"] = source["import_metadata"]["source_sha256"]
    try:
        record = await create_file(
            {
                "job_id": job_id,
                "project_id": project_id,
                "bucket": bucket,
                "path": path,
                "file_type": "dxf",
                "mime_type": "application/dxf",
                "size_bytes": len(raw),
                "name": f"{payload.room_name.strip()}.dxf",
                "import_metadata": geometry,
                "version": int(source.get("version") or 1)+1 if source else 1,
            },
            user,
        )
        if not record or record.get("error"):
            raise RuntimeError("CAD drawing metadata could not be saved")
    except Exception as exc:
        try:
            await run_in_threadpool(lambda: client.storage.from_(bucket).remove([path]))
        except Exception:
            pass
        raise HTTPException(status_code=503, detail="CAD drawing could not be persisted") from exc
    # Audit is best effort; storage and project metadata are authoritative.
    try:
        await record_audit_event(
            action="cad.room_generated", entity_type="file",
            entity_id=str(record["id"]), actor_user_id=user_id,
            project_id=project_id,
            metadata={"generation_method": "parametric_room_v1"},
        )
    except Exception:
        pass
    return {"file": record, "geometry": geometry}

class RoomEditRequest(BaseModel):
    command: str = Field(min_length=1,max_length=500)
    expected_sha256: str | None = Field(default=None,pattern=r"^[0-9a-f]{64}$")


async def _source_edit(file_id: UUID, payload: RoomEditRequest, user: dict):
    source=await get_file(str(file_id),user)
    if not source or source.get("archived_at"):
        raise HTTPException(status_code=404,detail="Active drawing not found")
    project=await get_project(str(source["project_id"]),user)
    if not project or project.get("archived_at") or project.get("workspace_id"):
        raise HTTPException(status_code=409,detail="Drawing project is archived or regional processing unavailable")
    metadata=source.get("import_metadata")
    if not isinstance(metadata,dict) or metadata.get("generation_method")!="parametric_room_v1":
        raise HTTPException(status_code=422,detail="Select a generated parametric room drawing")
    raw=await _read_dxf(str(file_id),str(source["project_id"]),user)
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=metadata.get("source_sha256") or (payload.expected_sha256 and digest!=payload.expected_sha256):
        raise HTTPException(status_code=409,detail="Source drawing integrity or preview version mismatch")
    try:
        data,geometry=await run_in_threadpool(propose_room_edit,metadata,payload.command)
        validated=RoomRequest(project_id=source["project_id"],job_id=source["job_id"],**data)
    except (KeyError,TypeError,ValueError) as exc:
        raise HTTPException(status_code=422,detail=str(exc)[:500]) from exc
    return source,digest,validated,geometry


@router.post("/rooms/{file_id}/edit-preview")
async def preview_room_edit(file_id:UUID,payload:RoomEditRequest,user:dict=Depends(require_auth)):
    source,digest,validated,geometry=await _source_edit(file_id,payload,user)
    return {"file_id":str(file_id),"source_sha256":digest,"geometry":geometry,"command":payload.command,
            "requires_confirmation":True}


@router.post("/rooms/{file_id}/edit",status_code=201)
async def apply_room_edit(file_id:UUID,payload:RoomEditRequest,user:dict=Depends(require_auth)):
    if not payload.expected_sha256:
        raise HTTPException(status_code=422,detail="Confirm a source-bound edit preview first")
    source,digest,validated,geometry=await _source_edit(file_id,payload,user)
    return await _persist_room(validated,user,source)
