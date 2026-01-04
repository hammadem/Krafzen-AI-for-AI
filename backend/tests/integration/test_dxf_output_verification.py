"""
Verification script for DXF file output format
This script tests the DXF generator to ensure correct file output
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.dxf_generator_service import DXFGeneratorService
from app.schemas.parser import ParsedInstruction


def test_dxf_output_format():
    """Test DXF file output format and structure"""
    print("🔍 Testing DXF file output format...")
    
    service = DXFGeneratorService()
    
    # Create sample instructions
    instructions = [
        ParsedInstruction(
            command="line",
            parameters={"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 100}},
            confidence=0.95
        ),
        ParsedInstruction(
            command="circle",
            parameters={"center": {"x": 50, "y": 50}, "radius": 25},
            confidence=0.90
        ),
        ParsedInstruction(
            command="rectangle",
            parameters={"corner": {"x": 10, "y": 10}, "width": 80, "height": 60},
            confidence=0.85
        ),
    ]
    
    try:
        # Generate DXF
        dxf_bytes = service.generate_dxf(instructions, filename="test_output.dxf")
        
        print(f"✅ DXF file generated: {len(dxf_bytes)} bytes")
        
        # Verify file structure
        dxf_content = dxf_bytes.decode('utf-8', errors='ignore')
        
        # Check for DXF section markers
        required_sections = ['SECTION', 'HEADER', 'TABLES', 'ENTITIES', 'EOF']
        found_sections = []
        
        for section in required_sections:
            if section in dxf_content:
                found_sections.append(section)
                print(f"✅ Found section: {section}")
            else:
                print(f"⚠️  Missing section: {section}")
        
        # Validate DXF file
        is_valid, error_msg = service.validate_dxf(dxf_bytes)
        if is_valid:
            print("✅ DXF file validation passed")
        else:
            print(f"❌ DXF file validation failed: {error_msg}")
            return False
        
        # Save test file for manual inspection
        test_output_dir = Path(__file__).parent.parent.parent / "test_output"
        test_output_dir.mkdir(exist_ok=True)
        test_file = test_output_dir / "test_output.dxf"
        
        with open(test_file, 'wb') as f:
            f.write(dxf_bytes)
        
        print(f"✅ Test DXF file saved to: {test_file}")
        print(f"   You can open this file in AutoCAD or other CAD software to verify")
        
        return True
        
    except Exception as e:
        print(f"❌ DXF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dxf_entity_types():
    """Test all supported entity types"""
    print("\n🔍 Testing all supported entity types...")
    
    service = DXFGeneratorService()
    
    instructions = [
        ParsedInstruction(command="line", parameters={"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 100}}, confidence=0.95),
        ParsedInstruction(command="circle", parameters={"center": {"x": 50, "y": 50}, "radius": 25}, confidence=0.90),
        ParsedInstruction(command="rectangle", parameters={"corner": {"x": 10, "y": 10}, "width": 80, "height": 60}, confidence=0.85),
        ParsedInstruction(command="arc", parameters={"center": {"x": 50, "y": 50}, "radius": 30, "start_angle": 0, "end_angle": 90}, confidence=0.80),
        ParsedInstruction(command="polyline", parameters={"points": [{"x": 0, "y": 0}, {"x": 50, "y": 0}, {"x": 50, "y": 50}, {"x": 0, "y": 50}], "close": True}, confidence=0.85),
    ]
    
    try:
        dxf_bytes = service.generate_dxf(instructions)
        is_valid, error_msg = service.validate_dxf(dxf_bytes)
        
        if is_valid:
            print("✅ All entity types generated successfully")
            print(f"   File size: {len(dxf_bytes)} bytes")
            return True
        else:
            print(f"❌ Validation failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ Entity type test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("DXF Output Format Verification")
    print("=" * 60)
    
    success = True
    success &= test_dxf_output_format()
    success &= test_dxf_entity_types()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

