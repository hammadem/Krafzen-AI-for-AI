#!/usr/bin/env python3
"""
Test script for Audio → Transcription → JSON → DXF pipeline
Usage: python tests/integration/test_audio_to_json_to_dxf.py [audio_file_path]
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.whisper_service import whisper_service
from app.services.text_to_json_converter import text_to_json_converter
from app.services.json_instruction_parser import json_instruction_parser
from app.services.dxf_generator_service import dxf_generator_service
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_audio_to_json_to_dxf(audio_file_path: str):
    """
    Test pipeline: Audio → Transcription → JSON → DXF Generation
    
    Args:
        audio_file_path: Path to audio file
    """
    print("=" * 60)
    print("Testing Audio → JSON → DXF Generation Pipeline (RECOMMENDED)")
    print("=" * 60)
    
    # Step 1: Transcribe audio
    print("\n📝 Step 1: Transcribing audio file...")
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return False
    
    try:
        # Read audio file as bytes
        with open(audio_file_path, 'rb') as f:
            file_content = f.read()
        
        # Transcribe using transcribe_file method
        transcribed_text, detected_language, duration = await whisper_service.transcribe_file(
            file_content=file_content,
            filename=os.path.basename(audio_file_path),
            language="en"
        )
        
        if not transcribed_text:
            print("❌ Transcription failed or returned empty text")
            return False
        
        print(f"✅ Transcription successful!")
        print(f"   Text: {transcribed_text[:200]}..." if len(transcribed_text) > 200 else f"   Text: {transcribed_text}")
        if detected_language:
            print(f"   Language: {detected_language}")
        if duration:
            print(f"   Duration: {duration:.2f}s")
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Convert text to JSON
    print("\n🔄 Step 2: Converting text to structured JSON format...")
    try:
        json_data = await text_to_json_converter.convert_text_to_json(
            text=transcribed_text,
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
    
    # Step 3: Parse JSON to instructions
    print("\n📋 Step 3: Parsing JSON to CAD instructions...")
    try:
        instructions = json_instruction_parser.parse_json(json_data)
        
        if not instructions:
            print("❌ No instructions parsed from JSON")
            return False
        
        print(f"✅ Parsing successful! Generated {len(instructions)} instructions")
        for i, instr in enumerate(instructions[:10], 1):  # Show first 10
            print(f"   {i}. {instr.command}")
        
    except Exception as e:
        print(f"❌ JSON parsing error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Generate DXF file
    print("\n📐 Step 4: Generating DXF file...")
    try:
        dxf_bytes = dxf_generator_service.generate_dxf(
            instructions=instructions,
            filename="audio_json_generated.dxf"
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
    
    # Step 5: Save DXF file
    print("\n💾 Step 5: Saving DXF file...")
    try:
        output_dir = Path(__file__).parent.parent.parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        # Generate output filename based on input audio file
        audio_name = Path(audio_file_path).stem
        safe_name = audio_name.replace(" ", "_").replace("/", "_")
        output_file = output_dir / f"{safe_name}_json.dxf"
        
        with open(output_file, 'wb') as f:
            f.write(dxf_bytes)
        
        print(f"✅ DXF file saved to: {output_file}")
        print(f"   You can open this file in AutoCAD or other CAD software")
        
    except Exception as e:
        print(f"❌ File save error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Full pipeline test completed successfully!")
    print("=" * 60)
    return True


async def main():
    """Main function"""
    # Check for audio file argument
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        # Try to find test audio file
        test_audio = Path(__file__).parent.parent.parent / "test_audio.wav"
        if test_audio.exists():
            audio_file = str(test_audio)
            print(f"Using default test audio file: {audio_file}")
        else:
            print("Usage: python test_audio_to_json_to_dxf.py [audio_file_path]")
            print("Or place a test_audio.wav file in the backend directory")
            sys.exit(1)
    
    # Check if services are available
    if not whisper_service:
        print("❌ Whisper service is not available. Check OPENAI_API_KEY.")
        sys.exit(1)
    
    if not text_to_json_converter:
        print("❌ Text to JSON converter is not available. Check OPENAI_API_KEY.")
        sys.exit(1)
    
    if not dxf_generator_service:
        print("❌ DXF generator service is not available. Check ezdxf installation.")
        sys.exit(1)
    
    # Run test
    success = await test_audio_to_json_to_dxf(audio_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

