"""Create honest, non-dimensionally-certified project image reference PDFs."""
import base64
import binascii
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

_MAX_INPUT_BYTES = 20 * 1024 * 1024
_MAX_PIXELS = 25_000_000
_MAX_PDF_BYTES = 50 * 1024 * 1024
_MIME = {"png": "PNG", "jpeg": "JPEG", "webp": "WEBP"}


def create_reference_pdf(image_uri: str) -> bytes:
    """Render the real stored project image with a visible verification warning.

    This is a visual-document export, not an architectural scaled plan.
    Raster input cannot guarantee geometry, dimensions, regulatory compliance,
    or construction suitability. PDF bytes come from the actual source image.
    """
    if not isinstance(image_uri, str) or not image_uri.startswith("data:image/"):
        raise ValueError("A PNG, JPEG or WebP source image data URI is required")
    try:
        header, b64 = image_uri.split(",", 1)
        kind = header.removeprefix("data:image/").removesuffix(";base64").lower()
        if header != f"data:image/{kind};base64" or kind not in _MIME:
            raise ValueError("Unsupported project image type")
        encoded_size = (len(b64) * 3) // 4
        if encoded_size > _MAX_INPUT_BYTES:
            raise ValueError("Stored project image exceeds reference PDF limit")
        source = base64.b64decode(b64, validate=True)
        if not source or len(source) > _MAX_INPUT_BYTES:
            raise ValueError("Stored project image is empty or exceeds limit")
        image = Image.open(BytesIO(source))
        if image.format != _MIME[kind]:
            raise ValueError("Image bytes do not match the declared type")
        width_px, height_px = image.size
        if (not width_px or not height_px or
                width_px * height_px > _MAX_PIXELS):
            raise ValueError("Project image dimensions exceed reference PDF limit")
        image.load()
        image = image.convert("RGB")
    except (ValueError, UnidentifiedImageError, OSError, binascii.Error) as exc:
        raise ValueError("Stored project image cannot be rendered safely") from exc

    stream = BytesIO()
    width, height = landscape(letter)
    pdf = canvas.Canvas(stream, pagesize=(width, height), pageCompression=1)
    pdf.setTitle("KRAFZEN Project Visual Reference — Not Dimensionally Verified")
    pdf.setAuthor("KRAFZEN AI")
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(35, height - 35, "PROJECT VISUAL REFERENCE")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(35, height - 52, "Source: project image stored with this project.")
    pdf.setFillColorRGB(0.7, 0.12, 0.10)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(35, 24, "NOT DIMENSIONALLY VERIFIED — NOT FOR CONSTRUCTION OR CODE APPROVAL")
    pdf.setFillColorRGB(0, 0, 0)

    available_width = width - 70
    available_height = height - 115
    ratio = min(available_width / width_px, available_height / height_px)
    draw_width = width_px * ratio
    draw_height = height_px * ratio
    pdf.drawImage(
        ImageReader(image),
        35 + (available_width - draw_width) / 2,
        48 + (available_height - draw_height) / 2,
        width=draw_width, height=draw_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    pdf.showPage()
    pdf.save()
    content = stream.getvalue()
    if not content.startswith(b"%PDF-") or len(content) > _MAX_PDF_BYTES:
        raise ValueError("Generated PDF failed file-integrity validation")
    return content
