#!/usr/bin/env python3
"""
Batch test script for testing multiple audio files
Tests the complete workflow: Audio → Transcription → Parsing → DXF Generation
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

async def test_audio_to_dxf(audio_file_path: str) -> Dict:
    """Test full pipeline from audio file to DXF"""
    result = {
        "file": os.path.basename(audio_file_path),
        "success": False,
        "transcription": None,
        "instructions_count": 0,
        "dxf_size": 0,
        "error": None
    }
    
    try:
        from app.services.whisper_service import whisper_service
        from app.services.gpt_parser_service import gpt_parser_service
        from app.services.dxf_generator_service import dxf_generator_service
        from app.schemas.parser import CADFileType
    except ImportError as e:
        result["error"] = f"Import error: {e}"
        return result
    
    # Check services
    if not whisper_service:
        result["error"] = "Whisper service not available"
        return result
    if not gpt_parser_service:
        result["error"] = "GPT parser service not available"
        return result
    if not dxf_generator_service:
        result["error"] = "DXF generator service not available"
        return result
    
    # Step 1: Transcribe
    try:
        with open(audio_file_path, 'rb') as f:
            file_content = f.read()
        
        text, detected_language, duration = await whisper_service.transcribe_file(
            file_content=file_content,
            filename=os.path.basename(audio_file_path),
            language="en"
        )
        
        if not text:
            result["error"] = "Transcription failed - no text returned"
            return result
        
        result["transcription"] = text
    except Exception as e:
        result["error"] = f"Transcription error: {e}"
        return result
    
    # Step 2: Parse
    try:
        instructions, _ = await gpt_parser_service.parse_text(
            text=text,
            file_type=CADFileType.DXF
        )
        
        if not instructions:
            result["error"] = "No instructions generated"
            return result
        
        result["instructions_count"] = len(instructions)
    except Exception as e:
        result["error"] = f"Parsing error: {e}"
        return result
    
    # Step 3: Generate DXF
    try:
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        result["dxf_size"] = len(dxf_bytes)
        
        # Validate
        is_valid, msg = dxf_generator_service.validate_dxf(dxf_bytes)
        if not is_valid:
            result["error"] = f"DXF validation failed: {msg}"
            return result
    except Exception as e:
        result["error"] = f"DXF generation error: {e}"
        return result
    
    result["success"] = True
    return result

async def test_all_audio_files(audio_dir: str, output_dir: str = None):
    """Test all audio files in a directory"""
    audio_path = Path(audio_dir)
    if not audio_path.exists():
        print(f"❌ Directory not found: {audio_dir}")
        return
    
    # Find all audio files
    audio_extensions = ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm']
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(list(audio_path.glob(f"*{ext}")))
        audio_files.extend(list(audio_path.glob(f"*{ext.upper()}")))
    
    if not audio_files:
        print(f"❌ No audio files found in: {audio_dir}")
        return
    
    print("=" * 80)
    print(f"🎯 Testing {len(audio_files)} audio file(s)")
    print("=" * 80)
    
    # Setup output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path(__file__).parent.parent.parent / "test_output"
    output_path.mkdir(exist_ok=True)
    
    results = []
    for i, audio_file in enumerate(sorted(audio_files), 1):
        print(f"\n[{i}/{len(audio_files)}] Testing: {audio_file.name}")
        print("-" * 80)
        
        result = await test_audio_to_dxf(str(audio_file))
        results.append(result)
        
        if result["success"]:
            print(f"✅ Success!")
            print(f"   Transcription: {result['transcription'][:100]}...")
            print(f"   Instructions: {result['instructions_count']}")
            print(f"   DXF Size: {result['dxf_size']} bytes")
            
            # Save DXF file
            safe_name = audio_file.stem.replace(" ", "_").replace("/", "_")
            dxf_file = output_path / f"{safe_name}.dxf"
            try:
                # Regenerate DXF to save
                from app.services.gpt_parser_service import gpt_parser_service
                from app.services.dxf_generator_service import dxf_generator_service
                from app.schemas.parser import CADFileType
                
                instructions, _ = await gpt_parser_service.parse_text(
                    text=result["transcription"],
                    file_type=CADFileType.DXF
                )
                dxf_bytes = dxf_generator_service.generate_dxf(instructions)
                
                with open(dxf_file, 'wb') as f:
                    f.write(dxf_bytes)
                print(f"   Saved: {dxf_file}")
            except Exception as e:
                print(f"   ⚠️  Could not save DXF: {e}")
        else:
            print(f"❌ Failed: {result['error']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"Total files: {len(results)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if failed > 0:
        print("\nFailed files:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['file']}: {r['error']}")
    
    if successful > 0:
        print("\nSuccessful files:")
        for r in results:
            if r["success"]:
                print(f"  - {r['file']}: {r['instructions_count']} instructions, {r['dxf_size']} bytes")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_all_audio_files.py <audio_directory> [output_directory]")
        print("Example: python test_all_audio_files.py /path/to/audio /path/to/output")
        sys.exit(1)
    
    audio_directory = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else None
    
    asyncio.run(test_all_audio_files(audio_directory, output_directory))

