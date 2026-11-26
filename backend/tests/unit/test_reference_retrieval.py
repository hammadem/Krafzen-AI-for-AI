from pathlib import Path
import json
import shutil
import pytest
from app.services.reference_retrieval import ROOT, _load_index, reference_register, retrieve_reference, format_reference_answer

def test_license_gate_hash_verified_index_and_retrieval():
    result=reference_register()
    assert result["dataset_count"]>=6
    assert all(row["license"].endswith("(CC BY 4.0)") for row in result["datasets"])
    hits=retrieve_reference("IFC wall opening window")
    assert hits and hits[0]["dataset_id"]=="ifc4_wall_opening_window.ifc"
    assert hits[0]["entity_counts"]["IfcWindow"]==1
    answer=format_reference_answer(hits)
    assert "buildingSMART" in answer and "CC BY 4.0" in answer and "Source SHA-256" in answer
    assert retrieve_reference("qzxvunknownmaterial") == []

def test_tampered_reference_rejected(tmp_path:Path):
    shutil.copytree(ROOT,tmp_path/"reference")
    root=tmp_path/"reference"
    item=json.loads((root/"reference_manifest.json").read_text())["ifc_files"][0]
    path=root/item["name"]
    path.write_bytes(path.read_bytes()+b"\n")
    with pytest.raises(ValueError,match="integrity"):
        _load_index(root)


@pytest.mark.parametrize("question", [
    "IFC model qzxvunknownmaterial",
    "customer project verified construction",
    "IFC quantum entanglement",
])
def test_generic_or_boilerplate_terms_do_not_return_unrelated_reference(question):
    assert retrieve_reference(question) == []


def test_technical_schema_and_discipline_terms_remain_searchable():
    hits = retrieve_reference("IFC4 structural beams")
    assert hits
    assert hits[0]["discipline"] == "structural"
