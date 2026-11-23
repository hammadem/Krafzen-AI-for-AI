"""Project-owned, source-derived IFC triangle mesh for real 3-D viewing."""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.db.queries.file_queries import get_file
from app.db.queries.project_queries import get_project
from app.middlewares.auth import require_auth
from app.utils.storage_service import storage_service

router = APIRouter(prefix="/bim", tags=["IFC 3D Geometry"])
MAX_IFC_BYTES = 40 * 1024 * 1024
MAX_MESH_JSON_BYTES = 8 * 1024 * 1024


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


@router.get("/files/{file_id}/mesh")
async def get_model_mesh(file_id: UUID, user: dict = Depends(require_auth)):
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

    mesh = await run_in_threadpool(_extract_bounded_mesh, raw)
    return {
        "file_id": str(file_id),
        "project_id": project_id,
        "mesh": mesh,
    }
