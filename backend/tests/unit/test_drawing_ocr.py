from io import BytesIO
import shutil
import pytest
from PIL import Image,ImageDraw,ImageFont
from app.services.drawing_ocr import recognize_drawing_image

def test_missing_runtime_is_not_success(monkeypatch):
    monkeypatch.setattr(shutil,"which",lambda _:None)
    assert recognize_drawing_image(b"test")["optical_character_recognition_performed"] is False

@pytest.mark.skipif(not shutil.which("tesseract"),reason="native OCR not installed")
def test_actual_drawing_text_recognition():
    font=ImageFont.truetype("DejaVuSans.ttf",42)
    image=Image.new("RGB",(1000,500),"white")
    draw=ImageDraw.Draw(image)
    draw.rectangle((20,20,980,480),outline="black",width=2)
    for y,line in [(60,"ROOM 101"),(180,"WIDTH 3200 MM"),(300,"DOOR D01")]:
        draw.text((80,y),line,font=font,fill="black")
    out=BytesIO();image.save(out,format="PNG")
    result=recognize_drawing_image(out.getvalue())
    assert result["optical_character_recognition_performed"]
    assert "3200" in result["ocr_text_excerpt"]
    assert "ROOM" in result["ocr_text_excerpt"]
    assert result["ocr_measurements_verified"] is False
    assert all(len(word["bbox_px"])==4 for word in result["ocr_words"])
