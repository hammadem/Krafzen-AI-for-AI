#!/usr/bin/env python3
"""
Recreate the CADLLM dataset from scratch with proper descriptions.

This script:
1. Reads raw TXT/JSON files from the raw dataset
2. Matches them with descriptions from Excel files using File_id
3. Filters for 2D-only operations
4. Creates a new JSONL dataset with proper instructions and inputs

Usage:
    python recreate_dataset_with_descriptions.py \
        --raw-dir ../../cadllm_raw/cad_collection_select_V2/cad_collection_select_V2 \
        --excel-dir ../../cadllm_raw/ccs_description_text \
        --output ../jsonl/cadllm_2d_with_descriptions.jsonl
"""

import json
import argparse
import pandas as pd
import os
from pathlib import Path
from tqdm import tqdm
import re

# 3D operations that should be excluded
BAD_3D_OPERATIONS = [
    "<extrude>", "<revolve>", "<loft>",
    "joinfeature", "cutfeature",
    "onesidefeatureextenttype",
    "θ=", "φ=", "γ=",  # Unicode Greek letters
    "theta=", "phi=", "gamma=",  # ASCII versions
    "px=", "py=", "pz=",  # Position coordinates
]

# 2D sketch operations
GOOD_2D_OPERATIONS = [
    "<circle>", "<line>", "<arc>", "<rectangle>", "<polyline>",
    "<spline>", "<ellipse>", "<point>",
]

def extract_file_id_from_path(file_path):
    """Extract file ID from file path. Files are named like 00956163.txt"""
    filename = Path(file_path).stem
    try:
        # Remove leading zeros
        file_id = int(filename)
        return file_id
    except ValueError:
        return None

def normalize_ccs_for_matching(ccs_text):
    """Normalize CCS for matching - extract 2D sketch part and normalize."""
    if not ccs_text:
        return ""
    text = str(ccs_text).strip()
    lines = text.split('\n')
    sketch_lines = []
    for line in lines:
        line_lower = line.lower()
        # Stop at first 3D operation
        if any(marker in line_lower for marker in ['extrude', 'θ=', 'theta=', 'phi=', 'gamma=', 'px=', 'py=', 'pz=']):
            break
        # Keep 2D operations and markers
        if line.strip() and ('<sol>' in line_lower or '<eos>' in line_lower or 
                            '<circle>' in line_lower or '<line>' in line_lower or 
                            '<arc>' in line_lower or 'x=' in line or 'y=' in line or 'r=' in line):
            sketch_lines.append(line.strip())
    # Normalize whitespace and case
    normalized = ' '.join(sketch_lines)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.lower()

def load_descriptions(excel_dir):
    """Load all descriptions from Excel files and create lookup by normalized 2D CCS."""
    excel_dir = Path(excel_dir)
    
    # Load parameter descriptions (most important)
    param_file = excel_dir / "ccs_parameter_data.xlsx"
    ccs_lookup = {}  # Maps normalized 2D CCS to description
    
    if param_file.exists():
        print(f"📊 Loading {param_file.name}...")
        param_df = pd.read_excel(param_file)
        print(f"   Loaded {len(param_df)} parameter descriptions")
        
        for _, row in tqdm(param_df.iterrows(), total=len(param_df), desc="Indexing descriptions"):
            description = row.get('description', '')
            original_ccs = row.get('original_ccs', '')
            
            if pd.notna(description) and pd.notna(original_ccs):
                # Normalize the 2D sketch part
                normalized_ccs = normalize_ccs_for_matching(original_ccs)
                if normalized_ccs and len(normalized_ccs) > 20:  # Minimum meaningful length
                    # Store description (keep first match if duplicates)
                    if normalized_ccs not in ccs_lookup:
                        ccs_lookup[normalized_ccs] = str(description).strip()
    
    print(f"✅ Created lookup with {len(ccs_lookup)} unique 2D CCS patterns")
    return ccs_lookup

def extract_2d_sketch(ccs_text):
    """Extract 2D sketch operations from CCS, stopping at first 3D operation."""
    if not ccs_text:
        return None, 0
    
    lines = ccs_text.split('\n')
    sketch_lines = []
    sketch_op_count = 0
    
    for line in lines:
        line_lower = line.lower()
        
        # Stop at first 3D operation
        if any(op in line_lower for op in BAD_3D_OPERATIONS):
            break
        
        # Count and collect 2D sketch operations
        if any(op in line_lower for op in GOOD_2D_OPERATIONS):
            sketch_op_count += 1
            sketch_lines.append(line)
        elif line.strip() in ['<SOL>', '<EOS>']:
            # Keep start/end markers
            sketch_lines.append(line)
    
    if sketch_op_count < 2:
        return None, sketch_op_count
    
    sketch_output = '\n'.join(sketch_lines)
    if not sketch_output or len(sketch_output.strip()) < 30:
        return None, sketch_op_count
    
    return sketch_output, sketch_op_count

def process_raw_files(raw_dir, ccs_lookup, output_file):
    """Process raw TXT files and create dataset with descriptions by matching CCS content."""
    # Convert to Path objects
    raw_dir = Path(raw_dir)
    output_path = Path(output_file)
    
    # If not absolute, resolve relative to current working directory
    if not raw_dir.is_absolute():
        raw_dir = Path.cwd() / raw_dir
    raw_dir = raw_dir.resolve()
    
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path
    output_path = output_path.resolve()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    stats = {
        'total_files': 0,
        'matched_with_desc': 0,
        'no_description': 0,
        'skipped_too_simple': 0,
        'skipped_no_2d': 0,
        'written': 0
    }
    
    print(f"\n🔄 Processing raw files...")
    print(f"   Raw directory: {raw_dir}")
    print(f"   Output: {output_path}")
    
    # Find all TXT files
    txt_files = list(raw_dir.rglob("*.txt"))
    print(f"   Found {len(txt_files)} TXT files")
    
    with open(output_path, 'w') as outfile:
        for txt_file in tqdm(txt_files, desc="Processing files"):
            stats['total_files'] += 1
            
            # Read CCS from TXT file
            try:
                with open(txt_file, 'r') as f:
                    ccs_output = f.read().strip()
            except Exception as e:
                continue
            
            # Extract 2D sketch part
            sketch_output, op_count = extract_2d_sketch(ccs_output)
            
            if not sketch_output:
                if op_count < 2:
                    stats['skipped_too_simple'] += 1
                else:
                    stats['skipped_no_2d'] += 1
                continue
            
            # Normalize sketch for matching
            normalized_sketch = normalize_ccs_for_matching(sketch_output)
            
            # Try to find matching description
            description = None
            
            # Try exact match first
            if normalized_sketch in ccs_lookup:
                description = ccs_lookup[normalized_sketch]
            else:
                # Try substring matching (Excel's 2D part might be subset of our filtered 2D)
                for excel_ccs, excel_desc in ccs_lookup.items():
                    if excel_ccs in normalized_sketch and len(excel_ccs) > 30:
                        description = excel_desc
                        break
                    elif normalized_sketch in excel_ccs and len(normalized_sketch) > 30:
                        description = excel_desc
                        break
            
            if description:
                stats['matched_with_desc'] += 1
            else:
                # No description found, use generic
                description = "Generate a 2D CAD drawing from the following sketch commands"
                stats['no_description'] += 1
            
            # Create entry
            entry = {
                "instruction": description,
                "input": description,  # Use description as input too
                "output": sketch_output
            }
            
            # Write to output
            outfile.write(json.dumps(entry) + '\n')
            stats['written'] += 1
    
    print(f"\n✅ Processing complete!")
    print(f"   Total files processed: {stats['total_files']}")
    print(f"   Matched with descriptions: {stats['matched_with_desc']} ({stats['matched_with_desc']*100/max(stats['written'],1):.1f}%)")
    print(f"   No description: {stats['no_description']} ({stats['no_description']*100/max(stats['written'],1):.1f}%)")
    print(f"   Skipped (too simple): {stats['skipped_too_simple']}")
    print(f"   Skipped (no 2D): {stats['skipped_no_2d']}")
    print(f"   Written to dataset: {stats['written']}")
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Recreate CADLLM dataset with descriptions')
    parser.add_argument('--raw-dir', type=str, required=True, 
                       help='Raw data directory containing TXT files')
    parser.add_argument('--excel-dir', type=str, required=True,
                       help='Directory containing Excel description files')
    parser.add_argument('--output', type=str, required=True,
                       help='Output JSONL file')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Recreating CADLLM Dataset with Descriptions")
    print("=" * 80)
    
    # Load descriptions
    print("\n" + "=" * 80)
    print("Loading descriptions from Excel files...")
    print("=" * 80)
    ccs_lookup = load_descriptions(args.excel_dir)
    
    # Process raw files
    print("\n" + "=" * 80)
    print("Processing raw files...")
    print("=" * 80)
    stats = process_raw_files(args.raw_dir, ccs_lookup, args.output)
    
    print("\n" + "=" * 80)
    print("✅ Dataset recreation complete!")
    print("=" * 80)
    print(f"\nOutput file: {args.output}")
    print(f"Total entries: {stats['written']}")
    print(f"Entries with descriptions: {stats['matched_with_desc']} ({stats['matched_with_desc']*100/max(stats['written'],1):.1f}%)")

if __name__ == "__main__":
    main()

