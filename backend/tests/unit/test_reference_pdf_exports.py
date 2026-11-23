"""Visual-reference PDF exports must contain real project content and clear caveats."""
import base64
from io import BytesIO
from unittest.mock import AsyncMock, patch

from PIL import Image
import pytest

from app.services.reference_pdf_service import create_reference_pdf
from app.services import export_pipeline_service as pipeline

PROJECT = {
    "id": "bbbbbbbb-0000-0000-0000-000000000002",
    "user_id": "cccccccc-0000-0000-0000-000000000003",
    "workspace_id": None,
}
JOB = {
    "id": "aaaaaaaa-0000-0000-0000-000000000001",
    "project_id": PROJECT["id"],
    "requested_by": PROJECT["user_id"],
    "region_code": "global",
    "format": "pdf",
    "metadata": {},
}


def source_image(fmt="PNG"):
    picture = Image.new("RGB", (80, 50), color=(40, 160, 140))
    stream = BytesIO()
    picture.save(stream, format=fmt)
    kind = "jpeg" if fmt == "JPEG" else fmt.lower()
    return "data:image/" + kind + ";base64," + base64.b64encode(stream.getvalue()).decode()


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP"])
def test_generates_real_nonempty_project_reference_pdf(fmt):
    pdf = create_reference_pdf(source_image(fmt))
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 900
    assert b"Not Dimensionally Verified" in pdf


@pytest.mark.parametrize("uri", [
    "",
    "http://169.254.169.254/internal",
    "data:image/png;base64,not-valid!",
    "data:image/png;base64,",
    "data:text/html;base64,PGh0bWw+",
])
def test_invalid_or_untrusted_project_image_fails_closed(uri):
    with pytest.raises(ValueError):
        create_reference_pdf(uri)


def test_declared_image_type_must_match_real_source_bytes():
    mismatched = source_image("JPEG").replace("image/jpeg", "image/png", 1)
    with pytest.raises(ValueError):
        create_reference_pdf(mismatched)


@pytest.mark.asyncio
async def test_pdf_export_persists_provenance_and_real_pdf_artifact():
    uri = source_image()
    project = {**PROJECT, "image_url": uri}
    with (
        patch.object(pipeline, "_load_source_project", AsyncMock(return_value=project)),
        patch.object(pipeline.storage_service, "upload_cad_file",
                     AsyncMock(return_value="https://storage.example/reference.pdf")) as upload,
        patch.object(pipeline.storage_service, "resolve_target_bucket_and_client",
                     return_value=(object(), "dxf-files", "global")),
        patch.object(pipeline, "create_artifact_file",
                     AsyncMock(return_value={"id": "artifact-456"})),
        patch.object(pipeline, "update_export_status",
                     AsyncMock(return_value={"artifact_file_id": "artifact-456"})) as save,
    ):
        result = await pipeline.run_export_generation(JOB.copy())
    stored = upload.await_args.kwargs
    assert stored["file_bytes"].startswith(b"%PDF-")
    assert stored["file_extension"] == "pdf"
    assert result["format"] == "pdf"
    assert result["generation_method"] == "project_raster_reference_pdf"
    assert result["engineering_accuracy_verified"] is False
    assert save.await_args.args[1]["file_path"].endswith(".pdf")
