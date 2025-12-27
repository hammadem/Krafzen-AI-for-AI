#!/usr/bin/env python3
"""
Augment enhanced dataset with explicit coordinates.

This script reads the enhanced dataset (natural language descriptions) and
augments it with explicit coordinate outputs in a parseable DSL format.

Usage:
    python augment_with_coordinates.py \
        --input ../jsonl/cadllm_enhanced.jsonl \
        --output ../jsonl/cadllm_enhanced_with_coords.jsonl \
        --max_rows 50000
"""

import json
import re
import random
import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import argparse

# Constants
WALL_THICKNESS = 100  # mm
DEFAULT_SETBACK = 50  # mm from inner face of wall
MIN_GAP = 50  # mm between adjacent objects along a wall

ROOM_DEFAULTS = {
    "kitchen": (4000, 3000),
    "bedroom": (3000, 3000),
    "bathroom": (2000, 2000),
    "living room": (6000, 5000),
}

# Regex patterns
ROOM_RE = re.compile(r"(?i)(kitchen|bedroom|bathroom|living room).*?\((\d+)mm\s*x\s*(\d+)mm\)")
SIZE_RE = re.compile(r"(?i)(\d+)\s*mm\s*x\s*(\d+)\s*mm")
RADIUS_RE = re.compile(r"(?i)(\d+)\s*mm\s*radius|\br\s*=\s*(\d+)")
WALL_RE = re.compile(r"(?i)\bon\s+(north|south|east|west)\s+wall\b")
CENTER_RE = re.compile(r"(?i)\bon\s+center|centered")


def pick_room_dims(text: str, instruction: str) -> Tuple[int, int]:
    """Extract room dimensions from text or use defaults based on room type."""
    m = ROOM_RE.search(text)
    if m:
        return int(m.group(2)), int(m.group(3))
    # Fallback from instruction keywords
    low = (instruction + " " + text).lower()
    for k, (w, h) in ROOM_DEFAULTS.items():
        if k in low:
            return w, h
    return 4000, 3000


def wall_center_xy(wall: str, room_w: int, room_h: int, obj_w: int, obj_h: int, along: float) -> Tuple[float, float]:
    """
    Calculate center coordinates for an object placed on a wall.
    Properly accounts for object size to ensure it stays within room bounds.
    
    Formula:
    - south wall: y = -H/2 + (wall_thickness + setback + h/2)
    - north wall: y = +H/2 - (wall_thickness + setback + h/2)
    - west wall:  x = -W/2 + (wall_thickness + setback + w/2)
    - east wall:  x = +W/2 - (wall_thickness + setback + w/2)
    """
    room_half_w = room_w / 2
    room_half_h = room_h / 2
    
    if wall == "north":
        # Constrain along (x coordinate) to keep object within bounds
        max_along = room_half_w - obj_w / 2
        along = max(-max_along, min(along, max_along))
        x = along
        # Calculate y based on object's actual height
        y = +room_half_h - (WALL_THICKNESS + DEFAULT_SETBACK + obj_h / 2)
        # Double-check: ensure object doesn't extend beyond room
        assert y + obj_h / 2 <= room_half_h, f"North wall object extends beyond room: y={y}, obj_h={obj_h}, room_half={room_half_h}"
    elif wall == "south":
        # Constrain along (x coordinate)
        max_along = room_half_w - obj_w / 2
        along = max(-max_along, min(along, max_along))
        x = along
        # Calculate y based on object's actual height
        y = -room_half_h + (WALL_THICKNESS + DEFAULT_SETBACK + obj_h / 2)
        # Double-check: ensure object doesn't extend beyond room
        assert y - obj_h / 2 >= -room_half_h, f"South wall object extends beyond room: y={y}, obj_h={obj_h}, room_half={room_half_h}"
    elif wall == "east":
        # Constrain along (y coordinate)
        max_along = room_half_h - obj_h / 2
        along = max(-max_along, min(along, max_along))
        y = along
        # Calculate x based on object's actual width
        x = +room_half_w - (WALL_THICKNESS + DEFAULT_SETBACK + obj_w / 2)
        # Double-check: ensure object doesn't extend beyond room
        assert x + obj_w / 2 <= room_half_w, f"East wall object extends beyond room: x={x}, obj_w={obj_w}, room_half={room_half_w}"
    elif wall == "west":
        # Constrain along (y coordinate)
        max_along = room_half_h - obj_h / 2
        along = max(-max_along, min(along, max_along))
        y = along
        # Calculate x based on object's actual width
        x = -room_half_w + (WALL_THICKNESS + DEFAULT_SETBACK + obj_w / 2)
        # Double-check: ensure object doesn't extend beyond room
        assert x - obj_w / 2 >= -room_half_w, f"West wall object extends beyond room: x={x}, obj_w={obj_w}, room_half={room_half_w}"
    else:  # "none" or "center" - free placement
        # Constrain to room bounds
        max_x = room_half_w - obj_w / 2
        max_y = room_half_h - obj_h / 2
        x = max(-max_x, min(along if abs(along) < max_x else 0.0, max_x))
        y = max(-max_y, min(0.0, max_y))
    return x, y


def validate_bounds(x: float, y: float, obj_w: float, obj_h: float, room_w: int, room_h: int) -> bool:
    """Check if object bounding box is within room bounds."""
    half_w = obj_w / 2
    half_h = obj_h / 2
    room_half_w = room_w / 2
    room_half_h = room_h / 2
    
    # Check if object extends beyond room bounds
    return (x - half_w >= -room_half_w and 
            x + half_w <= room_half_w and
            y - half_h >= -room_half_h and
            y + half_h <= room_half_h)


def check_overlap(x1: float, y1: float, w1: float, h1: float,
                  x2: float, y2: float, w2: float, h2: float,
                  min_gap: float = 10.0) -> bool:
    """Check if two rectangles overlap (with optional minimum gap)."""
    # Expand bounding boxes by min_gap
    w1_exp = w1 + min_gap
    h1_exp = h1 + min_gap
    w2_exp = w2 + min_gap
    h2_exp = h2 + min_gap
    
    # Check axis-aligned bounding box overlap
    return not (x1 + w1_exp/2 < x2 - w2_exp/2 or
                x1 - w1_exp/2 > x2 + w2_exp/2 or
                y1 + h1_exp/2 < y2 - h2_exp/2 or
                y1 - h1_exp/2 > y2 + h2_exp/2)


def non_overlapping_slots(room_w: int, room_h: int, wall: str, widths_or_heights: List[int]) -> List[float]:
    """
    Assign positions along a wall without overlap, ensuring all slots are within bounds.
    For N/S we slot along X using object widths.
    For E/W we slot along Y using object heights.
    
    Returns list of 'along' coordinates (x for N/S, y for E/W) that keep all objects within bounds.
    """
    if not widths_or_heights:
        return []
    
    sizes = widths_or_heights
    
    # Available span along wall axis - must account for largest object's half-size on each side
    if wall in ("north", "south"):
        # For N/S walls, objects are placed along X axis
        # Available span: room width minus space needed for largest object on each side
        max_obj_half = max(sizes) / 2
        span = room_w - 2 * max_obj_half  # Ensure largest object fits
        if span <= 0:
            # Objects too large - return centered positions (will be constrained later)
            return [0.0] * len(sizes)
    else:
        # For E/W walls, objects are placed along Y axis
        max_obj_half = max(sizes) / 2
        span = room_h - 2 * max_obj_half
        if span <= 0:
            return [0.0] * len(sizes)

    # Calculate total space needed (including gaps)
    total = sum(sizes) + MIN_GAP * (len(sizes) - 1)
    
    # If objects don't fit, reduce gaps (but ensure they fit)
    if total > span:
        gap = max(10, (span - sum(sizes)) / max(1, (len(sizes) - 1)))  # Min 10mm gap
    else:
        gap = MIN_GAP

    # Center the group within available span
    start = -total / 2
    cur = start
    slots = []
    for s in sizes:
        center = cur + s / 2
        # Constrain to keep object within bounds
        # For each object, max center = span/2 - object_half_size
        max_center = span / 2 - s / 2
        min_center = -span / 2 + s / 2
        center = max(min_center, min(center, max_center))
        slots.append(center)
        cur += s + gap
    
    return slots


def extract_wall_objects(lines: List[str]) -> List[Dict]:
    """
    Extract objects from bullet-point lines.
    Return list of dicts: name, shape, w, h, r (for circles), wall
    """
    objs = []
    for ln in lines:
        if not ln.strip().startswith("-"):
            continue
        wall_m = WALL_RE.search(ln)
        center_m = CENTER_RE.search(ln)
        size_m = SIZE_RE.search(ln)
        radius_m = RADIUS_RE.search(ln)
        
        # Standardize entity name (replace spaces with underscores)
        name = ln.strip()[1:].split(":")[0].strip().upper().replace(" ", "_")
        
        # Check for circle
        if radius_m or "circle" in ln.lower():
            r = int(radius_m.group(1)) if radius_m and radius_m.group(1) else int(radius_m.group(2)) if radius_m else 100
            shape = "circle"
            wall = None
            if wall_m:
                wall = wall_m.group(1).lower()
            elif center_m:
                wall = "none"  # Free placement
            else:
                wall = "none"  # Default for circles
            
            objs.append({"name": name, "shape": shape, "r": r, "wall": wall})
            continue
        
        # Rectangle/square
        if not size_m:
            continue

        w = int(size_m.group(1))
        h = int(size_m.group(2))
        shape = "rect"
        if "square" in ln.lower():
            shape = "rect"
            h = w
        
        wall = None
        if wall_m:
            wall = wall_m.group(1).lower()
        elif center_m:
            wall = "none"  # Free placement (center)
        else:
            # If no wall specified, assume free placement
            wall = "none"
        
        objs.append({"name": name, "shape": shape, "w": w, "h": h, "wall": wall})
    
    return objs


def augment_record(rec: Dict) -> Optional[Dict]:
    """Augment a record with coordinate-enriched output."""
    instr = rec.get("instruction", "").strip()
    out = rec.get("output", "").strip()

    # Split output into lines for parsing
    lines = out.splitlines()
    room_w, room_h = pick_room_dims(out, instr)

    # Gather wall-anchored objects we can parse
    wall_objs = extract_wall_objects(lines)

    if not wall_objs:
        return None  # Skip if we can't parse any objects

    # Group by wall and assign along positions
    by_wall = defaultdict(list)
    center_objs = []
    
    for o in wall_objs:
        if o["wall"] == "center":
            center_objs.append(o)
        else:
            by_wall[o["wall"]].append(o)

    placements = []
    
    # Handle wall-anchored objects - process each wall separately
    for wall, objs in by_wall.items():
        if not objs:
            continue
            
        # Calculate sizes along wall axis (width for N/S, height for E/W)
        sizes = []
        for o in objs:
            if o["shape"] == "circle":
                size = o["r"] * 2  # Diameter
            else:
                size = o.get("w") if wall in ("north", "south") else o.get("h")
            sizes.append(size)
        
        # Get non-overlapping slot positions along the wall
        along_positions = non_overlapping_slots(room_w, room_h, wall, sizes)
        
        # Place each object at its slot position
        for o, along in zip(objs, along_positions):
            if o["shape"] == "circle":
                obj_w = obj_h = o["r"] * 2
                x, y = wall_center_xy(wall, room_w, room_h, obj_w, obj_h, along)
            else:
                obj_w = o["w"]
                obj_h = o["h"]
                x, y = wall_center_xy(wall, room_w, room_h, obj_w, obj_h, along)
            
            # Validate bounds (should always pass, but verify)
            if not validate_bounds(x, y, obj_w, obj_h, room_w, room_h):
                # Skip if somehow out of bounds (shouldn't happen with proper calculation)
                continue
            
            # Check for overlaps with existing placements (shouldn't happen for same wall, but check anyway)
            has_overlap = False
            for existing_o, ex_x, ex_y in placements:
                ex_w = existing_o.get("w", existing_o.get("r", 0) * 2)
                ex_h = existing_o.get("h", existing_o.get("r", 0) * 2)
                if check_overlap(x, y, obj_w, obj_h, ex_x, ex_y, ex_w, ex_h):
                    has_overlap = True
                    break
            
            if not has_overlap:
                placements.append((o, x, y))
    
    # Handle free placement objects (center/none) - place them avoiding overlaps
    for o in center_objs:
        obj_w = o.get("w", o.get("r", 0) * 2)
        obj_h = o.get("h", o.get("r", 0) * 2)
        
        # Try center first
        x, y = 0.0, 0.0
        if validate_bounds(x, y, obj_w, obj_h, room_w, room_h):
            # Check overlap
            has_overlap = False
            for existing_o, ex_x, ex_y in placements:
                ex_w = existing_o.get("w", existing_o.get("r", 0) * 2)
                ex_h = existing_o.get("h", existing_o.get("r", 0) * 2)
                if check_overlap(x, y, obj_w, obj_h, ex_x, ex_y, ex_w, ex_h):
                    has_overlap = True
                    break
            
            if not has_overlap:
                placements.append((o, x, y))
                continue
        
        # If center doesn't work, try offset positions
        placed = False
        for offset_x in [0, obj_w, -obj_w, obj_w*1.5, -obj_w*1.5]:
            for offset_y in [0, obj_h, -obj_h, obj_h*1.5, -obj_h*1.5]:
                x, y = offset_x, offset_y
                if not validate_bounds(x, y, obj_w, obj_h, room_w, room_h):
                    continue
                
                has_overlap = False
                for existing_o, ex_x, ex_y in placements:
                    ex_w = existing_o.get("w", existing_o.get("r", 0) * 2)
                    ex_h = existing_o.get("h", existing_o.get("r", 0) * 2)
                    if check_overlap(x, y, obj_w, obj_h, ex_x, ex_y, ex_w, ex_h):
                        has_overlap = True
                        break
                
                if not has_overlap:
                    placements.append((o, x, y))
                    placed = True
                    break
            
            if placed:
                break

    # Build new coordinate-enriched output (DSL-like)
    enriched = []
    enriched.append("UNITS: mm")
    enriched.append("ORIGIN_POLICY: room_center_at_(0,0)")
    enriched.append(f"ROOM: rect w={room_w} h={room_h} center=(0,0)")
    enriched.append("WALLS: rect_perimeter closed=true layer=WALLS")

    for o, x, y in placements:
        if o["shape"] == "circle":
            enriched.append(
                f"{o['name']}: circle r={o['r']} center=({x:.0f},{y:.0f}) "
                f"layer=OBJECTS closed=true anchor_wall={o.get('wall', 'none')}"
            )
        else:
            enriched.append(
                f"{o['name']}: rect w={o['w']} h={o['h']} center=({x:.0f},{y:.0f}) "
                f"layer=OBJECTS closed=true anchor_wall={o.get('wall', 'none')}"
            )

    return {"instruction": instr, "output": "\n".join(enriched)}


def main(inp: str, outp: str, max_rows: Optional[int] = None, seed: int = 42):
    """Main function to process the dataset."""
    random.seed(seed)
    kept = 0
    total = 0
    
    with open(inp, "r", encoding="utf-8") as fin, open(outp, "w", encoding="utf-8") as fout:
        for line in fin:
            total += 1
            rec = json.loads(line)
            aug = augment_record(rec)
            if aug is None:
                continue
            fout.write(json.dumps(aug, ensure_ascii=False) + "\n")
            kept += 1
            if max_rows and kept >= max_rows:
                break
    
    print(f"✅ Done. total={total}, kept={kept} ({kept/total*100:.1f}%)")
    print(f"   Output: {outp}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Augment enhanced dataset with explicit coordinates"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input JSONL file (enhanced dataset)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSONL file (coordinate-enriched)"
    )
    parser.add_argument(
        "--max_rows",
        type=int,
        default=None,
        help="Maximum number of rows to process (for testing)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    args = parser.parse_args()
    main(args.input, args.output, args.max_rows, args.seed)

