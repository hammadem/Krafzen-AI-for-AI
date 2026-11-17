"""Real Potrace DXF integration smoke test, run in CI with native tracer installed."""

import base64
from io import BytesIO
from pathlib import Path

import ezdxf
import pytest
from PIL import Image, ImageDraw

from app.services.local_dxf_service import LocalDxfService


@pytest.mark.asyncio
async def test_real_potrace_generates_readable_nonempty_dxf(tmp_path):
    image = Image.new("RGB", (200, 150), "white")
    drawing = ImageDraw.Draw(image)
    drawing.rectangle((20, 20, 180, 130), outline="black", width=7)
    drawing.line((20, 75, 180, 75), fill="black", width=5)
    png = BytesIO()
    image.save(png, format="PNG")
    source = "data:image/png;base64," + base64.b64encode(png.getvalue()).decode()

    service = LocalDxfService(output_dir=str(tmp_path))
    path = await service.convert_to_dxf(source)
    try:
        assert Path(path).stat().st_size > 500
        doc = ezdxf.readfile(path)
        assert len(list(doc.modelspace())) >= 1
    finally:
        Path(path).unlink(missing_ok=True)
