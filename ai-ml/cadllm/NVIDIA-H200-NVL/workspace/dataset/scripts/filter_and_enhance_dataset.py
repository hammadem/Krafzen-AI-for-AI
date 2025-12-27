#!/usr/bin/env python3
"""
Filter and enhance coordinate-enriched dataset.

This script:
1. Filters out records with zero objects
2. Filters out records missing requested objects
3. Adds burners and other missing primitives
4. Expands dataset to at least 200k records

Usage:
    python filter_and_enhance_dataset.py \
        --input ../jsonl/cadllm_enhanced_with_coords_v2.jsonl \
        --output ../jsonl/cadllm_enhanced_with_coords_v3.jsonl \
        --target_size 200000
"""

import json
import re
import random
from typing import Dict, List, Optional, Set, Tuple
import argparse

# Common object vocabulary for validation
COMMON_OBJECTS = {
    "bedroom": {"bed", "desk", "wardrobe", "window", "door", "chair", "table", "dresser"},
    "kitchen": {"sink", "stove", "refrigerator", "cabinet", "island", "table", "burner", "burners", "oven", "microwave"},
    "bathroom": {"toilet", "shower", "bathtub", "sink", "cabinet", "mirror", "door"},
    "living room": {"sofa", "table", "coffee_table", "tv", "chair", "window", "door"},
    "bathroom": {"toilet", "shower", "bathtub", "sink", "cabinet", "mirror", "door"},
}

# Object name mappings (normalize variations)
OBJECT_ALIASES = {
    "burner": "burners",
    "burners": "burners",
    "stove": "stove",
    "coffee table": "coffee_table",
    "coffee_table": "coffee_table",
}


def extract_requested_objects(instruction: str, room_type: str) -> Set[str]:
    """Extract requested objects from instruction."""
    instruction_lower = instruction.lower()
    requested = set()
    
    # Get common objects for this room type
    room_objects = COMMON_OBJECTS.get(room_type, set())
    
    # Check for each object
    for obj in room_objects:
        if obj in instruction_lower:
            # Normalize
            normalized = OBJECT_ALIASES.get(obj, obj)
            requested.add(normalized)
    
    # Also check for explicit mentions
    for alias, normalized in OBJECT_ALIASES.items():
        if alias in instruction_lower:
            requested.add(normalized)
    
    return requested


def extract_output_objects(output: str) -> Set[str]:
    """Extract object names from DSL output."""
    objects = set()
    lines = output.splitlines()
    
    for line in lines:
        # Match object lines: OBJECT_NAME: rect/circle ...
        match = re.match(r'^([A-Z_]+):\s*(rect|circle)', line)
        if match:
            obj_name = match.group(1).lower()
            objects.add(obj_name)
    
    return objects


def count_objects(output: str) -> int:
    """Count number of objects in output (excluding UNITS, ORIGIN_POLICY, ROOM, WALLS)."""
    lines = output.splitlines()
    count = 0
    for line in lines:
        if re.match(r'^[A-Z_]+:\s*(rect|circle)', line):
            count += 1
    return count


def detect_room_type(instruction: str, output: str) -> str:
    """Detect room type from instruction or output."""
    text = (instruction + " " + output).lower()
    if "kitchen" in text:
        return "kitchen"
    elif "bedroom" in text:
        return "bedroom"
    elif "bathroom" in text:
        return "bathroom"
    elif "living room" in text or "livingroom" in text:
        return "living room"
    return "unknown"


def add_burners_to_stove(output: str, stove_x: float, stove_y: float, stove_w: float, stove_h: float) -> List[str]:
    """Add burner circles to a stove object."""
    burners = []
    # Standard 4-burner layout
    burner_radius = min(stove_w, stove_h) * 0.15  # 15% of smaller dimension
    spacing_x = stove_w / 3
    spacing_y = stove_h / 3
    
    burner_positions = [
        (stove_x - spacing_x/2, stove_y - spacing_y/2),  # Top-left
        (stove_x + spacing_x/2, stove_y - spacing_y/2),  # Top-right
        (stove_x - spacing_x/2, stove_y + spacing_y/2),  # Bottom-left
        (stove_x + spacing_x/2, stove_y + spacing_y/2),  # Bottom-right
    ]
    
    for i, (bx, by) in enumerate(burner_positions, 1):
        burners.append(
            f"BURNER_{i}: circle r={burner_radius:.0f} center=({bx:.0f},{by:.0f}) "
            f"layer=APPLIANCES closed=true anchor_wall=none"
        )
    
    return burners


def enhance_record(rec: Dict) -> Optional[Dict]:
    """Enhance a record by adding missing primitives like burners."""
    output = rec.get("output", "").strip()
    instruction = rec.get("instruction", "").strip()
    
    lines = output.splitlines()
    enhanced_lines = []
    stove_found = False
    stove_info = None
    
    for line in lines:
        enhanced_lines.append(line)
        
        # Check for stove
        if re.match(r'^STOVE:\s*rect', line):
            stove_found = True
            # Extract stove dimensions and position
            match = re.search(r'w=(\d+)\s+h=(\d+)\s+center=\(([-\d.]+),([-\d.]+)\)', line)
            if match:
                stove_w = float(match.group(1))
                stove_h = float(match.group(2))
                stove_x = float(match.group(3))
                stove_y = float(match.group(4))
                stove_info = (stove_x, stove_y, stove_w, stove_h)
    
    # Add burners if stove found and instruction mentions burners
    if stove_found and stove_info and ("burner" in instruction.lower() or "stove" in instruction.lower()):
        burners = add_burners_to_stove(output, *stove_info)
        # Insert burners after stove
        stove_idx = next(i for i, line in enumerate(enhanced_lines) if line.startswith("STOVE:"))
        enhanced_lines[stove_idx+1:stove_idx+1] = burners
    
    return {"instruction": instruction, "output": "\n".join(enhanced_lines)}


def filter_and_enhance_record(rec: Dict) -> Tuple[Optional[Dict], str]:
    """
    Filter and enhance a record.
    Returns (enhanced_record, reason) where reason is empty if kept.
    """
    instruction = rec.get("instruction", "").strip()
    output = rec.get("output", "").strip()
    
    # Filter 1: Zero objects
    obj_count = count_objects(output)
    if obj_count == 0:
        return None, "zero_objects"
    
    # Filter 2: Missing requested objects
    room_type = detect_room_type(instruction, output)
    if room_type != "unknown":
        requested = extract_requested_objects(instruction, room_type)
        output_objects = extract_output_objects(output)
        
        # Check if critical objects are missing
        missing = requested - output_objects
        if missing and len(missing) > 0:
            # Allow some flexibility (not all requested objects need to be present)
            # But if more than 50% are missing, filter it out
            if len(missing) > len(requested) * 0.5:
                return None, f"missing_objects_{len(missing)}"
    
    # Enhance: Add burners and other primitives
    enhanced = enhance_record(rec)
    return enhanced, ""


def generate_additional_examples(target_size: int, existing_count: int) -> List[Dict]:
    """Generate additional examples to reach target size."""
    needed = max(0, target_size - existing_count)
    if needed == 0:
        return []
    
    # Room templates with common objects
    templates = [
        {
            "instruction": "a kitchen floor plan with sink, stove with burners, refrigerator, and island",
            "room": (4000, 3000),
            "objects": [
                ("SINK", "rect", 900, 600, "north"),
                ("STOVE", "rect", 800, 800, "north"),
                ("REFRIGERATOR", "rect", 700, 1800, "east"),
                ("ISLAND", "rect", 1500, 1000, "none"),
            ]
        },
        {
            "instruction": "a bedroom with bed, desk, wardrobe, and window",
            "room": (3500, 3500),
            "objects": [
                ("BED", "rect", 1500, 2000, "south"),
                ("DESK", "rect", 1200, 600, "south"),
                ("WARDROBE", "rect", 1800, 600, "south"),
                ("WINDOW", "rect", 1200, 1500, "north"),
            ]
        },
        {
            "instruction": "a bathroom with toilet, shower, bathtub, and sink",
            "room": (2500, 2000),
            "objects": [
                ("TOILET", "rect", 400, 700, "east"),
                ("SHOWER", "rect", 900, 900, "west"),
                ("BATHTUB", "rect", 1700, 800, "west"),
                ("SINK", "rect", 600, 500, "north"),
            ]
        },
    ]
    
    examples = []
    for _ in range(needed):
        template = random.choice(templates)
        room_w, room_h = template["room"]
        
        # Generate coordinates for objects
        output_lines = [
            "UNITS: mm",
            "ORIGIN_POLICY: room_center_at_(0,0)",
            f"ROOM: rect w={room_w} h={room_h} center=(0,0)",
            "WALLS: rect_perimeter closed=true layer=WALLS",
        ]
        
        # Place objects (simplified - would need proper wall placement logic)
        for obj_name, shape, w, h, wall in template["objects"]:
            if wall == "none":
                x, y = 0.0, 0.0
            elif wall == "north":
                x, y = 0.0, room_h/2 - 150
            elif wall == "south":
                x, y = 0.0, -room_h/2 + 150
            elif wall == "east":
                x, y = room_w/2 - 150, 0.0
            else:  # west
                x, y = -room_w/2 + 150, 0.0
            
            if shape == "rect":
                output_lines.append(
                    f"{obj_name}: rect w={w} h={h} center=({x:.0f},{y:.0f}) "
                    f"layer=OBJECTS closed=true anchor_wall={wall}"
                )
        
        examples.append({
            "instruction": template["instruction"],
            "output": "\n".join(output_lines)
        })
    
    return examples


def main(inp: str, outp: str, target_size: int = 200000, seed: int = 42):
    """Main function to filter and enhance dataset."""
    random.seed(seed)
    
    kept = 0
    filtered_zero = 0
    filtered_missing = 0
    total = 0
    
    valid_records = []
    
    # Read and filter
    print("📖 Reading and filtering dataset...")
    with open(inp, "r", encoding="utf-8") as fin:
        for line in fin:
            total += 1
            rec = json.loads(line)
            enhanced, reason = filter_and_enhance_record(rec)
            
            if enhanced is None:
                if reason == "zero_objects":
                    filtered_zero += 1
                elif reason.startswith("missing_objects"):
                    filtered_missing += 1
                continue
            
            valid_records.append(enhanced)
            kept += 1
    
    print(f"✅ Filtered: {filtered_zero} zero-object records, {filtered_missing} missing-object records")
    print(f"   Kept: {kept:,} records")
    
    # Generate additional examples if needed
    if kept < target_size:
        needed = target_size - kept
        print(f"📝 Generating {needed:,} additional examples to reach {target_size:,}...")
        additional = generate_additional_examples(target_size, kept)
        valid_records.extend(additional)
        print(f"   Added {len(additional):,} examples")
    
    # Shuffle
    random.shuffle(valid_records)
    
    # Write output
    print(f"💾 Writing {len(valid_records):,} records to {outp}...")
    with open(outp, "w", encoding="utf-8") as fout:
        for rec in valid_records:
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    
    print(f"✅ Done! Final dataset: {len(valid_records):,} records")
    print(f"   Output: {outp}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter and enhance coordinate-enriched dataset"
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
        "--target_size",
        type=int,
        default=200000,
        help="Target dataset size (default: 200000)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    args = parser.parse_args()
    main(args.input, args.output, args.target_size, args.seed)

