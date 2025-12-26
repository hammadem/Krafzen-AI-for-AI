#!/usr/bin/env python3
"""
Clean and normalize the CADLLM dataset.

This script processes the dataset to:
1. Normalize coordinates to origin (0, 0)
2. Close unclosed shapes
3. Remove multiple objects when not requested
4. Extract and apply correct dimensions from instructions
5. Generate a new cleaned dataset file

Usage:
    python clean_dataset.py --input dataset/jsonl/cadllm_2d.jsonl --output dataset/jsonl/cadllm_2d_cleaned.jsonl
"""

import json
import re
import argparse
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import sys

# Patterns for parsing
CIRCLE_PATTERN = re.compile(r'<Circle>:\s*x=([\d.]+),\s*y=([\d.]+),\s*r=([\d.]+)')
LINE_PATTERN = re.compile(r'<Line>:\s*x=([\d.]+),\s*y=([\d.]+)')
ARC_PATTERN = re.compile(r'<Arc>:\s*x=([\d.]+),\s*y=([\d.]+),\s*α=([\d.]+),\s*f=([\d.]+)')
SOL_PATTERN = re.compile(r'<SOL>')
EOS_PATTERN = re.compile(r'<EOS>')

# Dimension extraction patterns
DIMENSION_PATTERNS = [
    re.compile(r'(\d+(?:\.\d+)?)\s*mm', re.IGNORECASE),
    re.compile(r'(\d+(?:\.\d+)?)\s*cm', re.IGNORECASE),
    re.compile(r'radius\s*[=:]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    re.compile(r'r\s*[=:]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    re.compile(r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)', re.IGNORECASE),  # width x height
]


def extract_dimensions(instruction: str) -> Dict[str, float]:
    """
    Extract dimensions from instruction text.
    
    Returns:
        Dictionary with 'radius', 'width', 'height', 'scale' etc.
    """
    dimensions = {}
    instruction_lower = instruction.lower()
    
    # Extract radius
    radius_match = re.search(r'radius\s*[=:]?\s*(\d+(?:\.\d+)?)', instruction_lower)
    if not radius_match:
        radius_match = re.search(r'r\s*[=:]?\s*(\d+(?:\.\d+)?)', instruction_lower)
    if radius_match:
        dimensions['radius'] = float(radius_match.group(1))
    
    # Extract width x height
    size_match = re.search(r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)', instruction_lower)
    if size_match:
        dimensions['width'] = float(size_match.group(1))
        dimensions['height'] = float(size_match.group(2))
    
    # Extract single dimension values
    mm_values = re.findall(r'(\d+(?:\.\d+)?)\s*mm', instruction_lower)
    if mm_values:
        dimensions['values_mm'] = [float(v) for v in mm_values]
    
    return dimensions


def parse_output(output: str) -> List[Dict]:
    """
    Parse output into list of objects.
    Each object contains circles, lines, and arcs.
    """
    objects = []
    
    if not output or not output.strip():
        return objects
    
    # Split by <SOL> to get separate objects
    parts = re.split(r'<SOL>', output)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Remove <EOS> if present (some entries might not have it)
        part = re.sub(r'<EOS>', '', part).strip()
        if not part:
            continue
        
        obj = {
            'circles': [],
            'lines': [],
            'arcs': []
        }
        
        # Extract circles
        for match in CIRCLE_PATTERN.finditer(part):
            x, y, r = float(match.group(1)), float(match.group(2)), float(match.group(3))
            obj['circles'].append((x, y, r))
        
        # Extract lines
        for match in LINE_PATTERN.finditer(part):
            x, y = float(match.group(1)), float(match.group(2))
            obj['lines'].append((x, y))
        
        # Extract arcs
        for match in ARC_PATTERN.finditer(part):
            x, y, alpha, flag = float(match.group(1)), float(match.group(2)), float(match.group(3)), float(match.group(4))
            obj['arcs'].append((x, y, alpha, flag))
        
        if obj['circles'] or obj['lines'] or obj['arcs']:
            objects.append(obj)
    
    return objects


def normalize_coordinates(objects: List[Dict]) -> List[Dict]:
    """
    Normalize coordinates to center at origin (0, 0).
    Normalize each object separately to ensure proper centering.
    """
    if not objects:
        return objects
    
    normalized = []
    for obj in objects:
        # Collect coordinates for this object only
        all_coords = []
        
        for x, y, r in obj['circles']:
            all_coords.append((x - r, y - r))  # Bottom-left of circle
            all_coords.append((x + r, y + r))  # Top-right of circle
        
        for x, y in obj['lines']:
            all_coords.append((x, y))
        
        for x, y, _, _ in obj['arcs']:
            all_coords.append((x, y))
        
        if not all_coords:
            normalized.append(obj)
            continue
        
        # Calculate center for this object
        # Use centroid (average of all points) for better centering
        if obj['circles']:
            # For circles, use circle centers
            circle_centers = [(x, y) for x, y, r in obj['circles']]
            center_x = sum(c[0] for c in circle_centers) / len(circle_centers)
            center_y = sum(c[1] for c in circle_centers) / len(circle_centers)
        elif obj['lines']:
            # For lines, use centroid of all line points
            line_points = obj['lines']
            center_x = sum(p[0] for p in line_points) / len(line_points)
            center_y = sum(p[1] for p in line_points) / len(line_points)
        else:
            # Fallback to bounding box
            min_x = min(c[0] for c in all_coords)
            max_x = max(c[0] for c in all_coords)
            min_y = min(c[1] for c in all_coords)
            max_y = max(c[1] for c in all_coords)
            center_x = (min_x + max_x) / 2.0
            center_y = (min_y + max_y) / 2.0
        
        # Apply offset to center at origin
        new_obj = {
            'circles': [],
            'lines': [],
            'arcs': []
        }
        
        # Normalize circles
        for x, y, r in obj['circles']:
            new_obj['circles'].append((x - center_x, y - center_y, r))
        
        # Normalize lines
        for x, y in obj['lines']:
            new_obj['lines'].append((x - center_x, y - center_y))
        
        # Normalize arcs
        for x, y, alpha, flag in obj['arcs']:
            new_obj['arcs'].append((x - center_x, y - center_y, alpha, flag))
        
        normalized.append(new_obj)
    
    return normalized


def close_shape(lines: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Close an unclosed shape by adding the first point at the end if needed.
    """
    if len(lines) < 3:
        return lines
    
    # Check if already closed (first and last points are close)
    first = lines[0]
    last = lines[-1]
    
    # If points are within 1 unit, consider it closed
    if abs(first[0] - last[0]) < 1.0 and abs(first[1] - last[1]) < 1.0:
        return lines
    
    # Add first point to close the shape
    return lines + [first]


def scale_object(obj: Dict, scale_factor: float) -> Dict:
    """
    Scale an object by a factor.
    """
    scaled = {
        'circles': [],
        'lines': [],
        'arcs': []
    }
    
    # Scale circles (center and radius)
    for x, y, r in obj['circles']:
        scaled['circles'].append((x * scale_factor, y * scale_factor, r * scale_factor))
    
    # Scale lines
    for x, y in obj['lines']:
        scaled['lines'].append((x * scale_factor, y * scale_factor))
    
    # Scale arcs (center only, angle stays same)
    for x, y, alpha, flag in obj['arcs']:
        scaled['arcs'].append((x * scale_factor, y * scale_factor, alpha, flag))
    
    return scaled


def apply_dimensions(objects: List[Dict], instruction: str, dimensions: Dict) -> List[Dict]:
    """
    Apply correct dimensions from instruction to objects.
    This is complex - we'll try to match dimensions to the actual shape.
    """
    if not objects or not dimensions:
        return objects
    
    # For now, we'll calculate a scale factor based on the bounding box
    # and try to match it to requested dimensions
    # This is a simplified approach - could be improved
    
    # Calculate current bounding box
    all_coords = []
    for obj in objects:
        for x, y, r in obj['circles']:
            all_coords.append((x - r, y - r))
            all_coords.append((x + r, y + r))
        for x, y in obj['lines']:
            all_coords.append((x, y))
    
    if not all_coords:
        return objects
    
    current_width = max(c[0] for c in all_coords) - min(c[0] for c in all_coords)
    current_height = max(c[1] for c in all_coords) - min(c[1] for c in all_coords)
    
    # Determine target dimensions
    target_width = dimensions.get('width')
    target_height = dimensions.get('height')
    target_radius = dimensions.get('radius')
    
    scale_factor = 1.0
    
    # If we have width and height, scale to match
    if target_width and target_height and current_width > 0 and current_height > 0:
        scale_w = target_width / current_width
        scale_h = target_height / current_height
        scale_factor = (scale_w + scale_h) / 2.0  # Average
    # If we have radius and it's a circle, scale to match
    elif target_radius and len(objects) == 1 and objects[0]['circles'] and not objects[0]['lines']:
        if objects[0]['circles']:
            current_r = objects[0]['circles'][0][2]
            if current_r > 0:
                scale_factor = target_radius / current_r
    
    # Apply scaling if factor is reasonable (between 0.1 and 10)
    if 0.1 <= scale_factor <= 10.0:
        return [scale_object(obj, scale_factor) for obj in objects]
    
    return objects


def format_output(objects: List[Dict]) -> str:
    """
    Format objects back to the coordinate format string.
    """
    if not objects:
        return "<SOL>\n<EOS>"
    
    parts = []
    for obj in objects:
        lines = ["<SOL>"]
        
        # Add circles
        for x, y, r in obj['circles']:
            lines.append(f"<Circle>: x={x:.1f}, y={y:.1f}, r={r:.1f}")
        
        # Add lines (close shape if needed)
        lines_coords = obj['lines']
        if lines_coords:
            lines_coords = close_shape(lines_coords)
            for x, y in lines_coords:
                lines.append(f"<Line>: x={x:.1f}, y={y:.1f}")
        
        # Add arcs
        for x, y, alpha, flag in obj['arcs']:
            lines.append(f"<Arc>: x={x:.1f}, y={y:.1f}, α={alpha:.1f}, f={flag:.1f}")
        
        lines.append("<EOS>")
        parts.append("\n".join(lines))
    
    return "\n".join(parts)


def should_keep_multiple_objects(instruction: str, num_objects: int) -> bool:
    """
    Determine if multiple objects should be kept based on instruction.
    """
    instruction_lower = instruction.lower()
    
    # Keywords that suggest multiple objects
    multi_keywords = ['multiple', 'several', 'many', 'two', 'three', 'four', 'five', 'six', 'array', 'grid']
    
    # If instruction explicitly asks for multiple, keep them
    for keyword in multi_keywords:
        if keyword in instruction_lower:
            return True
    
    # Otherwise, keep only first object if multiple exist
    return False


def clean_entry(entry: Dict, stats: Dict) -> Optional[Dict]:
    """
    Clean a single dataset entry.
    
    Returns:
        Cleaned entry or None if entry should be skipped
    """
    instruction = entry.get('instruction', '').strip()
    input_text = entry.get('input', '').strip()
    output = entry.get('output', '').strip()
    
    if not output:
        stats['skipped_empty'] += 1
        return None
    
    # Parse output
    objects = parse_output(output)
    
    if not objects:
        stats['skipped_no_objects'] += 1
        return None
    
    # Check if multiple objects should be kept
    if len(objects) > 1:
        if should_keep_multiple_objects(instruction, len(objects)):
            stats['kept_multiple'] += 1
        else:
            # Keep only first object
            objects = [objects[0]]
            stats['removed_multiple'] += 1
    
    # Normalize coordinates to origin
    objects = normalize_coordinates(objects)
    stats['normalized'] += 1
    
    # Close unclosed shapes
    for obj in objects:
        if obj['lines'] and len(obj['lines']) >= 3:
            original_len = len(obj['lines'])
            obj['lines'] = close_shape(obj['lines'])
            if len(obj['lines']) > original_len:
                stats['closed_shapes'] += 1
    
    # Extract dimensions from instruction
    dimensions = extract_dimensions(instruction)
    
    # Apply dimensions if found
    if dimensions:
        objects = apply_dimensions(objects, instruction, dimensions)
        stats['applied_dimensions'] += 1
    
    # Format cleaned output
    cleaned_output = format_output(objects)
    
    return {
        'instruction': instruction,
        'input': input_text,
        'output': cleaned_output
    }


def main():
    parser = argparse.ArgumentParser(description='Clean CADLLM dataset')
    parser.add_argument('--input', type=str, required=True, help='Input dataset file (JSONL)')
    parser.add_argument('--output', type=str, required=True, help='Output cleaned dataset file (JSONL)')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of entries to process (for testing)')
    parser.add_argument('--skip', type=int, default=0, help='Skip first N entries')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Statistics
    stats = {
        'total': 0,
        'processed': 0,
        'skipped_empty': 0,
        'skipped_no_objects': 0,
        'normalized': 0,
        'closed_shapes': 0,
        'removed_multiple': 0,
        'kept_multiple': 0,
        'applied_dimensions': 0
    }
    
    print("=" * 80)
    print("CADLLM Dataset Cleaning")
    print("=" * 80)
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print()
    
    # Process entries
    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        for line_num, line in enumerate(infile, 1):
            if args.skip and line_num <= args.skip:
                continue
            
            if args.limit and stats['processed'] >= args.limit:
                break
            
            stats['total'] += 1
            
            try:
                entry = json.loads(line.strip())
                cleaned = clean_entry(entry, stats)
                
                if cleaned:
                    outfile.write(json.dumps(cleaned) + '\n')
                    stats['processed'] += 1
                
                # Progress update
                if stats['total'] % 1000 == 0:
                    print(f"Processed: {stats['total']:,} entries, Cleaned: {stats['processed']:,}", end='\r')
            
            except json.JSONDecodeError as e:
                print(f"\n⚠️  Error parsing line {line_num}: {e}")
                continue
    
    print()  # New line after progress
    print()
    print("=" * 80)
    print("Cleaning Complete!")
    print("=" * 80)
    print(f"Total entries:     {stats['total']:,}")
    print(f"Cleaned entries:   {stats['processed']:,}")
    print(f"Skipped (empty):   {stats['skipped_empty']:,}")
    print(f"Skipped (no obj):  {stats['skipped_no_objects']:,}")
    print(f"Normalized coords: {stats['normalized']:,}")
    print(f"Closed shapes:     {stats['closed_shapes']:,}")
    print(f"Removed multiple:  {stats['removed_multiple']:,}")
    print(f"Kept multiple:     {stats['kept_multiple']:,}")
    print(f"Applied dims:      {stats['applied_dimensions']:,}")
    print()
    print(f"✅ Cleaned dataset saved to: {output_path}")


if __name__ == "__main__":
    main()

