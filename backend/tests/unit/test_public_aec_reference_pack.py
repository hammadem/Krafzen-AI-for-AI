"""Regression checks against independently sourced IFC and measured DXF QA fixtures.

IFCs are original buildingSMART CC BY 4.0 certification models and must
remain byte-identical to their attributed upstream Git blobs.
DXFs are deterministic synthetic QA layouts with explicit millimetre truth.
"""
import hashlib
import json
from io import StringIO
from pathlib import Path
import sys

import ezdxf
import ifcopenshell

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tests/fixtures/aec_reference"
sys.path.insert(0, str(ROOT / "scripts"))
from generate_aec_reference_dxf import generate  # noqa: E402


def test_original_buildingsmart_ifc_files_are_attributed_and_unchanged():
    manifest=json.loads((SOURCE / "reference_manifest.json").read_text())
    assert manifest["license"] == (
        "Creative Commons Attribution 4.0 International (CC BY 4.0)"
    )
    assert (SOURCE / "BUILDINGSMART_LICENSE.txt").exists()
    assert len(manifest["ifc_files"]) >= 6

    for item in manifest["ifc_files"]:
        path = SOURCE / item["name"]
        raw = path.read_bytes()
        assert raw.startswith(b"ISO-10303-21;"), item["name"]
        assert raw.rstrip().endswith(b"END-ISO-10303-21;"), item["name"]
        # Git blob hash authenticates bytes against the original upstream file.
        header=f"blob {len(raw)}\0".encode()
        blob=hashlib.sha1(header+raw).hexdigest()
        assert blob == item["blob"], f"Reference IFC modified: {item['name']}"
        assert len(raw) <= 4 * 1024 * 1024
        assert item["source_url"].startswith(
            "https://github.com/buildingSMART/Certification-datasets/blob/main/"
        )


def test_ifc_examples_are_real_parseable_multidiscipline_models():
    manifest=json.loads((SOURCE / "reference_manifest.json").read_text())
    covered=set()
    for item in manifest["ifc_files"]:
        model=ifcopenshell.open(str(SOURCE / item["name"]))
        assert model.schema.upper().startswith(
            item["schema"].replace("_ADD2", "")
        )
        assert len(model.by_type("IfcProject")) >= 1
        for entity,min_count in item["expected_min"].items():
            count=len(model.by_type(entity))
            assert count>=min_count, (item["name"],entity,count)
        covered.add(item["schema"])
    assert {"IFC2X3", "IFC4", "IFC4X3_ADD2"} <= covered


def test_known_studio_geometry_and_revision_delta(tmp_path):
    truth=generate(tmp_path)
    original=ezdxf.readfile(tmp_path/"residential_studio_original.dxf")
    revised=ezdxf.readfile(
        tmp_path/"residential_studio_asbuilt_entrance_shift_300mm.dxf"
    )
    for model in (original,revised):
        assert model.header["$INSUNITS"] == 4
        assert len(model.modelspace().query("DIMENSION")) >= 5
        assert len(model.modelspace().query('LINE[layer=="A-WALL"]')) >= 14
        assert len(model.modelspace().query('ARC[layer=="A-DOOR"]')) == 1
    old_door=list(original.modelspace().query('ARC[layer=="A-DOOR"]'))[0]
    revised_door=list(revised.modelspace().query('ARC[layer=="A-DOOR"]'))[0]
    delta=float(revised_door.dxf.center.x-old_door.dxf.center.x)
    assert delta == 300.0
    assert delta == truth["studio"]["door_shift_mm"]
    assert original.modelspace().query("DIMENSION")[0].dxf.text == "6400"
    assert revised.modelspace().query("DIMENSION")[0].dxf.text == "6400"


def test_known_structural_and_mep_measurements(tmp_path):
    truth=generate(tmp_path)
    structural=ezdxf.readfile(tmp_path/"structural_8x6m_grid.dxf")
    mep=ezdxf.readfile(tmp_path/"mep_duct_pipe_route.dxf")
    assert structural.header["$INSUNITS"] == 4
    assert len(structural.modelspace().query('LWPOLYLINE[layer=="S-COLUMN"]')) == 9
    assert len(structural.modelspace().query('LINE[layer=="S-BEAM"]')) == 6
    assert len(structural.modelspace().query("DIMENSION")) == 4
    assert mep.header["$INSUNITS"] == 4
    assert len(mep.modelspace().query('LWPOLYLINE[layer=="M-DUCT"]')) == 1
    assert len(mep.modelspace().query('CIRCLE[layer=="M-PIPE"]')) == 1
    circle=list(mep.modelspace().query('CIRCLE[layer=="M-PIPE"]'))[0]
    assert circle.dxf.radius*2 == truth["mep"]["pipe_plan_nominal_diameter_mm"]
    assert truth["mep"]["3d_clash_verified"] is False
    saved=json.loads((tmp_path/"reference_ground_truth.json").read_text())
    assert saved==truth
