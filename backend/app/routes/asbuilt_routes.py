"""Authenticated, project-bound DXF as-built comparisons with persisted results."""
import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.db.queries.file_queries import get_file
from app.db.queries.project_queries import get_project
from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.services.asbuilt_service import MAX_DXF_BYTES, compare_dxf_bytes
from app.services.asbuilt_pdf_service import generate_asbuilt_comparison_pdf
from app.utils.storage_service import storage_service

router = APIRouter(prefix="/asbuilt", tags=["As-Built"])


class ReferencePoint(BaseModel):
    x: float = Field(ge=-1e8, le=1e8, allow_inf_nan=False)
    y: float = Field(ge=-1e8, le=1e8, allow_inf_nan=False)


class ManualAlignment(BaseModel):
    original: ReferencePoint
    revised: ReferencePoint
    same_reference_point_confirmed: bool


class CompareRequest(BaseModel):
    project_id: UUID
    original_file_id: UUID
    revised_file_id: UUID
    alignment: ManualAlignment | None = None


async def _owned_project(project_id: str, user: dict) -> dict:
    project = await get_project(project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # This path uses the central storage/database. No regional fallback.
    if project.get("workspace_id"):
        raise HTTPException(
            status_code=503,
            detail="Sovereign organization comparisons require verified regional processing",
        )
    return project


async def _read_dxf(file_id: str, project_id: str, user: dict) -> bytes:
    file = await get_file(file_id, user)
    if not file or str(file.get("project_id") or "") != project_id:
        raise HTTPException(status_code=404, detail="Owned drawing not found in this project")
    if str(file.get("file_type") or "").lower() != "dxf":
        raise HTTPException(status_code=415, detail="Only imported DXF drawings can be compared")
    path = file.get("path")
    client, bucket, region = storage_service.resolve_target_bucket_and_client(None)
    prefix = f"{user['user_id']}/{project_id}/"
    if (
        region != "global" or file.get("bucket") != bucket
        or not isinstance(path, str) or not path.startswith(prefix)
        or any(part in ("", ".", "..") for part in path.split("/"))
        or "\\" in path
    ):
        raise HTTPException(status_code=409, detail="Unsafe or nonregional drawing storage reference")
    if int(file.get("size_bytes") or 0) > MAX_DXF_BYTES:
        raise HTTPException(status_code=413, detail="Drawing exceeds supported size")
    try:
        content = await run_in_threadpool(
            lambda: client.storage.from_(bucket).download(path)
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Cannot retrieve source drawing") from exc
    if not isinstance(content, bytes) or not content or len(content) > MAX_DXF_BYTES:
        raise HTTPException(status_code=503, detail="Source drawing bytes are unavailable or oversized")
    return content


@router.post("/compare", status_code=201)
async def compare_project_drawings(
    request: CompareRequest,
    user: dict = Depends(require_auth),
):
    """Store an evidence-backed diff, not a claim of construction compliance."""
    pid = str(request.project_id)
    original_id = str(request.original_file_id)
    revised_id = str(request.revised_file_id)
    if original_id == revised_id:
        raise HTTPException(status_code=422, detail="Select two different imported DXF files")
    if request.alignment is not None and not request.alignment.same_reference_point_confirmed:
        raise HTTPException(status_code=422, detail="Common drawing reference point confirmation is required")
    await _owned_project(pid, user)
    original = await _read_dxf(original_id, pid, user)
    revised = await _read_dxf(revised_id, pid, user)

    try:
        result = await asyncio.wait_for(
            run_in_threadpool(
                lambda: compare_dxf_bytes(
                    original, revised,
                    alignment=request.alignment.model_dump() if request.alignment else None,
                )
            ),
            timeout=45,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=503, detail="Drawing comparison exceeded 45 seconds") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    row = {
        "project_id": pid,
        "original_file_id": original_id,
        "revised_file_id": revised_id,
        "created_by": user["user_id"],
        "result": result,
    }
    try:
        response = await run_in_threadpool(
            lambda: db.table("asbuilt_comparisons").insert(row).execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Comparison could not be persisted") from exc
    if not response or not response.data:
        raise HTTPException(status_code=503, detail="Comparison was not saved")
    return response.data[0]


@router.get("/projects/{project_id}/comparisons")
async def list_project_comparisons(
    project_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    user: dict = Depends(require_auth),
):
    pid = str(project_id)
    await _owned_project(pid, user)
    try:
        response = await run_in_threadpool(
            lambda: db.table("asbuilt_comparisons")
            .select("*")
            .eq("project_id", pid)
            .eq("created_by", user["user_id"])
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Saved comparisons are unavailable") from exc
    return response.data if response and response.data else []


@router.get("/comparisons/{comparison_id}")
async def read_saved_comparison(
    comparison_id: UUID,
    user: dict = Depends(require_auth),
):
    try:
        response = await run_in_threadpool(
            lambda: db.table("asbuilt_comparisons")
            .select("*")
            .eq("id", str(comparison_id))
            .eq("created_by", user["user_id"])
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Saved comparison is unavailable") from exc
    row = response.data if response else None
    if not row:
        raise HTTPException(status_code=404, detail="Saved comparison not found")
    await _owned_project(str(row["project_id"]), user)
    return row


@router.get("/comparisons/{comparison_id}/report.pdf")
async def download_saved_comparison_pdf(
    comparison_id: UUID,
    user: dict = Depends(require_auth),
):
    """Download a factual PDF generated only from this user's persisted diff.

    Reuses the saved-comparison ownership, project ACL and sovereign-region
    guard; no user-supplied report body or invented field observations.
    """
    record = await read_saved_comparison(comparison_id, user=user)
    try:
        content = await asyncio.wait_for(
            run_in_threadpool(generate_asbuilt_comparison_pdf, record),
            timeout=20,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=503, detail="As-built report timed out") from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409, detail="Saved as-built comparison cannot be verified"
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="As-built PDF unavailable") from exc
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="krafzen_asbuilt_{comparison_id}.pdf"'
            ),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
