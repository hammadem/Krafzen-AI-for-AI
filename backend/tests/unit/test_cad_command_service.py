import pytest
from app.services.parametric_cad_service import build_room_dxf
from app.services.cad_command_service import propose_room_edit

def fixture():
    return build_room_dxf(name="Office",width_m=5,length_m=4,wall_thickness_m=.2,openings=[])[1]

def test_edit_explicit_dimensions_and_openings():
    original=fixture()
    data,geometry=propose_room_edit(original,"set width to 6000 mm")
    assert data["exterior_width_m"]==6
    assert geometry["interior_clear_area_m2"]==20.16
    assert original["exterior_width_m"]==5
    _,geometry=propose_room_edit(original,"add door on south at 1 m width 900 mm")
    assert geometry["openings"][0]["clear_width_m"]==.9
    _,removed=propose_room_edit(geometry,"remove opening 1")
    assert not removed["openings"]
    for command in ["make bigger","set width to 6","add door on south at 4.9 m width 0.9 m","remove opening 1"]:
        with pytest.raises(ValueError): propose_room_edit(original,command)
