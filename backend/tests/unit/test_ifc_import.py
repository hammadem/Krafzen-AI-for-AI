"""Real IFC parsing tests and fail-closed import lifecycle tests."""

import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import ifcopenshell
import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app.services import ifc_inspection, import_service

USER = {"user_id": "00000000-0000-0000-0000-000000000001"}
PROJECT = "00000000-0000-0000-0000-000000000002"
JOB = "00000000-0000-0000-0000-000000000003"


def make_ifc(tmp_path: Path, include_project=True, include_building=True) -> bytes:
    model = ifcopenshell.file(schema="IFC4")
    if include_project:
        model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), Name="Warehouse")
    if include_building:
        model.create_entity("IfcBuilding", GlobalId=ifcopenshell.guid.new(), Name="Main Building")
    path = tmp_path / "warehouse.ifc"
    model.write(str(path))
    return path.read_bytes()


def upload(data: bytes, name="warehouse.ifc"):
    return UploadFile(filename=name, file=io.BytesIO(data))


def test_real_ifcopenshell_reads_actual_model_entities(tmp_path):
    data = make_ifc(tmp_path)
    model_path = tmp_path / "warehouse.ifc"
    assert b"ISO-10303-21;" in data
    details = ifc_inspection.inspect_ifc_file(str(model_path))
    assert details["schema"] == "IFC4"
    assert details["project_name"] == "Warehouse"
    assert details["product_count"] == 1
    assert details["entity_counts"]["IfcBuilding"] == 1
    assert details["represented_product_count"] == 0
    assert details["geometry_validated"] is False


def test_ifc_inspector_rejects_models_without_project(tmp_path):
    make_ifc(tmp_path, include_project=False)
    with pytest.raises(ValueError, match="one IfcProject"):
        ifc_inspection.inspect_ifc_file(str(tmp_path / "warehouse.ifc"))


def test_ifc_scanner_failure_prevents_parser_execution(tmp_path):
    data = make_ifc(tmp_path)
    with (
        patch.object(import_service.shutil, "which", return_value=None),
        patch.object(import_service.subprocess, "run") as parser,
    ):
        with pytest.raises(HTTPException) as error:
            import_service._scan_ifc_and_extract_metadata(data)
    assert error.value.status_code == 503
    parser.assert_not_called()


def test_corrupt_ifc_envelope_is_rejected(tmp_path):
    with patch.object(import_service.shutil, "which") as scan:
        with pytest.raises(HTTPException) as error:
            import_service._scan_ifc_and_extract_metadata(b"not a model")
    assert error.value.status_code == 422
    scan.assert_not_called()


def test_real_ifc_subprocess_returns_actual_metadata_after_scan(tmp_path):
    data = make_ifc(tmp_path)
    with patch.object(import_service, "_scan_file") as scan:
        summary = import_service._scan_ifc_and_extract_metadata(data)
    scan.assert_called_once()
    assert summary["type"] == "ifc"
    assert summary["entity_counts"]["IfcBuilding"] == 1
    assert summary["geometry_validated"] is False


@pytest.mark.asyncio
async def test_ifc_upload_rejects_foreign_job_before_reading_file():
    with patch.object(import_service, "get_job", AsyncMock(return_value=None)):
        with pytest.raises(HTTPException) as error:
            await import_service.import_ifc_for_job(job_id=JOB, upload=upload(b"anything"), user=USER)
    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_ifc_upload_rejects_sovereign_organization_before_storage():
    with (
        patch.object(import_service, "get_job", AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project", AsyncMock(return_value={"workspace_id": "org-id"})),
        patch.object(import_service.storage_service, "resolve_target_bucket_and_client") as storage,
    ):
        with pytest.raises(HTTPException) as error:
            await import_service.import_ifc_for_job(job_id=JOB, upload=upload(b"anything"), user=USER)
    assert error.value.status_code == 503
    storage.assert_not_called()


@pytest.mark.asyncio
async def test_ifc_import_uploads_real_bytes_and_persists_parsed_metadata(tmp_path):
    data = make_ifc(tmp_path)
    summary = {"type": "ifc", "schema": "IFC4", "product_count": 1, "geometry_validated": False}
    client = MagicMock()
    saved = {"id": "ifc-file-id", "job_id": JOB, "project_id": PROJECT, "import_metadata": summary}
    with (
        patch.object(import_service, "get_job", AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project", AsyncMock(return_value={"workspace_id": None})),
        patch.object(import_service, "_scan_ifc_and_extract_metadata", return_value=summary),
        patch.object(import_service.storage_service, "resolve_target_bucket_and_client", return_value=(client, "dxf-files", "global")),
        patch.object(import_service, "create_file", AsyncMock(return_value=saved)) as create,
    ):
        result = await import_service.import_ifc_for_job(job_id=JOB, upload=upload(data), user=USER)
    assert result["import_metadata"]["schema"] == "IFC4"
    fields = create.await_args.args[0]
    assert fields["file_type"] == "ifc"
    assert fields["import_metadata"] == summary
    assert fields["path"].startswith(f"{USER['user_id']}/{PROJECT}/imports/{JOB}/")
    assert fields["path"].endswith(".ifc")
    client.storage.from_.return_value.upload.assert_called_once()
    assert client.storage.from_.return_value.upload.call_args.kwargs["file"] == data


@pytest.mark.asyncio
async def test_ifc_metadata_failure_removes_uploaded_blob(tmp_path):
    data = make_ifc(tmp_path)
    client = MagicMock()
    with (
        patch.object(import_service, "get_job", AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project", AsyncMock(return_value={"workspace_id": None})),
        patch.object(import_service, "_scan_ifc_and_extract_metadata", return_value={"type": "ifc"}),
        patch.object(import_service.storage_service, "resolve_target_bucket_and_client", return_value=(client, "dxf-files", "global")),
        patch.object(import_service, "create_file", AsyncMock(return_value={"error": "db unavailable"})),
    ):
        with pytest.raises(HTTPException) as error:
            await import_service.import_ifc_for_job(job_id=JOB, upload=upload(data), user=USER)
    assert error.value.status_code == 503
    client.storage.from_.return_value.remove.assert_called_once()


@pytest.mark.asyncio
async def test_ifc_route_rejects_invalid_file_extension_before_storage(client):
    with (
        patch.object(import_service, "get_job", AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project", AsyncMock(return_value={"workspace_id": None})),
    ):
        response = client.post(
            "/api/v1/files/import-ifc",
            data={"job_id": JOB},
            files={"upload": ("drawing.rvt", b"invalid", "application/octet-stream")},
        )
    assert response.status_code == 415



def test_real_ifc_spatial_storey_and_length_units(tmp_path):
    model = ifcopenshell.file(schema="IFC4")
    project = model.create_entity(
        "IfcProject", GlobalId=ifcopenshell.guid.new(), Name="Library"
    )
    storey = model.create_entity(
        "IfcBuildingStorey", GlobalId=ifcopenshell.guid.new(),
        Name="Level 01", Elevation=3.2,
    )
    metre = model.create_entity(
        "IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"
    )
    project.UnitsInContext = model.create_entity("IfcUnitAssignment", Units=[metre])
    path = tmp_path / "library.ifc"
    model.write(str(path))
    summary = ifc_inspection.inspect_ifc_file(str(path))
    assert summary["storey_count"] == 1
    assert summary["storeys"][0]["name"] == "Level 01"
    assert summary["storeys"][0]["elevation"] == 3.2
    assert summary["length_unit"]["name"] == "METRE"
    assert summary["geometry_validated"] is False


def test_ifc_summary_endpoint_requires_owned_file(client):
    from app.routes import file_routes
    with patch.object(file_routes, "get_file", AsyncMock(return_value=None)):
        response = client.get(f"/api/v1/files/{JOB}/bim-summary")
    assert response.status_code == 404


def test_ifc_summary_endpoint_returns_only_verified_ifc_model(client):
    from app.routes import file_routes
    metadata = {
        "type": "ifc", "schema": "IFC4",
        "storey_count": 1, "geometry_validated": False,
    }
    record = {
        "id": JOB, "project_id": PROJECT, "file_type": "ifc",
        "bucket": "private-bucket", "path": "private/path",
        "import_metadata": metadata,
    }
    with patch.object(file_routes, "get_file", AsyncMock(return_value=record)):
        response = client.get(f"/api/v1/files/{JOB}/bim-summary")
    assert response.status_code == 200
    assert response.json() == {
        "file_id": JOB, "project_id": PROJECT, "model": metadata,
    }
    assert "private/path" not in response.text


def test_ifc_summary_endpoint_rejects_unparsed_legacy_file(client):
    from app.routes import file_routes
    with patch.object(file_routes, "get_file", AsyncMock(return_value={
        "id": JOB, "project_id": PROJECT, "file_type": "ifc",
        "import_metadata": None,
    })):
        response = client.get(f"/api/v1/files/{JOB}/bim-summary")
    assert response.status_code == 409
