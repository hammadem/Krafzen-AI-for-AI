import ezdxf
import pytest
from app.services.dwg_dxf_validation import validate_converted_dxf,normalize_zero_handles

def test_zero_handle_normalization_preserves_geometry(tmp_path):
    original=tmp_path/"source.dxf"; output=tmp_path/"canonical.dxf"
    doc=ezdxf.new("R2000")
    doc.header["$INSUNITS"]=4
    entity=doc.modelspace().add_line((0,0,0),(1000,500,0))
    doc.saveas(original)
    old=("\n  5\n"+entity.dxf.handle+"\n").encode()
    raw=original.read_bytes()
    assert old in raw
    original.write_bytes(raw.replace(old,b"\n  5\n0\n",1))
    with pytest.raises(ValueError,match="Invalid handle 0"):
        ezdxf.readfile(original)
    assert validate_converted_dxf(original,output)==1
    result=ezdxf.readfile(output)
    assert result.header["$INSUNITS"]==4
    assert tuple(result.modelspace()[0].dxf.end)==(1000,500,0)

def test_truncated_output_rejected():
    with pytest.raises(ValueError): normalize_zero_handles(b"0\nSECTION\n2\nENTITIES\n")
