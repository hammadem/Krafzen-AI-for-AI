"""Actual, bounded document metadata extraction for authenticated uploads.

Runs in a separate, time-limited process after ClamAV scanning. No submitted
document is ever executed, evaluated as a spreadsheet or extracted to disk.
The results are source-derived metadata, not AI engineering conclusions.
"""
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ALLOWED_DOCUMENTS = {
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
MAX_UNCOMPRESSED_ZIP = 80 * 1024 * 1024
MAX_XML_BYTES = 8 * 1024 * 1024
MAX_ARCHIVE_FILES = 400


def _archive_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_FILES:
        raise ValueError("Document archive exceeds 400 entries")
    unpacked = 0
    for entry in infos:
        path = entry.filename
        parts = path.replace(chr(92), "/").split("/")
        if (not path or path.startswith("/") or path.startswith(chr(92))
            or any(x in ("", ".", "..") for x in parts if x != parts[-1])
            or ".." in parts
            or (len(parts[0]) >= 2 and parts[0][1] == ":")
            or entry.flag_bits & 1
            or (entry.external_attr >> 16) & 0o170000 == 0o120000):
            raise ValueError("Archive contains unsafe paths, symlinks or encryption")
        if entry.file_size > MAX_UNCOMPRESSED_ZIP:
            raise ValueError("Archive member exceeds expanded size budget")
        unpacked += entry.file_size
        if unpacked > MAX_UNCOMPRESSED_ZIP:
            raise ValueError("Archive expanded size budget exceeded")
        if entry.file_size > 1024 * 1024 and (
            entry.compress_size == 0 or
            entry.file_size > entry.compress_size * 150
        ):
            raise ValueError("Archive contains a suspicious compression ratio")
    return infos


def _safe_xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    record = archive.getinfo(name)
    if record.file_size > MAX_XML_BYTES:
        raise ValueError("Office document XML exceeds extraction limit")
    return ET.fromstring(archive.read(name))


def _office_summary(raw: bytes, kind: str) -> dict:
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = _archive_members(archive)
            names = {entry.filename for entry in entries}
            if kind in ("docx", "xlsx") and "[Content_Types].xml" not in names:
                raise ValueError("Office package is missing content types")
            if any(name.lower().endswith("vbaproject.bin") for name in names):
                raise ValueError("Macro-enabled documents are not supported")
            if kind == "docx":
                if "word/document.xml" not in names:
                    raise ValueError("DOCX has no actual document body")
                root = _safe_xml(archive, "word/document.xml")
                paragraphs = [
                    node.text or "" for node in root.iter()
                    if node.tag.endswith("}t") and node.text
                ]
                excerpt = " ".join(paragraphs)[:20000]
                return {
                    "text_excerpt": excerpt,
                    "text_truncated": sum(len(s) for s in paragraphs) > 20000,
                    "paragraph_text_fragments": len(paragraphs),
                }
            if kind == "xlsx":
                if "xl/workbook.xml" not in names:
                    raise ValueError("XLSX has no workbook content")
                root = _safe_xml(archive, "xl/workbook.xml")
                sheet_names = [
                    (node.attrib.get("name") or "")[:100]
                    for node in root.iter() if node.tag.endswith("}sheet")
                ]
                sheet_files = [
                    name for name in names
                    if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
                ]
                return {
                    "sheet_count": len(sheet_names),
                    "sheet_names": sheet_names[:100],
                    "worksheet_xml_files": len(sheet_files),
                    "calculation_executed": False,
                }
            return {
                "archive_entry_count": len(entries),
                "archive_entries": [
                    {"path": entry.filename[:200], "size_bytes": entry.file_size}
                    for entry in entries[:100]
                    if not entry.is_dir()
                ],
                "contents_extracted_to_disk": False,
            }
    except (zipfile.BadZipFile, KeyError, ET.ParseError, RuntimeError) as exc:
        raise ValueError("Document ZIP structure is unreadable") from exc


def inspect_document_bytes(raw: bytes, kind: str) -> dict:
    kind = str(kind or "").lower()
    if kind not in ALLOWED_DOCUMENTS:
        raise ValueError("Unsupported document format")
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_DOCUMENT_BYTES:
        raise ValueError("Document must be nonempty and at most 25 MB")
    result = {
        "type": "document", "format": kind,
        "mime_type": ALLOWED_DOCUMENTS[kind],
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_size_bytes": len(raw),
        "engineering_validation_performed": False,
    }
    if kind in ("docx", "xlsx", "zip"):
        result.update(_office_summary(raw, kind))
    elif kind == "pdf":
        if not raw.lstrip().startswith(b"%PDF-"):
            raise ValueError("Invalid PDF header")
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw), strict=True)
            if reader.is_encrypted:
                raise ValueError("Encrypted PDFs cannot be ingested")
            pages = len(reader.pages)
            if not 1 <= pages <= 300:
                raise ValueError("PDF must have between 1 and 300 pages")
            snippets = []
            for page in reader.pages[:min(pages, 8)]:
                snippets.append((page.extract_text() or "")[:3000])
            excerpt = "\n".join(snippets)[:20000]
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("PDF content could not be parsed safely") from exc
        result.update({
            "page_count": pages,
            "text_excerpt": excerpt,
            "text_extraction_pages": min(pages, 8),
            "text_truncated": pages > 8,
        })
    elif kind == "csv":
        if len(raw) > 10 * 1024 * 1024 or bytes([0]) in raw:
            raise ValueError("CSV is oversized or contains binary bytes")
        try:
            reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
            rows = 0
            max_cols = 0
            headers = []
            for row in reader:
                rows += 1
                if rows > 100000 or len(row) > 500:
                    raise ValueError("CSV row/column limits exceeded")
                max_cols = max(max_cols, len(row))
                if rows == 1:
                    headers = [cell[:160] for cell in row[:100]]
        except (UnicodeError, csv.Error) as exc:
            raise ValueError("CSV must contain valid UTF-8 tabular text") from exc
        if not rows:
            raise ValueError("CSV is empty")
        result.update({
            "row_count": rows, "maximum_column_count": max_cols,
            "headers": headers, "formulas_executed": False,
        })
    else:
        from PIL import Image, UnidentifiedImageError
        try:
            with Image.open(io.BytesIO(raw)) as image:
                actual = image.format
                width, height = image.size
                expected = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "webp": "WEBP"}[kind]
                if actual != expected or not width or not height or width * height > 25_000_000:
                    raise ValueError("Image format or dimensions are invalid")
                image.verify()
        except (UnidentifiedImageError, OSError, OverflowError) as exc:
            raise ValueError("Image is corrupt or unsupported") from exc
        result.update({
            "image_width_px": width, "image_height_px": height,
            "optical_character_recognition_performed": False,
        })
    return result


def inspect_document_file(path: str, kind: str) -> dict:
    return inspect_document_bytes(Path(path).read_bytes(), kind)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m app.services.document_inspection <path> <format>")
    try:
        print(json.dumps(inspect_document_file(sys.argv[1], sys.argv[2]), ensure_ascii=True))
    except Exception:
        raise SystemExit(2) from None
