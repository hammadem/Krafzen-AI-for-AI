"""Bounded, authenticated DXF ingestion with required anti-malware scanning.

Only ASCII DXF is supported in this initial implementation. This service is
deliberately fail-closed when ClamAV is unavailable; extension/MIME checks
and ezdxf parsing are NOT substitutes for malware scanning.
"""

import asyncio
import hashlib
import json
import os
import sys
import importlib.util
import shutil
import subprocess
import tempfile
from threading import Lock
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
MAX_IFC_BYTES = 40 * 1024 * 1024
SCAN_TIMEOUT_SECONDS = 60
_scan_slot = Lock()
IFC_PARSE_TIMEOUT_SECONDS = 90


def _scan_file(path: Path) -> None:
    """Scan uploaded bytes. No parser is allowed to run before a clean scan."""
    scanner = shutil.which(os.getenv("CLAMSCAN_CMD", "clamscan"))
    if not scanner:
        raise HTTPException(
            status_code=503, detail="Import scanner is not configured; upload rejected."
        )
    if not _scan_slot.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="Scanner is busy; retry later.")
    try:
        scan = subprocess.run(
            [scanner, "--no-summary", "--official-db-only=yes", "--fail-if-cvd-older-than=3",
             "--max-filesize=50M", "--max-scansize=150M", "--alert-exceeds-max=yes",
             "--alert-encrypted=yes", str(path)],
            capture_output=True,
            text=True,
            timeout=SCAN_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HTTPException(
            status_code=503, detail="Import scanner unavailable or timed out."
        ) from exc
    finally:
        _scan_slot.release()
    if scan.returncode == 1:
        raise HTTPException(status_code=422, detail="Upload rejected by malware scanner or scan safety limits.")
    if scan.returncode != 0:
        raise HTTPException(status_code=503, detail="Import scanner could not validate the file.")


def _scan_and_validate(data: bytes) -> None:
    """Scan and validate a source DXF, refusing empty modelspace."""
    with tempfile.TemporaryDirectory(prefix="krafzen-import-") as tmpdir:
        path = Path(tmpdir) / "upload.dxf"
        path.write_bytes(data)
        _scan_file(path)
        try:
            document = ezdxf.readfile(path)
            if not any(True for _ in document.modelspace()):
                raise ValueError("No modelspace geometry")
        except (ezdxf.DXFError, OSError, UnicodeDecodeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="Invalid or empty DXF drawing.") from exc


def _scan_ifc_and_extract_metadata(data: bytes) -> dict:
    """Scan an IFC and parse its real entities in a time-bounded child process."""
    if not data.lstrip().startswith(b"ISO-10303-21;") or b"END-ISO-10303-21;" not in data[-256:]:
        raise HTTPException(status_code=422, detail="Malformed IFC STEP envelope")
    if importlib.util.find_spec("ifcopenshell") is None:
        raise HTTPException(status_code=503, detail="IFC parser is not installed")
    with tempfile.TemporaryDirectory(prefix="krafzen-ifc-") as tmpdir:
        path = Path(tmpdir) / "upload.ifc"
        path.write_bytes(data)
        _scan_file(path)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "app.services.ifc_inspection", str(path)],
                capture_output=True,
                text=True,
                timeout=IFC_PARSE_TIMEOUT_SECONDS,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HTTPException(status_code=503, detail="IFC processing unavailable or timed out") from exc

        if result.returncode < 0:
            raise HTTPException(status_code=503, detail="IFC model processing failed")
        if result.returncode != 0:
            raise HTTPException(status_code=422, detail="Invalid or unsupported IFC model")
        try:
            summary = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            raise HTTPException(status_code=503, detail="IFC parser returned invalid metadata") from exc
        if not isinstance(summary, dict) or summary.get("type") != "ifc":
            raise HTTPException(status_code=503, detail="IFC model metadata is unavailable")
        return summary


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


async def import_ifc_for_job(
    *, job_id: str, upload: UploadFile, user: dict, revit_provenance: dict | None = None
) -> dict:
    """Import a genuine IFC model and persist parsed model metadata."""
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
    # Sovereign org projects require region-isolated scanner and persistence.
    if project.get("workspace_id"):
        raise HTTPException(
            status_code=503, detail="Organization imports require verified regional processing."
        )

    original = upload.filename or ""
    if (not original or "/" in original or "\\" in original
            or not original.lower().endswith(".ifc")):
        raise HTTPException(status_code=415, detail="Only .ifc BIM models are supported")

    data = await upload.read(MAX_IFC_BYTES + 1)
    if not data:
        raise HTTPException(status_code=422, detail="IFC file is empty")
    if len(data) > MAX_IFC_BYTES:
        raise HTTPException(status_code=413, detail="IFC file exceeds 40 MB")

    summary = await run_in_threadpool(_scan_ifc_and_extract_metadata, data)
    if revit_provenance:
        summary["revit_source"] = {**revit_provenance, "ifc_sha256": hashlib.sha256(data).hexdigest()}
    user_id = str(user["user_id"])
    filename = f"import_{uuid.uuid4().hex}.ifc"
    storage_path = f"{user_id}/{project_id}/imports/{job_id}/{filename}"
    client, bucket, region = storage_service.resolve_target_bucket_and_client(None)
    if region != "global":
        raise HTTPException(status_code=503, detail="Unexpected storage region")

    try:
        await run_in_threadpool(
            lambda: client.storage.from_(bucket).upload(
                path=storage_path,
                file=data,
                file_options={"content-type": "application/x-step", "upsert": "false"},
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="IFC storage upload failed") from exc

    try:
        record = await create_file(
            {
                "job_id": job_id,
                "project_id": project_id,
                "bucket": bucket,
                "path": storage_path,
                "file_type": "ifc",
                "mime_type": "application/x-step",
                "size_bytes": len(data),
                "name": original,
                "import_metadata": summary,
            },
            user,
        )
        if not record or record.get("error"):
            raise RuntimeError("IFC metadata registration failed")
        return record
    except Exception as exc:
        try:
            await run_in_threadpool(
                lambda: client.storage.from_(bucket).remove([storage_path])
            )
        except Exception:
            pass
        raise HTTPException(status_code=503, detail="IFC import could not be finalized") from exc


async def import_revit_bridge_for_job(*, job_id: str, source: UploadFile, upload: UploadFile, user: dict) -> dict:
    """Accept a local Revit-exported IFC and hash/scan its declared RVT source.

    Neither file is sent to a third party. The relationship is user-declared;
    only Revit can perform native export. We do not claim native RVT parsing.
    """
    if not user or not user.get("user_id"):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        uuid.UUID(str(job_id))
    except (ValueError,TypeError) as exc:
        raise HTTPException(status_code=422,detail="Invalid job ID") from exc
    job = await get_job(job_id,user)
    project = await get_project(str(job["project_id"]),user) if job else None
    if not project:
        raise HTTPException(status_code=404,detail="Project job not found")
    if project.get("workspace_id") or project.get("archived_at"):
        raise HTTPException(status_code=409,detail="Project is archived or requires regional processing")
    filename = source.filename or ""
    if (not filename.lower().endswith(".rvt") or len(filename)>250 or "/" in filename or chr(92) in filename):
        raise HTTPException(status_code=415,detail="Select the original RVT and exported IFC")
    if not (upload.filename or "").lower().endswith(".ifc"):
        raise HTTPException(status_code=415,detail="Export an actual IFC using Autodesk Revit")
    original = await source.read(MAX_IFC_BYTES+1)
    if len(original)>MAX_IFC_BYTES:
        raise HTTPException(status_code=413,detail="RVT source exceeds 40 MB")
    if len(original)<512 or original[:8] != bytes.fromhex("D0CF11E0A1B11AE1"):
        raise HTTPException(status_code=422,detail="Unsupported RVT container signature; native file not verified")
    def scan_source():
        with tempfile.TemporaryDirectory(prefix="krafzen-revit-source-") as folder:
            path = Path(folder)/"source.rvt"
            path.write_bytes(original)
            _scan_file(path)
    await run_in_threadpool(scan_source)
    return await import_ifc_for_job(job_id=job_id,upload=upload,user=user,
        revit_provenance={"source_name":filename,"source_sha256":hashlib.sha256(original).hexdigest(),
            "source_container":"compound_file_signature","conversion_method":"user_declared_local_revit_ifc_export",
            "native_rvt_parsed":False,"source_relationship_independently_verified":False,
            "original_binary_retained":False})


# Document/file classes use the SAME authenticated job/project, malware scanner,
# private bucket, and cleanup transaction as DXF/IFC imports.
DOCUMENT_FORMATS = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "zip": "application/zip",
}
MAX_DOCUMENT_BYTES = 25 * 1024 * 1024
DOCUMENT_PARSE_TIMEOUT_SECONDS = 60


def _scan_and_inspect_document(data: bytes, ext: str) -> dict:
    """Scan first; inspect in a bounded subprocess, never execute uploaded data."""
    with tempfile.TemporaryDirectory(prefix="krafzen-document-") as directory:
        path = Path(directory) / ("upload." + ext)
        path.write_bytes(data)
        _scan_file(path)
        try:
            process = subprocess.run(
                [sys.executable, "-m", "app.services.document_inspection", str(path), ext],
                capture_output=True,
                text=True,
                check=False,
                timeout=DOCUMENT_PARSE_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise HTTPException(
                status_code=503, detail="Document parser unavailable or timed out"
            ) from exc
        if process.returncode != 0:
            raise HTTPException(
                status_code=422,
                detail="Document is malformed, unsafe, encrypted or unsupported",
            )
        try:
            info = json.loads(process.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            raise HTTPException(status_code=503, detail="Document parser returned invalid metadata") from exc
        if not isinstance(info, dict) or info.get("type") != "document" or info.get("format") != ext:
            raise HTTPException(status_code=503, detail="Document metadata could not be verified")
        # Only persisted after an actual malware scan and structured extraction.
        info["malware_scan_completed"] = True
        return info


async def import_document_for_job(
    *, job_id: str, upload: UploadFile, user: dict,
) -> dict:
    """Securely import PDFs, Office files, CSV, images and ZIPs into a real job."""
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
    if project.get("workspace_id"):
        raise HTTPException(
            status_code=503,
            detail="Organization document imports require verified regional processing",
        )
    name = upload.filename or ""
    if (
        not name or len(name) > 255
        or "/" in name or chr(92) in name
        or name.startswith(".")
        or "." not in name
    ):
        raise HTTPException(status_code=415, detail="Invalid document filename")
    ext = name.rsplit(".", 1)[-1].lower()
    if ext not in DOCUMENT_FORMATS:
        raise HTTPException(status_code=415, detail="Document file format is not supported")
    data = await upload.read(MAX_DOCUMENT_BYTES + 1)
    if not data:
        raise HTTPException(status_code=422, detail="Document is empty")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds 25 MB")

    summary = await run_in_threadpool(_scan_and_inspect_document, data, ext)
    user_id = str(user["user_id"])
    filename = f"import_{uuid.uuid4().hex}.{ext}"
    storage_path = f"{user_id}/{project_id}/imports/{job_id}/{filename}"
    client, bucket, region = storage_service.resolve_target_bucket_and_client(None)
    if region != "global":
        raise HTTPException(status_code=503, detail="Unexpected storage region")
    try:
        await run_in_threadpool(
            lambda: client.storage.from_(bucket).upload(
                path=storage_path,
                file=data,
                file_options={
                    "content-type": DOCUMENT_FORMATS[ext],
                    "upsert": "false",
                },
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Document storage upload failed") from exc
    try:
        record = await create_file(
            {
                "job_id": job_id,
                "project_id": project_id,
                "bucket": bucket,
                "path": storage_path,
                "file_type": ext,
                "mime_type": DOCUMENT_FORMATS[ext],
                "size_bytes": len(data),
                "name": name,
                "import_metadata": summary,
            },
            user,
        )
        if not record or record.get("error"):
            raise RuntimeError("Document metadata registration failed")
        return record
    except Exception as exc:
        try:
            await run_in_threadpool(
                lambda: client.storage.from_(bucket).remove([storage_path])
            )
        except Exception:
            pass
        raise HTTPException(status_code=503, detail="Document import could not be finalized") from exc
