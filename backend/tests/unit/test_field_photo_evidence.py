"""Scanned, EXIF-stripped photo evidence and verified PDF field reports."""
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from fastapi import HTTPException, UploadFile
from PIL import Image
from pypdf import PdfReader
import pytest

from app.routes import field_routes
from app.services.field_evidence_service import (
    generate_field_report_pdf,
    sanitized_photo_bytes,
)

PROJECT = "00000000-0000-0000-0000-000000000002"
INSPECTION = "00000000-0000-0000-0000-000000000003"
PHOTO = "00000000-0000-0000-0000-000000000004"
USER = {"user_id": "00000000-0000-0000-0000-000000000001"}
PATH = f"{USER['user_id']}/{PROJECT}/field/{INSPECTION}/photo_abc.jpg"


def picture(exif_gps=True):
    result = BytesIO()
    picture = Image.new("RGB", (160, 120), color=(120, 50, 30))
    exif = Image.Exif()
    exif[271] = "Sensitive camera device"
    if exif_gps:
        exif[34853] = {1: "N", 2: (51, 1, 20), 3: "W"}
    picture.save(result, format="JPEG", exif=exif)
    return result.getvalue()


async def inline(func, *args, **kwargs):
    return func(*args, **kwargs)


def fake_inspection():
    return {
        "id": INSPECTION, "project_id": PROJECT,
        "created_by": USER["user_id"], "status": "open",
        "title": "Real note", "description": "Observed crack",
    }


def fake_photo_row(*, path=PATH, bucket="dxf-files"):
    return {
        "id": PHOTO, "project_id": PROJECT, "inspection_id": INSPECTION,
        "created_by": USER["user_id"], "bucket": bucket, "path": path,
        "mime_type": "image/jpeg", "size_bytes": 1000,
        "source_metadata": {"malware_scan_completed": True, "exif_gps_removed": True},
    }


def test_real_jpeg_scanned_and_gps_removed():
    original = picture()
    with patch("app.services.field_evidence_service._scan_file") as scan:
        result, metadata = sanitized_photo_bytes(original, "jpg")
    scan.assert_called_once()
    assert result.startswith(bytes([0xff, 0xd8]))
    assert result != original
    with Image.open(BytesIO(result)) as restored:
        assert restored.size == (160, 120)
        assert not restored.getexif()
    assert metadata["malware_scan_completed"] is True
    assert metadata["exif_gps_removed"] is True
    assert metadata["original_sha256"] != metadata["stored_sha256"]
    assert metadata["engineering_defect_confirmed"] is False


@pytest.mark.parametrize("kind", ["jpg", "png", "webp"])
def test_scanner_unauthorized_causes_no_image_decode(kind):
    with (
        patch("app.services.field_evidence_service._scan_file",
              side_effect=HTTPException(status_code=503, detail="Missing scanner")),
        patch("app.services.field_evidence_service.Image.open") as decode,
    ):
        with pytest.raises(HTTPException) as exception:
            sanitized_photo_bytes(b"invalid-file", kind)
    assert exception.value.status_code == 503
    decode.assert_not_called()


def test_invalid_image_extension_or_payload_rejected():
    with pytest.raises(HTTPException) as rejected:
        sanitized_photo_bytes(b"unsafe", "exe")
    assert rejected.value.status_code == 415
    with patch("app.services.field_evidence_service._scan_file"):
        with pytest.raises(HTTPException) as rejected:
            sanitized_photo_bytes(b"invalid JPEG", "jpg")
    assert rejected.value.status_code == 422


def test_genuine_factual_report_pdf_contains_only_stored_observations():
    records = [
        {
            "title": "Actual ramp obstruction",
            "status": "open",
            "severity": "high",
            "discipline": "site",
            "description": "North entrance approach blocked by materials",
            "location_label": "North lobby",
            "observed_at": "2026-11-23T11:00:00Z",
        }
    ]
    pdf_bytes = generate_field_report_pdf(PROJECT, records)
    assert pdf_bytes.startswith(b"%PDF-")
    reader = PdfReader(BytesIO(pdf_bytes))
    content = "\n".join(page.extract_text() for page in reader.pages)
    assert "Actual ramp obstruction" in content
    assert "North entrance approach blocked by materials" in content
    assert "NOT A CONFIRMED ENGINEERING DEFECT" in content
    assert "Verified persisted inspection records included: 1" in content
    assert "Example fixture" not in content


def test_field_report_paginate_long_notes_without_truncating_real_data():
    notes = "LONG-NOTE " * 550
    result = generate_field_report_pdf(PROJECT, [{
        "title": "Observed wall condition", "description": notes, "status": "open",
    }])
    report = PdfReader(BytesIO(result))
    assert len(report.pages) >= 2
    extracted = " ".join(page.extract_text() for page in report.pages)
    assert "Observed wall condition" in extracted
    assert extracted.count("LONG-NOTE") == 550


@pytest.mark.asyncio
async def test_photo_upload_persists_scanned_redacted_bytes_and_metadata():
    sanitized = b"\xff\xd8saved-jpeg-binary\xff\xd9"
    client = MagicMock()
    query = MagicMock()
    query.insert.return_value = query
    query.execute.return_value = SimpleNamespace(
        data=[{"id": PHOTO, **fake_photo_row(path=PATH)}]
    )
    db = MagicMock()
    db.table.return_value = query
    with (
        patch.object(field_routes, "_owned_field_inspection",
                     AsyncMock(return_value=fake_inspection())),
        patch.object(field_routes, "run_in_threadpool", inline),
        patch.object(field_routes, "sanitized_photo_bytes",
                     return_value=(sanitized, {
                         "malware_scan_completed": True,
                         "exif_gps_removed": True,
                     })) as scrub,
        patch.object(field_routes.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
        patch.object(field_routes, "db", db),
    ):
        result = await field_routes.upload_field_photo(
            UUID(INSPECTION),
            photo=UploadFile(filename="site.jpg", file=BytesIO(picture(False))),
            user=USER,
        )
    assert result["id"] == PHOTO
    assert scrub.called
    upload_args = client.storage.from_.return_value.upload.call_args.kwargs
    assert upload_args["file"] == sanitized
    assert upload_args["file_options"]["content-type"] == "image/jpeg"
    metadata = query.insert.call_args.args[0]
    assert metadata["inspection_id"] == INSPECTION
    assert metadata["project_id"] == PROJECT
    assert metadata["source_metadata"]["exif_gps_removed"] is True
    assert metadata["path"].startswith(
        f"{USER['user_id']}/{PROJECT}/field/{INSPECTION}/"
    )


@pytest.mark.asyncio
async def test_photo_upload_rolls_back_storage_if_database_insert_fails():
    client = MagicMock()
    query = MagicMock()
    query.insert.return_value = query
    query.execute.side_effect = RuntimeError("DB unavailable")
    db = MagicMock()
    db.table.return_value = query
    with (
        patch.object(field_routes, "_owned_field_inspection",
                     AsyncMock(return_value=fake_inspection())),
        patch.object(field_routes, "run_in_threadpool", inline),
        patch.object(field_routes, "sanitized_photo_bytes",
                     return_value=(b"\xff\xd8sanitized", {"exif_gps_removed": True})),
        patch.object(field_routes.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
        patch.object(field_routes, "db", db),
    ):
        with pytest.raises(HTTPException) as exc:
            await field_routes.upload_field_photo(
                UUID(INSPECTION),
                photo=UploadFile(filename="site.jpg", file=BytesIO(picture(False))),
                user=USER,
            )
    assert exc.value.status_code == 503
    client.storage.from_.return_value.remove.assert_called_once()


@pytest.mark.asyncio
async def test_untrusted_photo_path_cannot_generate_signed_url():
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.maybe_single.return_value = query
    query.execute.return_value = SimpleNamespace(data=fake_photo_row(
        path=f"{USER['user_id']}/{PROJECT}/field/{INSPECTION}/../other.jpg"
    ))
    db = MagicMock()
    db.table.return_value = query
    client = MagicMock()
    with (
        patch.object(field_routes, "_owned_field_inspection",
                     AsyncMock(return_value=fake_inspection())),
        patch.object(field_routes, "run_in_threadpool", inline),
        patch.object(field_routes.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
        patch.object(field_routes, "db", db),
    ):
        with pytest.raises(HTTPException) as error:
            await field_routes.get_field_photo_signed_url(UUID(PHOTO), user=USER)
    assert error.value.status_code == 409
    client.storage.from_.assert_not_called()


@pytest.mark.asyncio
async def test_private_photo_signing_uses_authenticated_project_only():
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.maybe_single.return_value = query
    query.execute.return_value = SimpleNamespace(data=fake_photo_row())
    db = MagicMock()
    db.table.return_value = query
    client = MagicMock()
    client.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": "https://private-storage.example/short-lived-photo"
    }
    with (
        patch.object(field_routes, "_owned_field_inspection",
                     AsyncMock(return_value=fake_inspection())),
        patch.object(field_routes, "run_in_threadpool", inline),
        patch.object(field_routes.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
        patch.object(field_routes, "db", db),
    ):
        result = await field_routes.get_field_photo_signed_url(UUID(PHOTO), user=USER)
    assert result["expires_in"] == 900
    client.storage.from_.return_value.create_signed_url.assert_called_once_with(
        PATH, 900
    )


@pytest.mark.asyncio
async def test_report_route_reads_real_owner_rows_and_returns_pdf():
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.order.return_value = query
    query.limit.return_value = query
    query.execute.return_value = SimpleNamespace(data=[
        {"title": "Actual field observation", "description": "Concrete damaged",
         "severity": "medium", "discipline": "site", "status": "open"},
    ])
    db = MagicMock()
    db.table.return_value = query
    with (
        patch.object(field_routes, "_owned_project", AsyncMock(return_value={"id": PROJECT})),
        patch.object(field_routes, "run_in_threadpool", inline),
        patch.object(field_routes, "db", db),
    ):
        response = await field_routes.get_field_project_report_pdf(
            UUID(PROJECT), user=USER
        )
    assert response.media_type == "application/pdf"
    assert response.body.startswith(b"%PDF-")
    assert "private, no-store" == response.headers["cache-control"]
    assert any(call.args == ("created_by", USER["user_id"]) for call in query.eq.call_args_list)
    assert b"Actual" in response.body or PdfReader(BytesIO(response.body))


@pytest.mark.asyncio
async def test_field_photo_rejects_unowned_observation_before_reading_upload():
    read = AsyncMock(side_effect=HTTPException(status_code=404, detail="Not found"))
    with patch.object(field_routes, "_owned_field_inspection", read):
        with pytest.raises(HTTPException) as exc:
            await field_routes.upload_field_photo(
                UUID(INSPECTION),
                photo=UploadFile(filename="site.jpg", file=BytesIO(picture(False))),
                user=USER,
            )
    assert exc.value.status_code == 404
