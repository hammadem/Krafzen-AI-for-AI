from io import BytesIO, StringIO
import ezdxf
import pytest
from pypdf import PdfReader
from app.services.review_pdf_service import build_review_pdf

def test_source_bound_review_pdf():
    drawing=ezdxf.new("R2010")
    drawing.modelspace().add_line((0,0),(10,10))
    drawing.modelspace().add_circle((5,5),1)
    out=StringIO()
    drawing.write(out)
    record={"id":"drawing","project_id":"project","version":2}
    marks=[{"id":"redline-1","file_id":"drawing","file_version":2,"kind":"arrow","x":0.1,"y":0.2,"x2":0.8,"y2":0.9,"severity":"medium","status":"open","comment":"Check beam alignment"}]
    result=build_review_pdf(out.getvalue().encode(), record, marks)
    pdf=PdfReader(BytesIO(result))
    assert len(pdf.pages)==2
    assert "Drawing version 2" in pdf.pages[0].extract_text()
    assert "Source SHA-256" in pdf.pages[0].extract_text()
    assert "Check beam alignment" in pdf.pages[1].extract_text()
    with pytest.raises(ValueError, match="version"):
        build_review_pdf(out.getvalue().encode(), record, [{**marks[0],"file_version":1}])
