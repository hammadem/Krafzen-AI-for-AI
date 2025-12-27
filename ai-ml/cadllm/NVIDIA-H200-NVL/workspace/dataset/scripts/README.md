# Dataset Scripts

This directory contains utility scripts for validating and generating CAD dataset records.

## Scripts

### `validate_dataset.py`

Validates a dataset JSONL file by checking for:
- **Out-of-bounds (OOB) objects**: Objects that extend beyond room boundaries
- **Overlaps**: Objects that overlap with each other (excluding subfeatures like burners)

**Usage:**
```bash
python validate_dataset.py \
    --input ../jsonl/dataset.jsonl \
    --output ../jsonl/dataset_validated.jsonl \
    --filter_oob \
    --filter_overlaps \
    --exclude_subfeatures
```

**Options:**
- `--input`: Input JSONL file to validate
- `--output`: Output JSONL file (only valid records)
- `--filter_oob`: Filter out records with out-of-bounds objects
- `--filter_overlaps`: Filter out records with overlapping objects
- `--exclude_subfeatures`: Exclude subfeatures (e.g., burners) from overlap checks
- `--seed`: Random seed (default: 42)

**Example:**
```bash
# Validate and filter a dataset
python validate_dataset.py \
    --input ../jsonl/cadllm_final.jsonl \
    --output ../jsonl/cadllm_final_validated.jsonl \
    --filter_oob \
    --filter_overlaps \
    --exclude_subfeatures
```

---

### `generate_records.py`

Generates new non-overlapping CAD records using templates for different room types (kitchen, bathroom, bedroom, living room).

**Features:**
- Generates records with proper coordinate placement
- Ensures no overlaps between objects
- Ensures all objects are within room bounds
- Includes burners for cooktops/stoves
- Uses the same placement logic as the main dataset generation

**Usage:**
```bash
python generate_records.py \
    --output ../jsonl/new_records.jsonl \
    --target_count 10000 \
    --seed 42
```

**Options:**
- `--output`: Output JSONL file path
- `--target_count`: Number of records to generate (default: 60000)
- `--seed`: Random seed (default: 42)

**Example:**
```bash
# Generate 10,000 new records
python generate_records.py \
    --output ../jsonl/topup_10k.jsonl \
    --target_count 10000 \
    --seed 42
```

**Note:** The script has an ~80% success rate (some attempts fail due to placement constraints). It will continue generating until the target count is reached or a maximum attempt limit is hit.

---

## Dataset Format

All scripts work with JSONL files where each line is a JSON object with:

```json
{
    "instruction": "Draw a kitchen with sink, stove, and refrigerator.",
    "input": "(none)",
    "output": "UNITS: mm\nORIGIN_POLICY: room_center_at_(0,0)\nROOM: rect w=4000 h=3000 center=(0,0)\nWALLS: rect_perimeter closed=true layer=WALLS\n..."
}
```

The `output` field contains a DSL-like format with:
- `UNITS`: Measurement units (mm)
- `ORIGIN_POLICY`: Coordinate system policy
- `ROOM`: Room dimensions and center
- `WALLS`: Wall perimeter
- Object definitions: `NAME: shape w=W h=H center=(x,y) layer=LAYER closed=true anchor_wall=WALL`

---

## Requirements

- Python 3.11+
- Standard library only (no external dependencies)

---

## Final Dataset

The final validated dataset is located at:
```
../jsonl/cadllm_final.jsonl
```

This dataset contains 200,191 records with:
- ✅ No out-of-bounds objects
- ✅ No overlaps (excluding subfeatures)
- ✅ Proper coordinate placement
- ✅ All room types (kitchen, bathroom, bedroom, living room)

