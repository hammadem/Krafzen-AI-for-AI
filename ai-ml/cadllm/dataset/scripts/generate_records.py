#!/usr/bin/env python3
"""
Generate new non-overlapping CAD records using room templates.

This script generates new records with proper coordinate placement, ensuring
no overlaps and no out-of-bounds objects. Uses templates for kitchen, bathroom,
bedroom, and living room types.

Usage:
    python generate_records.py \
        --output ../jsonl/new_records.jsonl \
        --target_count 10000 \
        --seed 42
"""

import json
import re
import random
import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import argparse

# Import functions from augment_with_coordinates.py
# Constants
WALL_THICKNESS = 100  # mm
DEFAULT_SETBACK = 50  # mm from inner face of wall
MIN_GAP = 50  # mm between adjacent objects along a wall

# Standard object dimensions (in mm)
OBJECT_DIMS = {
    # Kitchen
    "SINK": {"w": 600, "h": 500, "layer": "FIXTURES"},
    "COOKTOP": {"w": 700, "h": 600, "layer": "APPLIANCES"},
    "STOVE": {"w": 700, "h": 600, "layer": "APPLIANCES"},
    "FRIDGE": {"w": 900, "h": 700, "layer": "APPLIANCES"},
    "REFRIGERATOR": {"w": 900, "h": 700, "layer": "APPLIANCES"},
    "DINING_TABLE": {"w": 1500, "h": 800, "layer": "FURNITURE"},
    "ISLAND": {"w": 1500, "h": 1000, "layer": "FURNITURE"},
    "CENTER_TABLE": {"w": 1200, "h": 800, "layer": "FURNITURE"},
    
    # Bathroom
    "TOILET": {"w": 400, "h": 700, "layer": "FIXTURES"},
    "BATH_SINK": {"w": 600, "h": 500, "layer": "FIXTURES"},
    "BATHTUB": {"w": 1700, "h": 800, "layer": "FIXTURES"},
    "SHOWER": {"w": 900, "h": 900, "layer": "FIXTURES"},
    "MIRROR": {"w": 800, "h": 600, "layer": "FIXTURES"},
    
    # Bedroom
    "BED": {"w": 1500, "h": 2000, "layer": "FURNITURE"},
    "DESK": {"w": 1200, "h": 600, "layer": "FURNITURE"},
    "WARDROBE": {"w": 1800, "h": 600, "layer": "FURNITURE"},
    "NIGHTSTAND": {"w": 500, "h": 500, "layer": "FURNITURE"},
    "DRESSER": {"w": 1200, "h": 600, "layer": "FURNITURE"},
    
    # Living room
    "SOFA": {"w": 2000, "h": 900, "layer": "FURNITURE"},
    "TV_STAND": {"w": 1500, "h": 400, "layer": "FURNITURE"},
    "COFFEE_TABLE": {"w": 1200, "h": 600, "layer": "FURNITURE"},
    "CHAIR": {"w": 600, "h": 600, "layer": "FURNITURE"},
    "LAMP": {"w": 300, "h": 300, "layer": "FURNITURE", "shape": "circle", "r": 150},
    
    # Common
    "WINDOW": {"w": 1200, "h": 150, "layer": "OPENINGS"},
    "DOOR": {"w": 900, "h": 2000, "layer": "OPENINGS"},
}

# Room type templates
ROOM_TEMPLATES = {
    "kitchen": {
        "dims_range": [(3500, 5000), (2800, 4000)],
        "objects": [
            ("SINK", "north"),
            ("COOKTOP", "west"),
            ("FRIDGE", "east"),
            ("DINING_TABLE", "none"),
        ],
        "optional": [
            ("ISLAND", "none"),
            ("CENTER_TABLE", "none"),
        ],
    },
    "bathroom": {
        "dims_range": [(2000, 3000), (1800, 2800)],
        "objects": [
            ("TOILET", "west"),
            ("BATH_SINK", "north"),
            ("SHOWER", "east"),
        ],
        "optional": [
            ("BATHTUB", "south"),
            ("MIRROR", "north"),
        ],
    },
    "bedroom": {
        "dims_range": [(3000, 4500), (3000, 4000)],
        "objects": [
            ("BED", "south"),
            ("DESK", "north"),
            ("WARDROBE", "east"),
        ],
        "optional": [
            ("NIGHTSTAND", "south"),
            ("DRESSER", "north"),
            ("WINDOW", "north"),
        ],
    },
    "living_room": {
        "dims_range": [(4000, 6000), (3500, 5000)],
        "objects": [
            ("SOFA", "south"),
            ("TV_STAND", "north"),
            ("COFFEE_TABLE", "none"),
        ],
        "optional": [
            ("CHAIR", "none"),
            ("LAMP", "none"),
            ("WINDOW", "north"),
        ],
    },
}


def wall_center_xy(wall: str, room_w: int, room_h: int, obj_w: int, obj_h: int, along: float) -> Tuple[float, float]:
    """Calculate center coordinates for an object placed on a wall."""
    room_half_w = room_w / 2
    room_half_h = room_h / 2
    
    if wall == "north":
        max_along_x = room_half_w - obj_w / 2
        x = max(-max_along_x, min(along, max_along_x))
        y = room_half_h - (WALL_THICKNESS + DEFAULT_SETBACK + obj_h / 2)
        y = min(y, room_half_h - obj_h / 2)
    elif wall == "south":
        max_along_x = room_half_w - obj_w / 2
        x = max(-max_along_x, min(along, max_along_x))
        y = -room_half_h + (WALL_THICKNESS + DEFAULT_SETBACK + obj_h / 2)
        y = max(y, -room_half_h + obj_h / 2)
    elif wall == "east":
        max_along_y = room_half_h - obj_h / 2
        y = max(-max_along_y, min(along, max_along_y))
        x = room_half_w - (WALL_THICKNESS + DEFAULT_SETBACK + obj_w / 2)
        x = min(x, room_half_w - obj_w / 2)
    elif wall == "west":
        max_along_y = room_half_h - obj_h / 2
        y = max(-max_along_y, min(along, max_along_y))
        x = -room_half_w + (WALL_THICKNESS + DEFAULT_SETBACK + obj_w / 2)
        x = max(x, -room_half_w + obj_w / 2)
    else:  # "none" or "center"
        max_x = room_half_w - obj_w / 2
        max_y = room_half_h - obj_h / 2
        x = max(-max_x, min(along if abs(along) < max_x else 0.0, max_x))
        y = max(-max_y, min(0.0, max_y))
    return x, y


def validate_bounds(x: float, y: float, obj_w: float, obj_h: float, room_w: int, room_h: int) -> bool:
    """Check if object is within room bounds."""
    room_half_w = room_w / 2
    room_half_h = room_h / 2
    
    half_w = obj_w / 2
    half_h = obj_h / 2
    
    return (x - half_w >= -room_half_w and 
            x + half_w <= room_half_w and
            y - half_h >= -room_half_h and 
            y + half_h <= room_half_h)


def check_overlap(x1: float, y1: float, w1: float, h1: float,
                  x2: float, y2: float, w2: float, h2: float,
                  min_gap: float = 10.0) -> bool:
    """Check if two objects overlap (with optional minimum gap)."""
    w1_exp = w1 + min_gap
    h1_exp = h1 + min_gap
    w2_exp = w2 + min_gap
    h2_exp = h2 + min_gap
    
    return not (x1 + w1_exp/2 < x2 - w2_exp/2 or
                x1 - w1_exp/2 > x2 + w2_exp/2 or
                y1 + h1_exp/2 < y2 - h2_exp/2 or
                y1 - h1_exp/2 > y2 + h2_exp/2)


def non_overlapping_slots(room_w: int, room_h: int, wall: str, widths_or_heights: List[int]) -> List[float]:
    """Assign positions along a wall without overlap."""
    if not widths_or_heights:
        return []
    
    sizes = widths_or_heights
    
    if wall in ("north", "south"):
        effective_span = room_w - 2 * (WALL_THICKNESS + DEFAULT_SETBACK)
    else:
        effective_span = room_h - 2 * (WALL_THICKNESS + DEFAULT_SETBACK)

    effective_span = max(0, effective_span)
    total_needed_space = sum(sizes) + MIN_GAP * (len(sizes) - 1)
    
    if total_needed_space > effective_span:
        gap = max(10, (effective_span - sum(sizes)) / max(1, (len(sizes) - 1)))
        if gap < 10:
            return []
    else:
        gap = MIN_GAP

    start_position = -effective_span / 2 + (sizes[0] / 2)
    slots = []
    current_position = start_position
    for i, s in enumerate(sizes):
        center = current_position
        slots.append(center)
        if i < len(sizes) - 1:
            current_position += (s / 2) + gap + (sizes[i+1] / 2)
    
    return slots


def add_burners_to_stove(stove_x: float, stove_y: float, stove_w: float, stove_h: float, room_w: int, room_h: int) -> List[Dict]:
    """Add burner circles to a stove object."""
    burners = []
    burner_radius = min(stove_w, stove_h) * 0.12
    spacing_x = stove_w / 3
    spacing_y = stove_h / 3
    
    room_half_w = room_w / 2
    room_half_h = room_h / 2
    
    burner_positions = [
        (stove_x - spacing_x/2, stove_y - spacing_y/2),
        (stove_x + spacing_x/2, stove_y - spacing_y/2),
        (stove_x - spacing_x/2, stove_y + spacing_y/2),
        (stove_x + spacing_x/2, stove_y + spacing_y/2),
    ]
    
    for i, (bx, by) in enumerate(burner_positions, 1):
        bx = max(-room_half_w + burner_radius, min(bx, room_half_w - burner_radius))
        by = max(-room_half_h + burner_radius, min(by, room_half_h - burner_radius))
        
        if len(burner_positions) == 1:
            burner_name = "BURNER"
        else:
            burner_name = f"BURNER {i}"
        
        burners.append({
            "name": burner_name,
            "shape": "circle",
            "r": burner_radius,
            "x": bx,
            "y": by,
            "layer": "APPLIANCES",
            "anchor_wall": "none",
            "subfeature_of": "COOKTOP"
        })
    
    return burners


def generate_record(room_type: str, seed: Optional[int] = None) -> Optional[Dict]:
    """Generate a single record with non-overlapping objects."""
    if seed is not None:
        random.seed(seed)
    
    template = ROOM_TEMPLATES[room_type]
    
    # Pick room dimensions
    w_range, h_range = template["dims_range"]
    room_w = random.randint(w_range[0], w_range[1])
    room_h = random.randint(h_range[0], h_range[1])
    
    # Select objects
    required_objs = list(template["objects"])
    optional_objs = template.get("optional", [])
    
    # Add 0-2 optional objects randomly
    num_optional = random.randint(0, min(2, len(optional_objs)))
    selected_optional = random.sample(optional_objs, num_optional)
    all_objs = required_objs + selected_optional
    
    # Group objects by wall
    by_wall = defaultdict(list)
    center_objs = []
    
    for obj_name, wall in all_objs:
        obj_info = OBJECT_DIMS.get(obj_name, {"w": 500, "h": 500, "layer": "FURNITURE"})
        obj_info["name"] = obj_name
        obj_info["wall"] = wall
        if wall == "none":
            center_objs.append(obj_info)
        else:
            by_wall[wall].append(obj_info)
    
    placements = []
    
    # Place wall-anchored objects
    for wall, objs in by_wall.items():
        if not objs:
            continue
        
        sizes = []
        for o in objs:
            if o.get("shape") == "circle":
                size = o["r"] * 2
            else:
                size = o["w"] if wall in ("north", "south") else o["h"]
            sizes.append(size)
        
        along_positions = non_overlapping_slots(room_w, room_h, wall, sizes)
        
        if len(along_positions) != len(objs):
            return None  # Objects don't fit on wall
        
        for o, along in zip(objs, along_positions):
            if o.get("shape") == "circle":
                obj_w = obj_h = o["r"] * 2
            else:
                obj_w = o["w"]
                obj_h = o["h"]
            
            x, y = wall_center_xy(wall, room_w, room_h, obj_w, obj_h, along)
            
            if not validate_bounds(x, y, obj_w, obj_h, room_w, room_h):
                return None
            
            # Check for overlaps
            has_overlap = False
            for existing_o, ex_x, ex_y in placements:
                ex_w = existing_o.get("w", existing_o.get("r", 0) * 2)
                ex_h = existing_o.get("h", existing_o.get("r", 0) * 2)
                
                if existing_o.get("subfeature_of") and o.get("name") == existing_o.get("subfeature_of"):
                    continue
                
                if check_overlap(x, y, obj_w, obj_h, ex_x, ex_y, ex_w, ex_h):
                    has_overlap = True
                    break
            
            if not has_overlap:
                placements.append((o, x, y))
                
                # Add burners for cooktop/stove
                if o["name"] in ("COOKTOP", "STOVE"):
                    burners = add_burners_to_stove(x, y, obj_w, obj_h, room_w, room_h)
                    for burner in burners:
                        placements.append((burner, burner["x"], burner["y"]))
    
    # Place center objects
    for o in center_objs:
        if o.get("shape") == "circle":
            obj_w = obj_h = o["r"] * 2
        else:
            obj_w = o["w"]
            obj_h = o["h"]
        
        # Try center first
        x, y = 0.0, 0.0
        if validate_bounds(x, y, obj_w, obj_h, room_w, room_h):
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
        
        # Try offset positions
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
        
        if not placed:
            return None  # Couldn't place center object
    
    # Build output DSL
    output_lines = [
        "UNITS: mm",
        "ORIGIN_POLICY: room_center_at_(0,0)",
        f"ROOM: rect w={room_w} h={room_h} center=(0,0)",
        "WALLS: rect_perimeter closed=true layer=WALLS",
    ]
    
    # Generate instruction
    obj_names = [o["name"] for o, _, _ in placements if not o.get("subfeature_of")]
    instruction = f"Draw a {room_type} with {', '.join(obj_names[:5])}."
    
    # Add object definitions
    for o, x, y in placements:
        if o.get("subfeature_of"):
            subfeature_attr = f" subfeature_of={o['subfeature_of']}"
        else:
            subfeature_attr = ""
        
        anchor_wall = o.get("anchor_wall", o.get("wall", "none"))
        
        if o.get("shape") == "circle":
            output_lines.append(
                f"{o['name']}: circle r={o['r']:.0f} center=({x:.0f},{y:.0f}) "
                f"layer={o['layer']} closed=true anchor_wall={anchor_wall}{subfeature_attr}"
            )
        else:
            output_lines.append(
                f"{o['name']}: rect w={o['w']} h={o['h']} center=({x:.0f},{y:.0f}) "
                f"layer={o['layer']} closed=true anchor_wall={anchor_wall}{subfeature_attr}"
            )
    
    return {
        "instruction": instruction,
        "input": "(none)",
        "output": "\n".join(output_lines)
    }


def main(output_path: str, target_count: int = 60000, seed: int = 42):
    """Generate top-up records."""
    random.seed(seed)
    
    room_types = ["kitchen", "bathroom", "bedroom", "living_room"]
    room_weights = [0.25, 0.25, 0.25, 0.25]  # Equal distribution
    
    generated = 0
    attempts = 0
    max_attempts = target_count * 3  # Safety limit
    
    print(f"🎲 Generating {target_count:,} non-overlapping records...")
    print(f"   Room distribution: {dict(zip(room_types, room_weights))}")
    print()
    
    with open(output_path, "w", encoding="utf-8") as fout:
        while generated < target_count and attempts < max_attempts:
            attempts += 1
            
            # Select room type
            room_type = random.choices(room_types, weights=room_weights)[0]
            
            # Generate record
            rec = generate_record(room_type, seed=None)
            
            if rec is None:
                continue  # Skip invalid records
            
            # Write record
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            generated += 1
            
            if generated % 1000 == 0:
                print(f"   Generated: {generated:,} / {target_count:,} ({generated/attempts*100:.1f}% success rate)")
    
    print()
    print(f"✅ Generation complete!")
    print(f"   Generated: {generated:,} records")
    print(f"   Attempts: {attempts:,}")
    print(f"   Success rate: {generated/attempts*100:.2f}%")
    print(f"   Output: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate additional non-overlapping records"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSONL file"
    )
    parser.add_argument(
        "--target_count",
        type=int,
        default=60000,
        help="Target number of records to generate"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    args = parser.parse_args()
    main(args.output, args.target_count, args.seed)

