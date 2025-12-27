#!/usr/bin/env python3
"""
Filter dataset to remove invalid geometry (OOB and overlaps).

Usage:
    python filter_clean_dataset.py \
        --input ../jsonl/cadllm_synth_with_coords_200k.jsonl \
        --output ../jsonl/cadllm_synth_with_coords_200k_clean.jsonl \
        --filter_oob \
        --filter_overlaps \
        --exclude_subfeatures
"""

import json
import re
from typing import Dict, List, Optional, Set, Tuple
import argparse

# Regex patterns
ROOM_RE = re.compile(r'ROOM:\s*rect\s+w=(\d+)\s+h=(\d+)\s+center=\(([-\d.]+),([-\d.]+)\)')
OBJECT_RE = re.compile(r'^([A-Z_]+):\s*(rect|circle)\s+(?:w=(\d+)\s+h=(\d+)|r=(\d+))\s+center=\(([-\d.]+),([-\d.]+)\)')
SUBFEATURE_RE = re.compile(r'subfeature_of=([A-Z_]+)')


def parse_room(output: str) -> Optional[Tuple[int, int, float, float]]:
    """Parse room dimensions and center from DSL output."""
    for line in output.splitlines():
        match = ROOM_RE.search(line)
        if match:
            w = int(match.group(1))
            h = int(match.group(2))
            cx = float(match.group(3))
            cy = float(match.group(4))
            return (w, h, cx, cy)
    return None


def parse_objects(output: str) -> List[Dict]:
    """Parse all objects from DSL output."""
    objects = []
    for line in output.splitlines():
        match = OBJECT_RE.match(line)
        if not match:
            continue
        
        name = match.group(1)
        shape = match.group(2)
        
        if shape == "rect":
            w = int(match.group(3))
            h = int(match.group(4))
            r = None
        else:  # circle
            w = h = None
            r = int(match.group(5))
        
        x = float(match.group(6))
        y = float(match.group(7))
        
        # Check for subfeature
        subfeature_match = SUBFEATURE_RE.search(line)
        subfeature_of = subfeature_match.group(1) if subfeature_match else None
        
        objects.append({
            "name": name,
            "shape": shape,
            "w": w,
            "h": h,
            "r": r,
            "x": x,
            "y": y,
            "subfeature_of": subfeature_of
        })
    
    return objects


def check_bounds(obj: Dict, room_w: int, room_h: int) -> bool:
    """Check if object is within room bounds."""
    x, y = obj["x"], obj["y"]
    room_half_w = room_w / 2
    room_half_h = room_h / 2
    
    if obj["shape"] == "circle":
        r = obj["r"]
        return (abs(x) + r <= room_half_w and 
                abs(y) + r <= room_half_h)
    else:
        w, h = obj["w"], obj["h"]
        half_w = w / 2
        half_h = h / 2
        return (x - half_w >= -room_half_w and 
                x + half_w <= room_half_w and
                y - half_h >= -room_half_h and
                y + half_h <= room_half_h)


def check_overlap(obj1: Dict, obj2: Dict, min_gap: float = 10.0) -> bool:
    """Check if two objects overlap (with optional minimum gap)."""
    # Get bounding boxes
    if obj1["shape"] == "circle":
        w1 = h1 = obj1["r"] * 2
    else:
        w1, h1 = obj1["w"], obj1["h"]
    
    if obj2["shape"] == "circle":
        w2 = h2 = obj2["r"] * 2
    else:
        w2, h2 = obj2["w"], obj2["h"]
    
    x1, y1 = obj1["x"], obj1["y"]
    x2, y2 = obj2["x"], obj2["y"]
    
    # Expand by min_gap
    w1_exp = w1 + min_gap
    h1_exp = h1 + min_gap
    w2_exp = w2 + min_gap
    h2_exp = h2 + min_gap
    
    # Check axis-aligned bounding box overlap
    return not (x1 + w1_exp/2 < x2 - w2_exp/2 or
                x1 - w1_exp/2 > x2 + w2_exp/2 or
                y1 + h1_exp/2 < y2 - h2_exp/2 or
                y1 - h1_exp/2 > y2 + h2_exp/2)


def validate_record(rec: Dict, filter_oob: bool, filter_overlaps: bool, exclude_subfeatures: bool) -> Tuple[bool, str]:
    """
    Validate a record.
    Returns (is_valid, reason) where reason is empty if valid.
    """
    output = rec.get("output", "").strip()
    
    # Parse room
    room_info = parse_room(output)
    if not room_info:
        return False, "no_room"
    
    room_w, room_h, _, _ = room_info
    
    # Parse objects
    objects = parse_objects(output)
    if not objects:
        return False, "no_objects"
    
    # Check bounds
    if filter_oob:
        for obj in objects:
            if not check_bounds(obj, room_w, room_h):
                return False, "oob"
    
    # Check overlaps
    if filter_overlaps:
        for i, obj1 in enumerate(objects):
            for obj2 in objects[i+1:]:
                # Skip if either is a subfeature and we're excluding them
                if exclude_subfeatures:
                    if obj1.get("subfeature_of") or obj2.get("subfeature_of"):
                        continue
                
                if check_overlap(obj1, obj2):
                    return False, "overlap"
    
    return True, ""


def main(inp: str, outp: str, filter_oob: bool = True, filter_overlaps: bool = False, exclude_subfeatures: bool = True, seed: int = 42):
    """Main function to filter dataset."""
    import random
    random.seed(seed)
    
    kept = 0
    filtered_oob = 0
    filtered_overlap = 0
    filtered_no_room = 0
    filtered_no_objects = 0
    total = 0
    
    print("🔍 Filtering dataset...")
    print(f"   Filter OOB: {filter_oob}")
    print(f"   Filter overlaps: {filter_overlaps}")
    print(f"   Exclude subfeatures from overlap check: {exclude_subfeatures}")
    print()
    
    with open(inp, "r", encoding="utf-8") as fin, open(outp, "w", encoding="utf-8") as fout:
        for line in fin:
            total += 1
            rec = json.loads(line)
            
            is_valid, reason = validate_record(rec, filter_oob, filter_overlaps, exclude_subfeatures)
            
            if not is_valid:
                if reason == "oob":
                    filtered_oob += 1
                elif reason == "overlap":
                    filtered_overlap += 1
                elif reason == "no_room":
                    filtered_no_room += 1
                elif reason == "no_objects":
                    filtered_no_objects += 1
                continue
            
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            kept += 1
    
    print(f"✅ Filtering complete!")
    print(f"   Total records: {total:,}")
    print(f"   Kept: {kept:,} ({kept/total*100:.2f}%)")
    print(f"   Filtered:")
    print(f"     - OOB: {filtered_oob:,}")
    print(f"     - Overlaps: {filtered_overlap:,}")
    print(f"     - No room: {filtered_no_room:,}")
    print(f"     - No objects: {filtered_no_objects:,}")
    print(f"   Output: {outp}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter dataset to remove invalid geometry"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input JSONL file"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSONL file"
    )
    parser.add_argument(
        "--filter_oob",
        action="store_true",
        help="Filter out-of-bounds objects"
    )
    parser.add_argument(
        "--filter_overlaps",
        action="store_true",
        help="Filter overlapping objects"
    )
    parser.add_argument(
        "--exclude_subfeatures",
        action="store_true",
        default=True,
        help="Exclude subfeatures (like burners) from overlap check"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    args = parser.parse_args()
    main(args.input, args.output, args.filter_oob, args.filter_overlaps, args.exclude_subfeatures, args.seed)

