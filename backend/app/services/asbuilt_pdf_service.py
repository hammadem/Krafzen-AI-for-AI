"""Auditable PDF from a saved, exact-coordinate as-built DXF comparison.

This is a comparison of two persisted drawing files, not evidence that a
building was physically constructed as depicted. The source DXFs, not AI or
sample datasets, supplied the counts and geometrical difference samples.
"""
from datetime import UTC, datetime
from io import BytesIO
from string import hexdigits

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_SAMPLES = 100
MAX_SUPPORTED_ENTITIES = 50_000


def _valid_hash(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in hexdigits for character in value
    )


def _count(value: object) -> bool:
    return type(value) is int and 0 <= value <= MAX_SUPPORTED_ENTITIES


def _validate_saved_record(record: dict) -> dict:
    if not isinstance(record, dict) or not isinstance(record.get("result"), dict):
        raise ValueError("A persisted as-built comparison is required")
    for field in ("id", "project_id", "original_file_id", "revised_file_id"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError("Saved comparison is missing required project/file references")
    result = record["result"]
    if result.get("method") != "exact_coordinate_entity_diff_v1":
        raise ValueError("Saved comparison uses an unsupported method")
    if not all(_valid_hash(result.get(field)) for field in (
        "source_hash_sha256", "revised_hash_sha256"
    )):
        raise ValueError("Saved comparison is missing verifiable source hashes")
    for field in (
        "original_supported_count", "revised_supported_count",
        "unchanged_count", "added_count", "removed_count",
    ):
        if not _count(result.get(field)):
            raise ValueError("Saved comparison has invalid entity counts")
    if result["original_supported_count"] != (
        result["unchanged_count"] + result["removed_count"]
    ) or result["revised_supported_count"] != (
        result["unchanged_count"] + result["added_count"]
    ):
        raise ValueError("Saved comparison entity counts do not reconcile")
    if type(result.get("insunits")) is not int or result["insunits"] <= 0:
        raise ValueError("Saved comparison has no declared DXF units")
    if type(result.get("comparison_complete")) is not bool:
        raise ValueError("Saved comparison completeness was not recorded")
    if result.get("requires_professional_review") is not True:
        raise ValueError("Saved comparison has no professional-review warning")
    for sample_kind in ("added_samples", "removed_samples"):
        samples = result.get(sample_kind)
        if not isinstance(samples, list) or len(samples) > MAX_SAMPLES:
            raise ValueError("Saved comparison samples are invalid")
        for item in samples:
            if not isinstance(item, dict) or not _count(item.get("count")):
                raise ValueError("Saved comparison sample is invalid")
            for key in ("entity", "layer", "geometry"):
                if not isinstance(item.get(key), str) or len(item[key]) > 500:
                    raise ValueError("Saved comparison sample has invalid geometry")
    for name in ("unsupported_original", "unsupported_revised"):
        if not isinstance(result.get(name), dict):
            raise ValueError("Saved comparison unsupported entity counts are missing")
    return result


def generate_asbuilt_comparison_pdf(record: dict) -> bytes:
    """Render a measured-source provenance report; never invent missing data."""
    result = _validate_saved_record(record)
    out = BytesIO()
    pdf = canvas.Canvas(out, pagesize=letter, pageCompression=1)
    width, height = letter
    y = height - 48

    def page_footer() -> None:
        pdf.setFont("Helvetica-Bold", 8)
        pdf.setFillColorRGB(0.68, 0.10, 0.10)
        pdf.drawString(
            35, 30, "DRAWING DIFFERENCES ONLY - NOT FIELD VERIFIED OR CODE APPROVED"
        )
        pdf.setFillColorRGB(0, 0, 0)

    def new_page() -> None:
        nonlocal y
        page_footer()
        pdf.showPage()
        y = height - 48

    def line(value: object, size: int = 9, bold: bool = False) -> None:
        nonlocal y
        font = "Helvetica-Bold" if bold else "Helvetica"
        text = " ".join(str(value if value is not None else "").split())
        text = text.encode("latin-1", errors="replace").decode("latin-1")
        if not text:
            text = " "
        space = width - 70
        while text:
            left, right = 1, len(text)
            while left < right:
                mid = (left + right + 1) // 2
                if stringWidth(text[:mid], font, size) <= space:
                    left = mid
                else:
                    right = mid - 1
            end = max(1, left)
            if end < len(text):
                word_end = text.rfind(" ", 0, end + 1)
                if word_end > end // 2:
                    end = word_end
            if y < 70:
                new_page()
            pdf.setFont(font, size)
            pdf.drawString(35, y, text[:end].strip())
            y -= size + 5
            text = text[end:].lstrip()

    def section(heading: str) -> None:
        nonlocal y
        y -= 12
        line(heading, 11, True)

    pdf.setTitle("KRAFZEN As-Built Drawing Comparison - Not Field Verified")
    pdf.setAuthor("KRAFZEN AI")
    line("AS-BUILT DXF DRAWING DIFFERENCE REPORT", 14, True)
    line("Stored comparison: " + record["id"])
    line("Project: " + record["project_id"])
    line("Original drawing: " + record["original_file_id"])
    line("Revised drawing: " + record["revised_file_id"])
    line("Saved at: " + str(record.get("created_at") or "not supplied"))
    line("Report generated UTC: " + datetime.now(UTC).isoformat())
    line("Method: " + result["method"])
    line("DXF INSUNITS code: " + str(result["insunits"]))
    line("Original file SHA-256: " + result["source_hash_sha256"])
    line("Revised file SHA-256: " + result["revised_hash_sha256"])

    section("Supported modelspace geometry counts")
    line("Original: " + str(result["original_supported_count"]) +
         "  Revised: " + str(result["revised_supported_count"]))
    line("Unchanged: " + str(result["unchanged_count"]) +
         "  Added: " + str(result["added_count"]) +
         "  Removed: " + str(result["removed_count"]))
    line("Comparison coverage: " + (
        "supported entity types complete" if result["comparison_complete"]
        else "PARTIAL - unsupported entities were present"
    ))
    line("Unsupported original: " + str(result["unsupported_original"])[:300])
    line("Unsupported revised: " + str(result["unsupported_revised"])[:300])

    for field, heading in (
        ("added_samples", "Added entity samples (maximum 100)"),
        ("removed_samples", "Removed entity samples (maximum 100)"),
    ):
        section(heading)
        samples = result[field]
        if not samples:
            line("No samples in saved comparison.")
        for sample in samples:
            line(
                str(sample["count"]) + " x " + sample["entity"] +
                " | layer " + sample["layer"] + " | " + sample["geometry"], 8
            )
        if result["added_count" if field == "added_samples" else "removed_count"] > sum(
            item["count"] for item in samples
        ):
            line("Only representative samples are listed; consult saved JSON for counts.")

    section("Interpretation and restrictions")
    line(str(result.get("limitations") or "Source limitations not supplied")[:700])
    line("A change in two drawings is not proof of a physical construction deviation.")
    line("No automatic drawing registration, site-survey validation, structural approval,")
    line("full BIM geometry comparison, dimensional certification or code approval.")
    line("Status: REQUIRES REVIEW BY A QUALIFIED PROFESSIONAL.", 10, True)
    page_footer()
    pdf.save()
    raw = out.getvalue()
    if not raw.startswith(b"%PDF-") or len(raw) > MAX_PDF_BYTES:
        raise RuntimeError("As-built report could not be generated safely")
    return raw
