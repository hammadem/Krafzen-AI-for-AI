"""Native smoke check using synthetic drawing only; not a full fidelity claim."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import ezdxf

tools=Path(__file__).resolve().parents[1]/"bin"/"libredwg"/"bin"
with TemporaryDirectory(prefix="krafzen-dwg-smoke-") as work:
    root=Path(work)
    source=root/"source.dxf"; dwg=root/"source.dwg"; recovered=root/"recovered.dxf"
    drawing=ezdxf.new("R2000")
    drawing.header["$INSUNITS"]=4
    drawing.layers.new("QA_GEOMETRY")
    drawing.modelspace().add_line((0,0,0),(1000,500,0),dxfattribs={"layer":"QA_GEOMETRY"})
    drawing.modelspace().add_circle((100,200,0),50,dxfattribs={"layer":"QA_GEOMETRY"})
    drawing.saveas(source)
    subprocess.run([str(tools/"dxf2dwg"),"--as=r2000","-o",str(dwg),str(source)],check=True,timeout=180)
    assert dwg.read_bytes()[:6]==b"AC1015"
    subprocess.run([str(tools/"dwg2dxf"),"-o",str(recovered),str(dwg)],check=True,timeout=180)
    result=ezdxf.readfile(recovered)
    assert result.header["$INSUNITS"]==4
    lines=list(result.modelspace().query("LINE"))
    circles=list(result.modelspace().query("CIRCLE"))
    assert len(lines)==len(circles)==1
    assert tuple(lines[0].dxf.end)==(1000,500,0)
    assert tuple(circles[0].dxf.center)==(100,200,0)
    assert circles[0].dxf.radius==50
    assert lines[0].dxf.layer==circles[0].dxf.layer=="QA_GEOMETRY"
print("Actual LibreDWG R2000 native round trip passed for synthetic LINE/CIRCLE, units and layers")
