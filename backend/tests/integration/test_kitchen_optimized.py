#!/usr/bin/env python3
"""
Test script to generate DXF file from optimized kitchen cabinet instructions
Usage: python tests/integration/test_kitchen_optimized.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.gpt_parser_service import gpt_parser_service
from app.services.dxf_generator_service import dxf_generator_service
from app.schemas.parser import CADFileType
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Read optimized instructions
OPTIMIZED_INSTRUCTIONS = """Kitchen CAD Drawing – Optimized Instructions for DXF Generator

Draw the following geometric entities. Use exact coordinates in millimeters. Origin (0,0) is bottom-left corner.

1. ROOM WALLS (Layer: Walls):
   - Draw rectangle: corner (0, 0), width 3657.6mm, height 3048mm
   - Draw rectangle: corner (127, 127), width 3403.6mm, height 2794mm

2. DOOR ON RIGHT WALL (Layer: Doors):
   - Draw line: start (1828.8, 2921), end (1828.8, 2895.6)
   - Draw arc: center (1828.8, 2895.6), radius 914.4mm, start angle 270, end angle 90

3. BASE CABINETS ON TOP WALL (Layer: Cabinets):
   - Draw rectangle: corner (177.8, 2311.4), width 1193.8mm, height 609.6mm
   - Draw rectangle: corner (2286, 2311.4), width 1244.6mm, height 609.6mm
   - Draw rectangle: corner (1371.6, 2311.4), width 914.4mm, height 609.6mm

4. BASE CABINETS ON LEFT WALL (Layer: Cabinets):
   - Draw rectangle: corner (127, 127), width 609.6mm, height 1016mm
   - Draw rectangle: corner (127, 1905), width 609.6mm, height 1016mm
   - Draw rectangle: corner (127, 1143), width 609.6mm, height 762mm

5. REFRIGERATOR (Layer: Appliances):
   - Draw rectangle: corner (2616.2, 127), width 914.4mm, height 762mm

6. OVERHEAD CABINETS (Layer: Cabinets, use dashed linetype):
   - Draw rectangle: corner (1371.6, 2702), width 914.4mm, height 381mm
   - Draw rectangle: corner (127, 1524), width 381mm, height 762mm

7. DIMENSIONS (Layer: Dimensions):
   - Draw dimension: points [(0, 3148), (3657.6, 3148)], value 3657.6
   - Draw dimension: points [(3757.6, 0), (3757.6, 3048)], value 3048
   - Draw dimension: points [(177.8, 3000), (3530.6, 3000)], value 3352.8
   - Draw dimension: points [(1371.6, 3000), (2286, 3000)], value 914.4
   - Draw dimension: points [(1828.8, 3000), (2743.2, 3000)], value 914.4
   - Draw dimension: points [(736.6, 100), (1498.6, 100)], value 762
   - Draw dimension: points [(2616.2, 100), (3530.6, 100)], value 914.4"""


async def generate_kitchen_dxf():
    """
    Generate DXF file from optimized kitchen cabinet instructions
    """
    print("=" * 60)
    print("Generating Kitchen Cabinet DXF File (Optimized Instructions)")
    print("=" * 60)
    
    # Step 1: Parse text to CAD instructions
    print("\n🔍 Step 1: Parsing optimized kitchen instructions...")
    try:
        instructions, raw_response = await gpt_parser_service.parse_text(
            text=OPTIMIZED_INSTRUCTIONS,
            file_type=CADFileType.DXF,
            additional_context=None
        )
        
        if not instructions:
            print("❌ No instructions parsed from text")
            return False
        
        print(f"✅ Parsing successful! Generated {len(instructions)} instructions")
        for i, instr in enumerate(instructions, 1):
            print(f"   {i}. {instr.command} (confidence: {instr.confidence:.2f})")
        
    except Exception as e:
        print(f"❌ Parsing error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Generate DXF file
    print("\n📐 Step 2: Generating DXF file...")
    try:
        dxf_bytes = dxf_generator_service.generate_dxf(
            instructions=instructions,
            filename="kitchen_cabinet_optimized.dxf"
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
    
    # Step 3: Save DXF file
    print("\n💾 Step 3: Saving DXF file...")
    try:
        output_dir = Path(__file__).parent.parent.parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "kitchen_cabinet_optimized.dxf"
        
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
    if not gpt_parser_service:
        print("❌ GPT parser service is not available. Check OPENAI_API_KEY.")
        sys.exit(1)
    
    if not dxf_generator_service:
        print("❌ DXF generator service is not available. Check ezdxf installation.")
        sys.exit(1)
    
    # Run generation
    success = await generate_kitchen_dxf()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

