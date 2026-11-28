from io import StringIO
import ezdxf
from app.services.dxf_review_findings import inspect_dxf_review


def test_source_backed_review_findings():
    doc=ezdxf.new()
    m=doc.modelspace()
    a=m.add_line((0,0,0),(2,0,0))
    b=m.add_line((2,0,0),(0,0,0))
    m.add_line((0,0,1),(2,0,1))
    m.add_line((0,0,0),(2,0,0),dxfattribs={"layer":"OTHER"})
    m.add_line((1,1,0),(1,1,0))
    m.add_circle((1,1),.2)
    out=StringIO();doc.write(out)
    result=inspect_dxf_review(out.getvalue().encode())
    assert result["checked_line_count"]==5
    assert result["unchecked_entity_count"]==1
    assert result["finding_count"]==2
    duplicate=next(f for f in result["findings"] if f["kind"]=="coincident_line")
    assert set(duplicate["handles"])=={a.dxf.handle,b.dxf.handle}
    assert duplicate["occurrence_count"]==2
    assert duplicate["x"]==.5
    assert 0<=duplicate["y"]<=1
