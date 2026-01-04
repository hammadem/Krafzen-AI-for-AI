#!/usr/bin/env python3
"""
Test script to generate DXF file from JSON format instructions
Usage: python tests/integration/test_json_kitchen.py
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.json_instruction_parser import json_instruction_parser
from app.services.dxf_generator_service import dxf_generator_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


JSON_INSTRUCTIONS = {
  "units": "inches",
  "format": "DXF",
  "entities": {
    "room_boundary": {
      "type": "lwpolyline",
      "points": [
        [0, 0],
        [144, 0],
        [144, 120],
        [0, 120],
        [0, 0]
      ]
    },
    "door": {
      "opening_line": {
        "type": "line",
        "start": [144, 20],
        "end": [144, 56]
      },
      "swing_arc": {
        "type": "arc",
        "center": [144, 20],
        "radius": 36,
        "start_angle": 90,
        "end_angle": 0
      }
    },
    "bottom_cabinets": [
      {
        "type": "lwpolyline",
        "points": [
          [0, 0],
          [48, 0],
          [48, 20],
          [0, 20],
          [0, 0]
        ]
      },
      {
        "type": "lwpolyline",
        "points": [
          [48, 0],
          [96, 0],
          [96, 20],
          [48, 20],
          [48, 0]
        ]
      },
      {
        "type": "lwpolyline",
        "points": [
          [96, 0],
          [144, 0],
          [144, 20],
          [96, 20],
          [96, 0]
        ]
      }
    ],
    "right_wall_cabinet": {
      "type": "lwpolyline",
      "points": [
        [110, 40],
        [144, 40],
        [144, 60],
        [110, 60],
        [110, 40]
      ]
    },
    "sink_base": {
      "type": "lwpolyline",
      "points": [
        [50, 120],
        [94, 120],
        [94, 96],
        [50, 96],
        [50, 120]
      ]
    },
    "sink_basin": {
      "type": "lwpolyline",
      "points": [
        [58, 112],
        [86, 112],
        [86, 100],
        [58, 100],
        [58, 112]
      ]
    },
    "stove_base": {
      "type": "lwpolyline",
      "points": [
        [0, 36],
        [24, 36],
        [24, 60],
        [0, 60],
        [0, 36]
      ]
    },
    "stove_burners": [
      {
        "type": "circle",
        "center": [6, 52],
        "radius": 3
      },
      {
        "type": "circle",
        "center": [14, 52],
        "radius": 3
      },
      {
        "type": "circle",
        "center": [6, 44],
        "radius": 3
      },
      {
        "type": "circle",
        "center": [14, 44],
        "radius": 3
      }
    ],
    "small_appliance": {
      "type": "lwpolyline",
      "points": [
        [10, 120],
        [30, 120],
        [30, 100],
        [10, 100],
        [10, 120]
      ]
    },
    "countertop": {
      "type": "lwpolyline",
      "points": [
        [0, 60],
        [24, 60],
        [24, 96],
        [110, 96],
        [110, 60],
        [144, 60],
        [144, 120],
        [0, 120],
        [0, 60]
      ]
    }
  }
}


def generate_dxf_from_json():
    """
    Generate DXF file from JSON format instructions
    """
    print("=" * 60)
    print("Generating DXF File from JSON Instructions")
    print("=" * 60)
    
    # Step 1: Parse JSON to CAD instructions
    print("\n🔍 Step 1: Parsing JSON instructions...")
    try:
        instructions = json_instruction_parser.parse_json(JSON_INSTRUCTIONS)
        
        if not instructions:
            print("❌ No instructions parsed from JSON")
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
            filename="kitchen_from_json.dxf"
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
        output_file = output_dir / "kitchen_from_json.dxf"
        
        with open(output_file, 'wb') as f:
            f.write(dxf_bytes)
        
        print(f"✅ DXF file saved to: {output_file}")
        print(f"   You can open this file in AutoCAD or other CAD software")
        
    except Exception as e:
        print(f"❌ File save error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ DXF generation from JSON completed successfully!")
    print("=" * 60)
    return True


def main():
    """Main function"""
    if not dxf_generator_service:
        print("❌ DXF generator service is not available. Check ezdxf installation.")
        sys.exit(1)
    
    # Run generation
    success = generate_dxf_from_json()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

