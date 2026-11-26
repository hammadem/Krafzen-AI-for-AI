"""Narrow normalization for a known LibreDWG DXF output defect.

Do not use this on arbitrary uploads. The DWG source and converter output must
be scanned before parsing. A successful parse is not a fidelity certificate.
"""
from pathlib import Path
import re
import ezdxf

MAX_BYTES=25*1024*1024

def normalize_zero_handles(raw:bytes)->tuple[bytes,int]:
    if not 0<len(raw)<=MAX_BYTES or raw.startswith(b"AutoCAD Binary DXF") or b"\x00" in raw[:1024]:
        raise ValueError("Unsupported converter output")
    lines=raw.splitlines(keepends=True)
    if len(lines)%2:
        raise ValueError("Incomplete DXF tag stream")
    tags=[]
    for i in range(0,len(lines),2):
        try: code=int(lines[i].strip())
        except ValueError as exc: raise ValueError("Invalid DXF tag code") from exc
        tags.append((i,code,lines[i+1].strip()))
    if not tags or tags[-1][1:]!=(0,b"EOF"):
        raise ValueError("DXF EOF missing")
    # Include reference tags when reserving the handle namespace. Never
    # reassign a real nonzero handle or rewrite null owner references.
    used=set()
    for _,code,value in tags:
        if code in (5,105,1005) or 320<=code<=369 or 390<=code<=399:
            if re.fullmatch(rb"[0-9A-Fa-f]{1,16}",value):
                used.add(int(value,16))
    next_handle=max(used,default=0)+1
    section=None;waiting=False;count=0;seed_line=None
    for i,code,value in tags:
        if code==0 and value==b"SECTION":
            waiting=True;section=None
        elif waiting:
            if code!=2: raise ValueError("Invalid section header")
            section=value;waiting=False
        elif code==0 and value==b"ENDSEC":
            section=None
        elif section==b"HEADER" and code==9:
            seed_line=i+3 if value==b"$HANDSEED" and i+3<len(lines) and lines[i+2].strip()==b"5" else seed_line
        elif section not in (None,b"HEADER") and code in (5,105) and value==b"0":
            if next_handle>=2**64: raise ValueError("Handle range exhausted")
            end=b"\r\n" if lines[i+1].endswith(b"\r\n") else b"\n"
            lines[i+1]=format(next_handle,"X").encode()+end
            next_handle+=1;count+=1
    if count and seed_line is not None:
        end=b"\r\n" if lines[seed_line].endswith(b"\r\n") else b"\n"
        lines[seed_line]=format(next_handle,"X").encode()+end
    return b"".join(lines),count

def validate_converted_dxf(source:Path,destination:Path)->int:
    if not 0<source.stat().st_size<=MAX_BYTES:
        raise ValueError("Converter output exceeds supported size")
    raw=source.read_bytes()
    try:
        doc=ezdxf.readfile(source)
        fixed=0
        destination.write_bytes(raw)
    except ValueError as exc:
        if str(exc)!="Invalid handle 0.":
            raise
        corrected,fixed=normalize_zero_handles(raw)
        if not fixed:
            raise ValueError("No repairable zero handle found") from exc
        destination.write_bytes(corrected)
        doc=ezdxf.readfile(destination)
    if not any(True for _ in doc.modelspace()):
        raise ValueError("No modelspace geometry")
    return fixed
