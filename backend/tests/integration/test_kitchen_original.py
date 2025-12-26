#!/usr/bin/env python3
"""
Test script to generate DXF file from original kitchen cabinet instructions
Uses JSON pipeline (Option 2) for better accuracy
Usage: python tests/integration/test_kitchen_original.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.text_to_json_converter import text_to_json_converter
from app.services.json_instruction_parser import json_instruction_parser
from app.services.dxf_generator_service import dxf_generator_service
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ORIGINAL_INSTRUCTIONS = """Kitchen CAD Drawing – Detailed Instructions

Room Size:

Width: 12'

Depth: 10'

1. Draw the Room

Draw rectangle 12'-0" × 10'-0"

Offset inside 5 inches for interior wall thickness

Keep outer boundary as external wall

2. Door (Right Wall)

Place door at middle of the right wall

Door width: 3'-0"

Swing: open inward, hinge on right, swing left

Show arc for swing

3. Base Cabinets

Top wall (12 ft side):

Start 2" from inside corner

Base cabinet depth: 2'-0"

Run cabinets along full top wall except under-sink area

Add sink centered on top wall:

Sink width: 3'-0"

Left wall (10 ft side):

Add base cabinets full length except for cooktop area

Cabinet depth: 2'-0"

4. Appliances

Cooktop + Oven (Left Wall):

Cooktop block: 2'-6" wide

Oven depth flush with cabinets

Refrigerator (Right Wall):

Size: 3'-0" wide × 2'-6" deep

Place near bottom-right corner

5. Overhead Cabinets

Add overheads above sink (top wall)

Add above cooktop (left wall)

Depth: 1'-3"

6. Dimensions

Add linear dimensions for:

Room width (12')

Room height (10')

Cabinet lengths

Sink centerline

Door width + swing

Appliance sizes

All dimensions on a separate layer.

7. Layers to Use

Walls (thick line)

Cabinets (medium)

Appliances (medium)

Doors (thin)

Dimensions (thin)"""


async def generate_kitchen_dxf():
    """
    Generate DXF file from original kitchen cabinet instructions using JSON pipeline (Option 2)
    """
    print("=" * 60)
    print("Generating Kitchen Cabinet DXF File (Original Instructions)")
    print("Using JSON Pipeline (Option 2) - RECOMMENDED")
    print("=" * 60)
    
    # Step 1: Convert text to JSON
    print("\n🔄 Step 1: Converting text to structured JSON format...")
    try:
        json_data = await text_to_json_converter.convert_text_to_json(
            text=ORIGINAL_INSTRUCTIONS,
            units="inches"
        )
        
        print(f"✅ JSON conversion successful!")
        print(f"   Entities in JSON: {len(json_data.get('entities', {}))}")
        print(f"   Units: {json_data.get('units', 'unknown')}")
        
    except Exception as e:
        print(f"❌ JSON conversion error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Parse JSON to CAD instructions
    print("\n📋 Step 2: Parsing JSON to CAD instructions...")
    try:
        instructions = json_instruction_parser.parse_json(json_data)
        
        if not instructions:
            print("❌ No instructions parsed from JSON")
            return False
        
        print(f"✅ Parsing successful! Generated {len(instructions)} instructions")
        for i, instr in enumerate(instructions[:15], 1):  # Show first 15
            print(f"   {i}. {instr.command}")
        if len(instructions) > 15:
            print(f"   ... and {len(instructions) - 15} more instructions")
        
    except Exception as e:
        print(f"❌ JSON parsing error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Generate DXF file
    print("\n📐 Step 3: Generating DXF file...")
    try:
        dxf_bytes = dxf_generator_service.generate_dxf(
            instructions=instructions,
            filename="kitchen_cabinet_original.dxf"
        )
        
        print(f"✅ DXF generation successful! File size: {len(dxf_bytes)} bytes")
        
        # Validate DXF
        is_valid, error_msg = dxf_generator_service.validate_dxf(dxf_bytes)
        if is_valid:
            print("✅ DXF file validation passed")
        else:
            print(f"⚠️  DXF validation warning: {error_msg}")
        
    except Exception as e:
        print(f"❌ DXF generation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Save DXF file
    print("\n💾 Step 4: Saving DXF file...")
    try:
        output_dir = Path(__file__).parent.parent.parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "kitchen_cabinet_original.dxf"
        
        with open(output_file, 'wb') as f:
            f.write(dxf_bytes)
        
        print(f"✅ DXF file saved to: {output_file}")
        print(f"   You can open this file in AutoCAD or other CAD software")
        
    except Exception as e:
        print(f"❌ File save error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Kitchen cabinet DXF generation completed successfully!")
    print("=" * 60)
    return True


async def main():
    """Main function"""
    # Check if services are available
    if not text_to_json_converter:
        print("❌ Text to JSON converter is not available. Check OPENAI_API_KEY.")
        sys.exit(1)
    
    if not json_instruction_parser:
        print("❌ JSON instruction parser is not available.")
        sys.exit(1)
    
    if not dxf_generator_service:
        print("❌ DXF generator service is not available. Check ezdxf installation.")
        sys.exit(1)
    
    # Run generation
    success = await generate_kitchen_dxf()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

