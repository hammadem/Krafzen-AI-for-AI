"""PDF evidence report generated from a persisted assessment, not new AI output."""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_compliance_pdf(record):
    if not isinstance(record, dict) or not record.get("id") or not record.get("project_id"):
        raise ValueError("Missing persisted assessment identity")
    result = record.get("result")
    if not isinstance(result, dict) or result.get("complete_code_compliance_determined") is not False:
        raise ValueError("Unverified or unsupported compliance assessment")
    rows = result.get("rule_results")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("Invalid saved assessment findings")
    if any(not isinstance(row, dict) or row.get("result") not in {"pass", "fail", "unknown"}
           for row in rows):
        raise ValueError("Invalid saved assessment results")
    counts = {s: sum(row["result"] == s for row in rows) for s in ("pass", "fail", "unknown")}
    if result.get("counts") != counts:
        raise ValueError("Saved assessment count mismatch")

    stream = BytesIO()
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#0F3555")
    story = []

    def add(value, style="BodyText"):
        text = escape(str(value)[:1200]).replace("\n", "<br/>")
        story.append(Paragraph(text, styles[style]))
        story.append(Spacer(1, 5))

    add("KRAFZEN | Code measurement evidence", "Title")
    add("NOT an authority approval or full code-compliance determination.", "Heading2")
    add("Assessment: " + str(record["id"]))
    add("Project: " + str(record["project_id"]))
    add("Source file/version reference: " + str(record.get("source_file_id") or "No source linked"))
    add("Generated: " + str(result.get("generated_at") or record.get("created_at")))
    add("Review status: " + str(record.get("review_status") or "pending_qualified_review"))
    declaration=result.get("review_attestation")
    if isinstance(declaration,dict):
        add("Recorded reviewer-supplied declaration (credential not independently verified)", "Heading2")
        for field in ("disposition","reviewer_name","reviewer_credential","review_reference","notes","recorded_by","recorded_at"):
            add(field.replace("_"," ")+": "+str(declaration.get(field) or ""))
        add("This declaration does not establish authority approval or full code compliance.")
    add("Jurisdiction, applicable editions and declared reviewer", "Heading2")
    context = record.get("jurisdiction") or {}
    if not isinstance(context, dict):
        raise ValueError("Invalid jurisdiction")
    for key, value in sorted(context.items()):
        add(str(key).replace("_", " ") + ": " + str(value))
    add("Measured inputs (user declared; not independently verified)", "Heading2")
    measurements = record.get("measurements") or {}
    if not isinstance(measurements, dict):
        raise ValueError("Invalid measurements")
    for key, value in sorted(measurements.items()):
        add(str(key).replace("_", " ") + ": " + str(value))
    add(f"Isolated numerical checks: {counts['pass']} pass / {counts['fail']} fail / {counts['unknown']} unknown", "Heading2")
    for row in rows:
        add(f"{row.get('rule_id', 'Rule')} — {row['result'].upper()}", "Heading3")
        add(f"Code: {row.get('code_family')} {row.get('edition')}; Section: {row.get('section_reference')}")
        add(f"Measured: {row.get('measured')} {row.get('unit', '')}; Threshold: {row.get('threshold')}")
        add("Calculation: " + str(row.get("calculation_method") or "Not established"))
        add("Explanation: " + str(row.get("explanation") or "Unknown"))
        add("Source: " + str(row.get("source_url") or "Missing"))
        add("Recommended action: " + str(row.get("suggested_action") or "Qualified review required"))
    add("Unresolved information", "Heading2")
    for value in result.get("missing_information", [])[:100]:
        add(value)
    if result.get("coverage"):
        add("Category coverage — full compliance unknown", "Heading2")
        for item in result["coverage"][:100]:
            add(f"{item.get('code_family')} / {item.get('category')}: {item.get('coverage')}")
    add(result.get("disclaimer") or "Professional review required.")
    document = SimpleDocTemplate(stream, pagesize=A4, title="KRAFZEN Code Evidence",
                                 author="KRAFZEN AI", rightMargin=42, leftMargin=42,
                                 topMargin=40, bottomMargin=40)
    document.build(story)
    return stream.getvalue()
