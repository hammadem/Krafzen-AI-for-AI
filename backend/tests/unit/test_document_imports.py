"""Real project-document file fixtures, unsafe ZIP rejection and scan sequencing."""
import io
import json
import stat
import zipfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, UploadFile
from PIL import Image
from pypdf import PdfWriter
import pytest

from app.services import document_inspection, import_service

PROJECT = "00000000-0000-0000-0000-000000000002"
JOB = "00000000-0000-0000-0000-000000000003"
USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


def zipped(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return out.getvalue()


def docx_fixture():
    return zipped({
        "[Content_Types].xml": '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        "word/document.xml": '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Fire egress annotation</w:t></w:r></w:p></w:body></w:document>',
    })


def xlsx_fixture():
    return zipped({
        "[Content_Types].xml": "<Types/>",
        "xl/workbook.xml": '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Schedule" sheetId="1"/></sheets></workbook>',
        "xl/worksheets/sheet1.xml": '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1"/></row></sheetData></worksheet>',
    })


def pdf_fixture():
    writer = PdfWriter()
    writer.add_blank_page(width=600, height=450)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def png_fixture():
    out = io.BytesIO()
    Image.new("RGB", (64, 48), (44, 110, 130)).save(out, format="PNG")
    return out.getvalue()


@pytest.mark.parametrize("kind,data,expected", [
    ("pdf", pdf_fixture(), ("page_count", 1)),
    ("docx", docx_fixture(), ("paragraph_text_fragments", 1)),
    ("xlsx", xlsx_fixture(), ("sheet_count", 1)),
    ("csv", b"item,count\nBeams,14\nWalls,8\n", ("row_count", 3)),
    ("png", png_fixture(), ("image_width_px", 64)),
    ("zip", zipped({"readme.txt": b"real contents"}), ("archive_entry_count", 1)),
])
def test_genuine_document_metadata_parsers(kind, data, expected):
    report = document_inspection.inspect_document_bytes(data, kind)
    assert report["type"] == "document"
    assert report["format"] == kind
    assert report["source_size_bytes"] == len(data)
    assert report[expected[0]] == expected[1]
    assert report["engineering_validation_performed"] is False


def test_docx_extracted_text_is_actual_fixture_content():
    report = document_inspection.inspect_document_bytes(docx_fixture(), "docx")
    assert "Fire egress annotation" in report["text_excerpt"]


@pytest.mark.parametrize("payload", [
    zipped({"../../outside.txt": b"x"}),
    zipped({"..\\outside.txt": b"x"}),
    zipped({"/etc/password": b"x"}),
])
def test_archive_traversal_rejected(payload):
    with pytest.raises(ValueError, match="unsafe"):
        document_inspection.inspect_document_bytes(payload, "zip")


def test_zip_bomb_ratio_fails_closed():
    payload = zipped({"large.txt": b"A" * (2 * 1024 * 1024)})
    with pytest.raises(ValueError, match="compression ratio"):
        document_inspection.inspect_document_bytes(payload, "zip")


def test_macro_enabled_office_package_rejected():
    unsafe = zipped({
        "[Content_Types].xml": "<Types/>",
        "word/document.xml": "<document/>",
        "word/vbaProject.bin": b"bad",
    })
    with pytest.raises(ValueError, match="Macro"):
        document_inspection.inspect_document_bytes(unsafe, "docx")


def test_encrypted_archive_rejected():
    archive = io.BytesIO()
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr(info, "etc/passwd")
    with pytest.raises(ValueError, match="unsafe"):
        document_inspection.inspect_document_bytes(archive.getvalue(), "zip")


@pytest.mark.parametrize("raw", [b"", b"not pdf", b"%PDF-malformed"])
def test_invalid_pdf_rejected(raw):
    with pytest.raises(ValueError):
        document_inspection.inspect_document_bytes(raw, "pdf")


def test_csv_data_is_counted_but_not_executed():
    report = document_inspection.inspect_document_bytes(
        b"name,formula\nexample,=CMD(123)\n", "csv"
    )
    assert report["row_count"] == 2
    assert report["headers"] == ["name", "formula"]
    assert report["formulas_executed"] is False


@pytest.mark.asyncio
async def test_document_upload_scans_before_parsing_and_saves_project_metadata():
    raw = b"field,amount\nslabs,4\n"
    user = USER
    client = MagicMock()
    actions = []

    def scanner(data, ext):
        actions.append("scan_and_parse")
        return {
            "type": "document", "format": ext, "row_count": 2,
            "source_size_bytes": len(data),
            "malware_scan_completed": True,
        }

    async def inline(fn, *args):
        return fn(*args)

    async def store_row(file_data, actor):
        actions.append("database")
        assert file_data["project_id"] == PROJECT
        assert file_data["job_id"] == JOB
        assert file_data["import_metadata"]["malware_scan_completed"] is True
        assert file_data["file_type"] == "csv"
        assert file_data["path"].startswith(f"{USER['user_id']}/{PROJECT}/imports/{JOB}/")
        assert actor == USER
        return {"id": "saved-1", **file_data}

    with (
        patch.object(import_service, "get_job",
                     AsyncMock(return_value={"id": JOB, "project_id": PROJECT})),
        patch.object(import_service, "get_project",
                     AsyncMock(return_value={"id": PROJECT, "workspace_id": None})),
        patch.object(import_service, "run_in_threadpool", inline),
        patch.object(import_service, "_scan_and_inspect_document", side_effect=scanner),
        patch.object(import_service.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
        patch.object(import_service, "create_file", side_effect=store_row),
    ):
        response = await import_service.import_document_for_job(
            job_id=JOB, upload=UploadFile(filename="field.csv", file=io.BytesIO(raw)),
            user=user,
        )
    assert response["id"] == "saved-1"
    assert actions == ["scan_and_parse", "database"]
    client.storage.from_.return_value.upload.assert_called_once()


@pytest.mark.asyncio
async def test_document_import_rejects_sovereign_project_before_storage():
    client = MagicMock()
    with (
        patch.object(import_service, "get_job",
                     AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project",
                     AsyncMock(return_value={"workspace_id": "org-1"})),
        patch.object(import_service.storage_service, "resolve_target_bucket_and_client") as resolve,
    ):
        with pytest.raises(HTTPException) as result:
            await import_service.import_document_for_job(
                job_id=JOB,
                upload=UploadFile(filename="report.pdf", file=io.BytesIO(pdf_fixture())),
                user=USER,
            )
    assert result.value.status_code == 503
    resolve.assert_not_called()


@pytest.mark.asyncio
async def test_document_import_rolls_back_uploaded_blob_if_row_insert_fails():
    raw = b"col\nrow\n"
    client = MagicMock()

    async def inline(fn, *args):
        return fn(*args)

    with (
        patch.object(import_service, "get_job",
                     AsyncMock(return_value={"project_id": PROJECT})),
        patch.object(import_service, "get_project",
                     AsyncMock(return_value={"workspace_id": None})),
        patch.object(import_service, "run_in_threadpool", inline),
        patch.object(import_service, "_scan_and_inspect_document",
                     return_value={"type": "document", "format": "csv", "row_count": 2}),
        patch.object(import_service.storage_service, "resolve_target_bucket_and_client",
                     return_value=(client, "dxf-files", "global")),
        patch.object(import_service, "create_file", AsyncMock(return_value={"error": "DB down"})),
    ):
        with pytest.raises(HTTPException) as exc:
            await import_service.import_document_for_job(
                job_id=JOB,
                upload=UploadFile(filename="report.csv", file=io.BytesIO(raw)),
                user=USER,
            )
    assert exc.value.status_code == 503
    client.storage.from_.return_value.remove.assert_called_once()
