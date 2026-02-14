#!/usr/bin/env python3
"""
Simple test script for Audio → DXF pipeline
Tests the complete workflow: Audio → Transcription → Parsing → DXF Generation
"""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

async def test_audio_to_dxf(audio_file_path: str):
    """Test full pipeline from audio file to DXF"""
    print("=" * 70)
    print("🎯 Testing Audio → DXF Generation Pipeline")
    print("=" * 70)
    
    # Import services
    try:
        from app.services.whisper_service import whisper_service
        from app.services.gpt_parser_service import gpt_parser_service
        from app.services.dxf_generator_service import dxf_generator_service
        from app.schemas.parser import CADFileType
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Check services
    if not whisper_service:
        print("❌ Whisper service not available")
        return False
    if not gpt_parser_service:
        print("❌ GPT parser service not available")
        return False
    if not dxf_generator_service:
        print("❌ DXF generator service not available")
        return False
    
    # Step 1: Transcribe
    print("\n📝 Step 1: Transcribing audio...")
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return False
    
    try:
        # Read audio file as bytes
        with open(audio_file_path, 'rb') as f:
            file_content = f.read()
        
        # Transcribe using transcribe_file method
        text, detected_language, duration = await whisper_service.transcribe_file(
            file_content=file_content,
            filename=os.path.basename(audio_file_path),
            language="en"
        )
        
        if not text:
            print("❌ Transcription failed - no text returned")
            return False
        
        print(f"✅ Transcribed: \"{text}\"")
        if detected_language:
            print(f"   Language: {detected_language}")
        if duration:
            print(f"   Duration: {duration:.2f}s")
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Parse
    print("\n🔍 Step 2: Parsing to CAD instructions...")
    try:
        instructions, _ = await gpt_parser_service.parse_text(
            text=text,
            file_type=CADFileType.DXF
        )
        
        if not instructions:
            print("❌ No instructions generated")
            return False
        
        print(f"✅ Generated {len(instructions)} instruction(s):")
        for i, instr in enumerate(instructions, 1):
            print(f"   {i}. {instr.command} (confidence: {instr.confidence:.2f})")
    except Exception as e:
        print(f"❌ Parsing error: {e}")
        return False
    
    # Step 3: Generate DXF
    print("\n📐 Step 3: Generating DXF file...")
    try:
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        print(f"✅ Generated DXF: {len(dxf_bytes)} bytes")
        
        # Validate
        is_valid, msg = dxf_generator_service.validate_dxf(dxf_bytes)
        if is_valid:
            print("✅ DXF validation passed")
        else:
            print(f"⚠️  Validation warning: {msg}")
    except Exception as e:
        print(f"❌ DXF generation error: {e}")
        return False
    
    # Step 4: Save
    print("\n💾 Step 4: Saving DXF file...")
    try:
        output_dir = Path(__file__).parent.parent.parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "audio_generated.dxf"
        
        with open(output_file, 'wb') as f:
            f.write(dxf_bytes)
        
        print(f"✅ Saved to: {output_file}")
    except Exception as e:
        print(f"❌ Save error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ Pipeline test completed successfully!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    # Handle filenames with spaces by joining all arguments after script name
    if len(sys.argv) > 1:
        audio_file = " ".join(sys.argv[1:])  # Join all args to handle spaces in filename
    else:
        audio_file = "test_audio.wav"
    
    # Expand user path if it starts with ~
    if audio_file.startswith("~"):
        audio_file = os.path.expanduser(audio_file)
    
    # Convert to absolute path if not already
    if not os.path.isabs(audio_file):
        audio_file = str(Path(__file__).parent.parent.parent / audio_file)
    
    success = asyncio.run(test_audio_to_dxf(audio_file))
    sys.exit(0 if success else 1)

