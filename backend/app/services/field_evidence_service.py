"""Scanned, EXIF-stripped field photographs and factual inspection PDF reports.

No GPS/device data is stored or trusted. Camera EXIF is stripped before upload,
and a photograph is documented as a *user observation*, not a proven defect.
"""
from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import tempfile

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.services.import_service import _scan_file

MAX_PHOTO_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 25_000_000


def sanitized_photo_bytes(raw: bytes, extension: str) -> tuple[bytes, dict]:
    ext = extension.strip(".").lower()
    if ext not in {"jpg", "jpeg", "png", "webp"}:
        raise HTTPException(status_code=415, detail="Only JPG, PNG or WebP photos are supported")
    if not isinstance(raw, bytes) or not raw:
        raise HTTPException(status_code=422, detail="Photograph is empty")
    if len(raw) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="Photograph exceeds 10 MB")

    # Strictly BEFORE parsing image payloads, require a functioning scanner.
    with tempfile.TemporaryDirectory(prefix="krafzen-field-photo-") as directory:
        path = Path(directory) / ("submitted." + ext)
        path.write_bytes(raw)
        _scan_file(path)

    try:
        with Image.open(BytesIO(raw)) as source:
            expected = "JPEG" if ext in ("jpg", "jpeg") else ext.upper()
            if source.format != expected:
                raise HTTPException(status_code=422, detail="Photo bytes do not match filename type")
            width, height = source.size
            if not width or not height or width * height > MAX_PIXELS:
                raise HTTPException(status_code=413, detail="Photo pixel dimensions exceed limit")
            # Transpose orientation and re-encode from decoded pixels without any
            # EXIF, XMP or GPS info; retain no untrusted metadata.
            decoded = ImageOps.exif_transpose(source)
            decoded.load()
            sanitized = decoded.convert("RGB")
            width, height = sanitized.size
            buf = BytesIO()
            sanitized.save(buf, format="JPEG", quality=88, optimize=True)
            result = buf.getvalue()
    except HTTPException:
        raise
    except (UnidentifiedImageError, ValueError, OSError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail="Photograph cannot be decoded safely") from exc

    if not result.startswith(bytes([0xFF, 0xD8])) or len(result) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=422, detail="Sanitized photo failed content validation")
    return result, {
        "original_sha256": sha256(raw).hexdigest(),
        "stored_sha256": sha256(result).hexdigest(),
        "original_bytes": len(raw),
        "stored_bytes": len(result),
        "image_width_px": width,
        "image_height_px": height,
        "malware_scan_completed": True,
        "exif_gps_removed": True,
        "source_kind": "user_supplied_field_photo",
        "engineering_defect_confirmed": False,
    }


def generate_field_report_pdf(project_id: str, rows: list[dict]) -> bytes:
    """Render only the actual persisted inspection records, never fake results."""
    if not isinstance(rows, list) or len(rows) > 200:
        raise ValueError("Field report requires at most 200 persisted inspections")
    out = BytesIO()
    document = canvas.Canvas(out, pagesize=letter)
    page_width, page_height = letter
    y = page_height - 45

    def line(text: object, size: int = 10, bold: bool = False) -> None:
        nonlocal y
        from reportlab.pdfbase.pdfmetrics import stringWidth

        font = "Helvetica-Bold" if bold else "Helvetica"
        document.setFont(font, size)
        # Normalize user text; enforce physical line width and check EVERY
        # resulting line for a page break, even for 4,000-character notes.
        clean = " ".join(str(text or "").split()).encode(
            "latin-1", errors="replace"
        ).decode("latin-1")
        available = page_width - 70
        if not clean:
            clean = " "
        while clean:
            low, high = 1, len(clean)
            while low < high:
                middle = (low + high + 1) // 2
                if stringWidth(clean[:middle], font, size) <= available:
                    low = middle
                else:
                    high = middle - 1
            end = max(low, 1)
            # Preserve word breaks where possible; split very long words
            # safely instead of rendering text beyond the page edge.
            if end < len(clean):
                whitespace = clean.rfind(" ", 0, end + 1)
                if whitespace > max(1, end // 2):
                    end = whitespace
            if y < 85:
                document.showPage()
                y = page_height - 45
                document.setFont(font, size)
            document.drawString(35, y, clean[:end].strip())
            y -= size + 5
            clean = clean[end:].lstrip()

    document.setTitle("KRAFZEN Field Observations — Pending Professional Review")
    line("FIELD INSPECTION OBSERVATIONS", 15, True)
    line(f"Project: {project_id}")
    line(f"Generated UTC: {datetime.now(UTC).isoformat()}")
    line(f"Verified persisted inspection records included: {len(rows)}")
    y -= 16
    for record in rows:
        line("Observation: " + str(record.get("title") or ""), 11, True)
        line("Recorded status: " + str(record.get("status") or "unknown"))
        line("Discipline/severity: " + str(record.get("discipline") or "") +
             " / " + str(record.get("severity") or ""))
        line("Observed: " + str(record.get("observed_at") or record.get("created_at") or "unknown"))
        line("Location (user-declared): " + str(record.get("location_label") or "not supplied"))
        line("Description: " + str(record.get("description") or ""))
        if record.get("resolved_at"):
            line("Resolved: " + str(record["resolved_at"]))
        for note in record.get("report_notes", []):
            line("Note: " + str(note.get("kind") or "comment").replace("_", " ") +
                 " | " + str(note.get("created_at") or "unknown"), 10, True)
            if note.get("due_date"):
                line("Corrective action due: " + str(note["due_date"]))
            line(note.get("body") or "")
        for photo in record.get("report_photos", []):
            line("Stored photo evidence reference: " + str(photo.get("id") or ""))
            line("Recorded: " + str(photo.get("created_at") or "unknown"))
            metadata = photo.get("source_metadata") or {}
            if metadata.get("stored_sha256"):
                line("Stored SHA-256: " + str(metadata["stored_sha256"]))
        y -= 10

    line("NOT A CONFIRMED ENGINEERING DEFECT OR CODE APPROVAL.", 10, True)
    line("Original observations require independent site evidence and qualified reviewer.")
    document.save()
    rendered = out.getvalue()
    if not rendered.startswith(b"%PDF-") or len(rendered) > 5 * 1024 * 1024:
        raise RuntimeError("Field report generation failed")
    return rendered
