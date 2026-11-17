"""Bounded, authenticated DXF ingestion with required anti-malware scanning.

Only ASCII DXF is supported in this initial implementation. This service is
deliberately fail-closed when ClamAV is unavailable; extension/MIME checks
and ezdxf parsing are NOT substitutes for malware scanning.
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import ezdxf
from fastapi import HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.db.queries.file_queries import create_file
from app.db.queries.job_queries import get_job
from app.db.queries.project_queries import get_project
from app.utils.storage_service import storage_service

MAX_DXF_BYTES = 25 * 1024 * 1024
SCAN_TIMEOUT_SECONDS = 60


def _scan_and_validate(data: bytes) -> None:
    """Validate nonempty vector entities and require a successful ClamAV scan."""
    with tempfile.TemporaryDirectory(prefix="krafzen-import-") as tmpdir:
        path = Path(tmpdir) / "upload.dxf"
        path.write_bytes(data)

        scanner = shutil.which(os.getenv("CLAMSCAN_CMD", "clamscan"))
        if not scanner:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Import scanner is not configured; upload rejected.",
            )
        try:
            scan = subprocess.run(
                [scanner, "--no-summary", str(path)],
                capture_output=True,
                text=True,
                timeout=SCAN_TIMEOUT_SECONDS,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Import scanner unavailable or timed out.",
            ) from exc
        if scan.returncode == 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Upload rejected by malware scanner.",
            )
        if scan.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Import scanner could not validate the file.",
            )

        try:
            document = ezdxf.readfile(path)
            # Reject DXF containers that lack editable vector geometry.
            if not any(True for _ in document.modelspace()):
                raise ValueError("No modelspace geometry")
        except (ezdxf.DXFError, OSError, UnicodeDecodeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid or empty DXF drawing.",
            ) from exc


async def import_dxf_for_job(
    *, job_id: str, upload: UploadFile, user: dict
) -> dict:
    """Upload a validated drawing to a unique, job-scoped storage path."""
    if not user or not user.get("user_id"):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        uuid.UUID(str(job_id))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Invalid job ID") from exc

    job = await get_job(job_id, user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    project_id = str(job.get("project_id") or "")
    project = await get_project(project_id, user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Sovereign tenants require an isolated regional import pipeline. Until
    # region-specific metadata and scanning are verified, do not cross regions.
    if project.get("workspace_id"):
        raise HTTPException(
            status_code=503,
            detail="Organization imports require verified regional processing.",
        )

    original = upload.filename or ""
    if (not original or "/" in original or "\\" in original
            or not original.lower().endswith(".dxf")):
        raise HTTPException(status_code=415, detail="Only .dxf drawings are supported")

    data = await upload.read(MAX_DXF_BYTES + 1)
    if not data:
        raise HTTPException(status_code=422, detail="The drawing file is empty")
    if len(data) > MAX_DXF_BYTES:
        raise HTTPException(status_code=413, detail="DXF file exceeds 25 MB")
    if data.startswith(b"AutoCAD Binary DXF") or b"\x00" in data[:1024]:
        raise HTTPException(
            status_code=415, detail="Binary DXF is not supported by this importer"
        )

    await run_in_threadpool(_scan_and_validate, data)

    user_id = str(user["user_id"])
    new_name = f"import_{uuid.uuid4().hex}.dxf"
    storage_path = f"{user_id}/{project_id}/imports/{job_id}/{new_name}"
    storage_client, bucket, region = storage_service.resolve_target_bucket_and_client(None)
    if region != "global":
        raise HTTPException(status_code=503, detail="Unexpected storage region")

    try:
        await run_in_threadpool(
            lambda: storage_client.storage.from_(bucket).upload(
                path=storage_path,
                file=data,
                file_options={"content-type": "application/dxf", "upsert": "false"},
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="DXF storage upload failed") from exc

    try:
        record = await create_file(
            {
                "job_id": job_id,
                "project_id": project_id,
                "bucket": bucket,
                "path": storage_path,
                "file_type": "dxf",
                "mime_type": "application/dxf",
                "size_bytes": len(data),
                "name": original,
            },
            user,
        )
        if not record or record.get("error"):
            raise RuntimeError("File metadata registration failed")
        return record
    except Exception as exc:
        try:
            await run_in_threadpool(
                lambda: storage_client.storage.from_(bucket).remove([storage_path])
            )
        except Exception:
            # Cleanup requires operator follow-up; preserve the real failure.
            pass
        raise HTTPException(status_code=503, detail="Import could not be finalized") from exc
