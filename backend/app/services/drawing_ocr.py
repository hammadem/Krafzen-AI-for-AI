"""Optional local OCR of previously scanned drawings; no inferred dimensions."""
import csv
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

def recognize_drawing_image(raw: bytes) -> dict:
    from PIL import Image, ImageOps
    engine=shutil.which("tesseract")
    if not engine:
        return {"optical_character_recognition_performed":False,"ocr_status":"engine_unavailable"}
    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.width*source.height>25_000_000 or getattr(source,"n_frames",1)!=1:
                raise ValueError("Image exceeds OCR budget or is animated")
            image=ImageOps.exif_transpose(source).convert("L")
            image.thumbnail((2400,2400))
            width,height=image.size
            with tempfile.TemporaryDirectory(prefix="krafzen-ocr-") as directory:
                path=Path(directory)/"drawing.png"
                image.save(path)
                proc=subprocess.run([engine,str(path),"stdout","-l","eng","--psm","11","tsv"],
                    capture_output=True,timeout=12,check=False,env={**os.environ,"OMP_THREAD_LIMIT":"1"})
        if proc.returncode or len(proc.stdout)>2_000_000:
            raise ValueError("OCR unavailable")
        words=[]
        for row in csv.DictReader(io.StringIO(proc.stdout.decode("utf-8")),delimiter="\t"):
            if row.get("level")!="5" or not (row.get("text") or "").strip():continue
            conf=float(row["conf"])
            left,top,w,h=(int(row[k]) for k in ("left","top","width","height"))
            if not (0<=conf<=100 and 0<=left<width and 0<=top<height and w>0 and h>0 and left+w<=width and top+h<=height):
                continue
            words.append({"text":row["text"].strip()[:150],"confidence":conf,"bbox_px":[left,top,w,h]})
            if len(words)>=500:break
        return {"optical_character_recognition_performed":True,"ocr_status":"completed","ocr_engine":"tesseract_eng_psm11",
                "ocr_words":words,"ocr_text_excerpt":" ".join(w["text"] for w in words)[:12000],"ocr_width_px":width,"ocr_height_px":height,
                "ocr_truncated":len(words)>=500,"ocr_coordinates":"EXIF-oriented, resized OCR image pixels",
                "ocr_measurements_verified":False}
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired,UnicodeError):
        return {"optical_character_recognition_performed":False,"ocr_status":"unavailable_or_failed"}
