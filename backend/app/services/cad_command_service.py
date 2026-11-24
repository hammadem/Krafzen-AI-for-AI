"""Deterministic, explicit-unit edit commands for generated parametric room DXF."""
import re
from app.services.parametric_cad_service import build_room_dxf

VALUE=r"(\d{1,5}(?:\.\d{1,6})?)\s*(mm|cm|m|ft|in)"
FACTORS={"mm":0.001,"cm":0.01,"m":1.0,"ft":0.3048,"in":0.0254}

def metre(value,unit):
    return round(float(value)*FACTORS[unit.lower()],9)

def propose_room_edit(metadata, command):
    if not isinstance(metadata,dict) or metadata.get("generation_method")!="parametric_room_v1":
        raise ValueError("Only source-verified parametric room drawings support command editing")
    if not isinstance(command,str) or len(command)>500 or not command.strip():
        raise ValueError("Enter a single supported edit command")
    data={"room_name":metadata["room_name"],"exterior_width_m":metadata["exterior_width_m"],
          "exterior_length_m":metadata["exterior_length_m"],"wall_thickness_m":metadata["wall_thickness_m"],
          "openings":[dict(x) for x in metadata.get("openings",[])]}
    value=command.strip().rstrip(".")
    match=re.fullmatch(r"(?:set|change) (?:exterior )?(width|length|wall thickness) to "+VALUE,value,re.I)
    if match:
        field={"width":"exterior_width_m","length":"exterior_length_m","wall thickness":"wall_thickness_m"}[match[1].lower()]
        data[field]=metre(match[2],match[3])
    else:
        match=re.fullmatch(r"add (door|window) on (north|south|east|west)(?: wall)? at "+VALUE+r" (?:with )?(?:clear )?width "+VALUE,value,re.I)
        if match:
            data["openings"].append({"kind":match[1].lower(),"side":match[2].lower(),
                "offset_m":metre(match[3],match[4]),"clear_width_m":metre(match[5],match[6])})
        else:
            match=re.fullmatch(r"remove opening (\d{1,2})",value,re.I)
            if match:
                index=int(match[1])-1
                if index<0 or index>=len(data["openings"]): raise ValueError("Opening number does not exist")
                data["openings"].pop(index)
            else:
                match=re.fullmatch(r"rename room to (.{1,80})",value,re.I)
                if not match:
                    raise ValueError("Supported commands: set width/length/wall thickness to 6 m; add door on south at 1 m width 0.9 m; remove opening 1; rename room to Office. Explicit units required.")
                data["room_name"]=match[1].strip()
    _, geometry=build_room_dxf(name=data["room_name"],width_m=data["exterior_width_m"],
        length_m=data["exterior_length_m"],wall_thickness_m=data["wall_thickness_m"],openings=data["openings"])
    # Validate with the same generation limits as the existing geometry engine.
    return data,geometry
