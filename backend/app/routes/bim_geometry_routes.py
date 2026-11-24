"""Project-owned, source-derived IFC triangle mesh for real 3-D viewing."""
import importlib.util
import asyncio
from hashlib import sha256
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.db.queries.file_queries import get_file
from app.db.queries.project_queries import get_project
from app.db.supabase_client import db
from app.services.ifc_spatial_screen import screen_ifc_mesh_overlap
from app.services.ifc_revision_service import compare_ifc_mesh_revisions
from app.middlewares.auth import require_auth
from app.utils.storage_service import storage_service

router = APIRouter(prefix="/bim", tags=["IFC 3D Geometry"])
MAX_IFC_BYTES = 40 * 1024 * 1024
MAX_MESH_JSON_BYTES = 8 * 1024 * 1024
MAX_COORDINATION_PAIR_BYTES = 20 * 1024 * 1024
_coordination_slot = asyncio.Semaphore(1)


def _extract_bounded_mesh(raw: bytes) -> dict:
    """Parse untrusted IFC in native-code subprocess, with hard memory+time caps."""
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_IFC_BYTES:
        raise HTTPException(status_code=413, detail="IFC mesh source exceeds 40 MB")
    if (not raw.lstrip().startswith(b"ISO-10303-21;")
        or b"END-ISO-10303-21;" not in raw[-256:]):
        raise HTTPException(status_code=422, detail="Invalid IFC STEP document")
    if importlib.util.find_spec("ifcopenshell") is None:
        raise HTTPException(status_code=503, detail="IFC geometry engine unavailable")
    with tempfile.TemporaryDirectory(prefix="krafzen-mesh-") as folder:
        path = Path(folder) / "source.ifc"
        path.write_bytes(raw)
        try:
            process = subprocess.run(
                [sys.executable, "-m", "app.services.ifc_mesh_extraction", str(path)],
                capture_output=True, check=False, timeout=90,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HTTPException(status_code=503, detail="IFC geometry calculation timed out") from exc
    if process.returncode != 0:
        raise HTTPException(
            status_code=422, detail="Model has no supported tessellated IFC geometry"
        )
    if len(process.stdout) > MAX_MESH_JSON_BYTES:
        raise HTTPException(status_code=413, detail="Mesh exceeds view size")
    try:
        data = json.loads(process.stdout)
    except (ValueError, UnicodeError) as exc:
        raise HTTPException(status_code=503, detail="IFC geometry engine returned invalid data") from exc
    if (not isinstance(data, dict) or data.get("type") != "ifc_true_mesh" or
        not isinstance(data.get("elements"), list) or not data["elements"]):
        raise HTTPException(status_code=503, detail="Real IFC geometry was not returned")
    return data


async def _read_verified_ifc(file_id: UUID, user: dict):
    record = await get_file(str(file_id), user)
    if not record:
        raise HTTPException(status_code=404, detail="IFC file not found")
    if str(record.get("file_type") or "").lower() != "ifc":
        raise HTTPException(status_code=415, detail="File is not an IFC model")
    project_id = str(record.get("project_id") or "")
    project = await get_project(project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("workspace_id"):
        raise HTTPException(
            status_code=503,
            detail="Organization 3D models need verified regional geometry processing",
        )
    summary = record.get("import_metadata")
    if not isinstance(summary, dict) or summary.get("type") != "ifc":
        raise HTTPException(
            status_code=409,
            detail="Model has no verified scanned IFC import metadata",
        )

    path = record.get("path")
    job_id = str(record.get("job_id") or "")
    expected = f"{user['user_id']}/{project_id}/imports/{job_id}/"
    client, bucket, region = storage_service.resolve_target_bucket_and_client(None)
    if (region != "global" or record.get("bucket") != bucket
        or not isinstance(path, str) or not path.startswith(expected)
        or not path.lower().endswith(".ifc")
        or chr(92) in path
        or any(segment in ("", ".", "..") for segment in path.split("/"))):
        raise HTTPException(status_code=409, detail="Unsafe IFC source storage reference")
    size = record.get("size_bytes")
    if not isinstance(size, int) or size <= 0 or size > MAX_IFC_BYTES:
        raise HTTPException(status_code=413, detail="IFC source size is invalid")
    try:
        raw = await run_in_threadpool(
            lambda: client.storage.from_(bucket).download(path)
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Cannot read stored IFC source") from exc
    if not isinstance(raw, bytes) or len(raw) != size:
        raise HTTPException(status_code=503, detail="Stored IFC size or bytes mismatch")

    return project_id, raw


@router.get("/files/{file_id}/mesh")
async def get_model_mesh(file_id: UUID, user: dict = Depends(require_auth)):
    project_id, raw = await _read_verified_ifc(file_id, user)
    mesh = await run_in_threadpool(_extract_bounded_mesh, raw)
    return {
        "file_id": str(file_id),
        "project_id": project_id,
        "source_sha256": sha256(raw).hexdigest(),
        "mesh": mesh,
    }


def _native_coordination(first: bytes, second: bytes, clearance_m: float) -> dict:
    if len(first) + len(second) > MAX_COORDINATION_PAIR_BYTES:
        raise HTTPException(status_code=413, detail="IFC coordination pair exceeds 20 MB")
    for raw in (first, second):
        if (not raw.lstrip().startswith(b"ISO-10303-21;")
            or b"END-ISO-10303-21;" not in raw[-256:]):
            raise HTTPException(status_code=422, detail="Invalid IFC STEP document")
    if importlib.util.find_spec("ifcopenshell") is None:
        raise HTTPException(status_code=503, detail="Native IFC geometry engine unavailable")
    with tempfile.TemporaryDirectory(prefix="krafzen-coordination-") as folder:
        a, b = Path(folder) / "a.ifc", Path(folder) / "b.ifc"
        a.write_bytes(first)
        b.write_bytes(second)
        try:
            process = subprocess.run(
                [sys.executable, "-m", "app.services.ifc_native_coordination",
                 str(a), str(b), str(clearance_m)],
                capture_output=True, check=False, timeout=90,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HTTPException(status_code=503, detail="Native IFC coordination timed out") from exc
    if process.returncode != 0 or len(process.stdout) > MAX_MESH_JSON_BYTES:
        raise HTTPException(status_code=422, detail="Native IFC coordination could not process these models")
    try:
        result = json.loads(process.stdout)
    except (ValueError, UnicodeError) as exc:
        raise HTTPException(status_code=503, detail="Native IFC coordination returned invalid data") from exc
    if not isinstance(result, dict) or result.get("method") != "ifcopenshell_native_intersection_clearance_v1":
        raise HTTPException(status_code=503, detail="Native IFC coordination evidence missing")
    return result


class SpatialScreenRequest(BaseModel):
    primary_file_id: UUID
    secondary_file_id: UUID
    same_origin_axes_and_scale_confirmed: bool = False
    mode: Literal["broad_phase", "native_coordination", "revision_comparison"] = "broad_phase"
    clearance_m: float = Field(default=0.05, ge=0.001, le=1, allow_inf_nan=False)


@router.post("/projects/{project_id}/spatial-screens", status_code=201)
async def screen_project_ifc_spatial_overlap(
    project_id: UUID,
    request: SpatialScreenRequest,
    user: dict = Depends(require_auth),
):
    """Persist selected broad-phase or native geometry review findings.

    Both modes require project-owned scanned IFC sources and asserted alignment.
    Neither certifies physical construction or independent model registration.
    """
    pid = str(project_id)
    a_id = str(request.primary_file_id)
    b_id = str(request.secondary_file_id)
    if a_id == b_id:
        raise HTTPException(status_code=422, detail="Choose two different IFC files")
    if not request.same_origin_axes_and_scale_confirmed:
        raise HTTPException(
            status_code=422,
            detail="Confirm that both IFC files use the same origin, axes and scale",
        )
    project = await get_project(pid, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("workspace_id"):
        raise HTTPException(
            status_code=503,
            detail="Regional BIM coordination processing is not verified",
        )

    # Verify BOTH source files belong to the chosen project before spawning
    # costly IFC tessellation and before making any result persistent.
    for file_id in (a_id, b_id):
        file_row = await get_file(file_id, user)
        if not file_row or str(file_row.get("project_id") or "") != pid:
            raise HTTPException(status_code=404, detail="Project IFC source not found")
        if str(file_row.get("file_type") or "").lower() != "ifc":
            raise HTTPException(status_code=415, detail="Only IFC sources can be screened")

    if request.mode == "native_coordination":
        if _coordination_slot.locked():
            raise HTTPException(status_code=429, detail="Another native IFC calculation is running")
        async with _coordination_slot:
            source_pid, source_raw = await _read_verified_ifc(request.primary_file_id, user)
            target_pid, target_raw = await _read_verified_ifc(request.secondary_file_id, user)
            if source_pid != pid or target_pid != pid:
                raise HTTPException(status_code=404, detail="Project IFC source mismatch")
            result = await run_in_threadpool(
                _native_coordination, source_raw, target_raw, request.clearance_m
            )
            result["source_files"] = [
                {"file_id": a_id, "sha256": sha256(source_raw).hexdigest()},
                {"file_id": b_id, "sha256": sha256(target_raw).hexdigest()},
            ]
            for finding in result["candidates"]:
                finding["source"]["file_id"] = a_id
                finding["target"]["file_id"] = b_id
    elif request.mode == "revision_comparison":
        if _coordination_slot.locked():
            raise HTTPException(status_code=429, detail="Another IFC calculation is running")
        async with _coordination_slot:
            source = await get_model_mesh(request.primary_file_id, user=user)
            target = await get_model_mesh(request.secondary_file_id, user=user)
            if source["project_id"] != pid or target["project_id"] != pid:
                raise HTTPException(status_code=404, detail="Project IFC source mismatch")
            result = await run_in_threadpool(compare_ifc_mesh_revisions, source["mesh"], target["mesh"])
            result["source_files"] = [
                {"file_id": a_id, "sha256": source["source_sha256"]},
                {"file_id": b_id, "sha256": target["source_sha256"]},
            ]
    else:
        source = await get_model_mesh(request.primary_file_id, user=user)
        target = await get_model_mesh(request.secondary_file_id, user=user)
        if source["project_id"] != pid or target["project_id"] != pid:
            raise HTTPException(status_code=404, detail="Project IFC source mismatch")
        try:
            result = await asyncio.wait_for(
                run_in_threadpool(
                    screen_ifc_mesh_overlap,
                    source["mesh"], target["mesh"],
                    primary_file_id=a_id,
                    secondary_file_id=b_id,
                    primary_sha256=source["source_sha256"],
                    secondary_sha256=target["source_sha256"],
                ),
                timeout=15,
            )
        except asyncio.TimeoutError as exc:
            raise HTTPException(status_code=503, detail="IFC screening timed out") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    row = {
        "project_id": pid,
        "primary_file_id": a_id,
        "secondary_file_id": b_id,
        "created_by": str(user["user_id"]),
        "alignment_user_asserted": True,
        "result": result,
    }
    try:
        persisted = await run_in_threadpool(
            lambda: db.table("bim_spatial_screenings").insert(row).execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail="BIM screening could not be saved"
        ) from exc
    if not persisted or not persisted.data:
        raise HTTPException(status_code=503, detail="BIM screening was not persisted")
    return persisted.data[0]


@router.get("/projects/{project_id}/spatial-screens")
async def list_project_ifc_spatial_screens(
    project_id: UUID,
    user: dict = Depends(require_auth),
):
    pid = str(project_id)
    project = await get_project(pid, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.get("workspace_id"):
        raise HTTPException(
            status_code=503, detail="Regional BIM screening access is not verified"
        )
    try:
        rows = await run_in_threadpool(
            lambda: db.table("bim_spatial_screenings").select("*")
            .eq("project_id", pid)
            .eq("created_by", str(user["user_id"]))
            .order("created_at", desc=True).limit(50).execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="BIM screening history unavailable") from exc
    return rows.data if rows and rows.data else []
