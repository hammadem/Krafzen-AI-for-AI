"""Generate independent measured DXF QA fixtures and explicit ground truth.

Synthetic by design: built from fixed millimetre coordinates and true AutoCAD
DIMENSION entities; these are test drawings, NOT surveyed construction plans.

Run: python backend/scripts/generate_aec_reference_dxf.py --output-dir /tmp/aec-fixtures
"""
import argparse
import json
from pathlib import Path

import ezdxf

UNIT_MM = 4


def _base_drawing(title):
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = UNIT_MM
    doc.header["$MEASUREMENT"] = 1
    for layer in ("A-WALL", "A-DOOR", "A-WINDOW", "A-PARTITION",
                  "S-COLUMN", "S-BEAM", "M-DUCT", "M-PIPE", "DIMENSIONS", "NOTES"):
        if not doc.layers.has_entry(layer):
            doc.layers.new(layer)
    doc.modelspace().add_text(title, dxfattribs={
        "layer": "NOTES", "height": 120, "insert": (200, 5700),
    })
    return doc


def _line(space, a, b, layer):
    space.add_line(a, b, dxfattribs={"layer": layer})


def _dimension(space, p1, p2, base, angle, text):
    space.add_linear_dim(
        base=base, p1=p1, p2=p2, angle=angle,
        text=text, dimstyle="EZDXF",
        dxfattribs={"layer": "DIMENSIONS"},
        override={"dimtxt": 100, "dimasz": 60},
    ).render()


def studio(door_start):
    """Exterior 6400x4900 mm; internal clear 6000x4500 mm.

    v1 entrance door (800,1700); v2 (1100,2000). Pure 300 mm move.
    North window (2400,3600) and east window (1650,2850).
    """
    doc = _base_drawing(f"QA Studio Floor Plan; entrance at X={door_start} mm")
    model = doc.modelspace()
    door_end = door_start + 900
    # South exterior wall has the genuine 900 mm door opening.
    for wall_y in (0, 200):
        _line(model, (0, wall_y), (door_start, wall_y), "A-WALL")
        _line(model, (door_end, wall_y), (6400, wall_y), "A-WALL")
    for x in (door_start, door_end):
        _line(model, (x, 0), (x, 200), "A-DOOR")
    model.add_arc(
        center=(door_start, 200), radius=900, start_angle=0, end_angle=90,
        dxfattribs={"layer": "A-DOOR"},
    )
    _line(model, (door_start, 200), (door_start+900, 200), "A-DOOR")
    # North wall + 1200 mm window: no invented wall behind the opening.
    for wall_y in (4700, 4900):
        _line(model, (0,wall_y), (2400,wall_y), "A-WALL")
        _line(model, (3600,wall_y), (6400,wall_y), "A-WALL")
    for x in (2400, 3600):
        _line(model, (x,4700), (x,4900), "A-WINDOW")
    # East wall + 1200 mm opening.
    for wall_x in (6200,6400):
        _line(model, (wall_x,0), (wall_x,1650), "A-WALL")
        _line(model, (wall_x,2850), (wall_x,4900), "A-WALL")
    for y in (1650,2850):
        _line(model, (6200,y), (6400,y), "A-WINDOW")
    # West wall uninterrupted.
    for wall_x in (0,200):
        _line(model, (wall_x,0), (wall_x,4900), "A-WALL")
    # Upper-left WC: 1800x1500 mm clear, 100mm internal partition.
    _line(model,(2100,3100),(2100,4700),"A-PARTITION")
    _line(model,(200,3100),(2100,3100),"A-PARTITION")
    _line(model,(200,3200),(2000,3200),"A-PARTITION")
    _line(model,(2000,3200),(2000,4700),"A-PARTITION")
    model.add_text("STUDIO 6000 x 4500 CLEAR", dxfattribs={
        "layer": "NOTES", "insert":(2600,2350),"height":100,
    })
    _dimension(model,(0,0),(6400,0),(3200,-700),0,"6400")
    _dimension(model,(0,0),(0,4900),(-700,2450),90,"4900")
    _dimension(model,(200,400),(6200,400),(3200,700),0,"6000")
    _dimension(model,(door_start,200),(door_end,200),
               (door_start+450,-350),0,"900")
    _dimension(model,(2400,4900),(3600,4900),(3000,5350),0,"1200")
    return doc


def structural_grid():
    """9 reinforced columns on 4000 mm by 3000 mm structural grid."""
    doc = _base_drawing("QA Structural Grid 8000 x 6000 mm")
    m = doc.modelspace()
    for x in (0,4000,8000):
        for y in (0,3000,6000):
            m.add_lwpolyline([
                (x-200,y-200),(x+200,y-200),
                (x+200,y+200),(x-200,y+200),
            ], close=True, dxfattribs={"layer":"S-COLUMN"})
    for y in (0,3000,6000):
        _line(m,(0,y),(8000,y),"S-BEAM")
    for x in (0,4000,8000):
        _line(m,(x,0),(x,6000),"S-BEAM")
    _dimension(m,(0,0),(4000,0),(2000,-900),0,"4000")
    _dimension(m,(4000,0),(8000,0),(6000,-900),0,"4000")
    _dimension(m,(0,0),(0,3000),(-900,1500),90,"3000")
    _dimension(m,(0,3000),(0,6000),(-900,4500),90,"3000")
    return doc


def mep_grid():
    """MEP routing measured in mm; no actual 3D coordination asserted."""
    doc=_base_drawing("QA MEP 600 mm Duct / 150 mm Pipe")
    m=doc.modelspace()
    # Plan duct rectangle 8000 x 600 with known width.
    m.add_lwpolyline([
        (0,2700),(8000,2700),(8000,3300),(0,3300)
    ],close=True,dxfattribs={"layer":"M-DUCT"})
    _line(m,(0,3000),(8000,3000),"M-DUCT")
    # Plan pipe centreline, 150 mm nominal width (not a pipe sizing approval).
    _line(m,(4000,0),(4000,6000),"M-PIPE")
    m.add_circle((4000,3000),radius=75,dxfattribs={"layer":"M-PIPE"})
    _dimension(m,(0,2700),(0,3300),(-450,3000),90,"600")
    _dimension(m,(0,3000),(8000,3000),(4000,3800),0,"8000")
    return doc


def generate(output):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    drawings={
        "residential_studio_original.dxf":studio(800),
        "residential_studio_asbuilt_entrance_shift_300mm.dxf":studio(1100),
        "structural_8x6m_grid.dxf":structural_grid(),
        "mep_duct_pipe_route.dxf":mep_grid(),
    }
    for name,doc in drawings.items():
        auditor=doc.audit()
        if auditor.has_errors:
            raise RuntimeError(f"Invalid DXF reference drawing: {name}")
        doc.saveas(str(output/name))
    truth={
        "disclaimer":"Synthetic measured regression fixtures, not surveyed or approved engineering designs.",
        "drawing_units":"millimetres","autocad_INSUNITS":UNIT_MM,
        "studio":{
            "exterior_mm":{"width":6400,"height":4900},
            "interior_clear_mm":{"width":6000,"height":4500},
            "door_original_start_x_mm":800,
            "door_asbuilt_start_x_mm":1100,
            "door_width_mm":900,"door_shift_mm":300,
            "north_window_width_mm":1200,
            "east_window_width_mm":1200,
            "wc_clear_mm":{"width":1800,"height":1500},
            "real_dimension_entities_min":5
        },
        "structural":{
            "grid_x_mm":[0,4000,8000],
            "grid_y_mm":[0,3000,6000],
            "column_count":9,"column_width_mm":400,
            "structural_beam_span_x_mm":4000,
            "structural_beam_span_y_mm":3000
        },
        "mep":{
            "duct_rectangle_length_mm":8000,
            "duct_rectangle_width_mm":600,
            "pipe_plan_nominal_diameter_mm":150,
            "3d_clash_verified":False,
        },
    }
    (output/"reference_ground_truth.json").write_text(
        json.dumps(truth,indent=2)+"\n",encoding="utf-8"
    )
    return truth


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    result=generate(args.output_dir)
    print(json.dumps(result,indent=2))
