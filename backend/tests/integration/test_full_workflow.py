#!/usr/bin/env python3
"""
Complete workflow test: Microphone → Transcription → Parsing
Records audio, transcribes it, and parses it into CAD instructions
"""

import requests
import sys
import os

try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
except ImportError:
    print("❌ Required packages not installed.")
    print("📦 Please install: pip install sounddevice soundfile numpy")
    sys.exit(1)

BASE_URL = "http://localhost:8000"

def check_server():
    """Check if backend server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running\n")
            return True
    except Exception as e:
        print("❌ Cannot connect to backend server at http://localhost:8000")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
        return False
    return False

def record_audio(duration=5, sample_rate=44100, filename="test_audio.wav"):
    """Record audio from microphone"""
    print(f"🎤 Recording for {duration} seconds...")
    print("   👉 Speak your CAD instruction now!")
    print("   Example: 'Create a rectangle with width 100 and height 50'\n")
    
    # Record audio
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    sd.wait()  # Wait until recording is finished
    
    # Save to file
    sf.write(filename, audio_data, sample_rate)
    file_size = os.path.getsize(filename) / 1024  # Size in KB
    print(f"✅ Audio saved: {filename} ({file_size:.2f} KB)\n")
    
    return filename

def transcribe_audio(file_path):
    """Send audio file to transcription endpoint"""
    print("📤 Step 1: Transcribing audio with Whisper...")
    
    try:
        with open(file_path, 'rb') as audio_file:
            files = {'file': (os.path.basename(file_path), audio_file, 'audio/wav')}
            params = {'language': 'en'}
            
            response = requests.post(
                f"{BASE_URL}/api/v1/transcribe",
                files=files,
                params=params,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            transcribed_text = result.get('text', '')
            
            print("✅ Transcription successful!")
            print(f"\n📝 Transcribed Text:")
            print(f"   \"{transcribed_text}\"")
            print(f"\n📊 Transcription Details:")
            print(f"   Language: {result.get('language', 'N/A')}")
            print(f"   Duration: {result.get('duration', 'N/A')} seconds")
            print()
            
            return transcribed_text
        else:
            print(f"❌ Transcription failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        return None

def parse_text(text, file_type="dxf"):
    """Send transcribed text to GPT-4 parsing endpoint"""
    print("🤖 Step 2: Parsing text into CAD instructions with GPT-4...")
    
    try:
        data = {
            "text": text,
            "file_type": file_type,
            "additional_context": "Voice command from microphone"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/parse",
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('status') == 'success':
                instructions = result.get('instructions', [])
                
                print("✅ Parsing successful!")
                print(f"\n📋 CAD Instructions Generated:")
                print(f"   File Type: {result.get('file_type', 'N/A').upper()}")
                print(f"   Number of Instructions: {len(instructions)}\n")
                
                for i, inst in enumerate(instructions, 1):
                    print(f"   {i}. Command: {inst.get('command', 'unknown')}")
                    print(f"      Parameters: {inst.get('parameters', {})}")
                    print(f"      Confidence: {inst.get('confidence', 0):.2f}")
                    print()
                
                return result
            else:
                print(f"❌ Parsing failed: {result}")
                return None
        else:
            print(f"❌ Parsing failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        return None

def main():
    """Main workflow"""
    print("=" * 70)
    print("🎯 KRAFZEN AI - Complete Workflow Test")
    print("   Microphone → Whisper Transcription → GPT-4 Parsing")
    print("=" * 70)
    print()
    
    # Check server
    if not check_server():
        sys.exit(1)
    
    # Get recording duration
    try:
        duration_input = input("Enter recording duration in seconds (default: 5): ").strip()
        duration = float(duration_input) if duration_input else 5
    except ValueError:
        duration = 5
    
    # Get file type
    file_type = input("Enter CAD file type (dxf/dwg/revit, default: dxf): ").strip().lower()
    if file_type not in ['dxf', 'dwg', 'revit']:
        file_type = 'dxf'
    
    print()
    
    # Step 1: Record audio
    audio_file = record_audio(duration=duration)
    
    # Step 2: Transcribe
    transcribed_text = transcribe_audio(audio_file)
    
    if not transcribed_text:
        print("❌ Transcription failed. Cannot proceed to parsing.")
        sys.exit(1)
    
    # Step 3: Parse
    parse_result = parse_text(transcribed_text, file_type=file_type)
    
    # Cleanup
    print("=" * 70)
    cleanup = input("🗑️  Delete test audio file? (y/n, default: y): ").lower()
    if cleanup != 'n':
        try:
            os.remove(audio_file)
            print(f"✅ Deleted {audio_file}")
        except:
            pass
    
    # Summary
    print("\n" + "=" * 70)
    if transcribed_text and parse_result:
        print("✅ Complete workflow test successful!")
        print("\n📊 Summary:")
        print(f"   • Recorded: {duration} seconds of audio")
        print(f"   • Transcribed: \"{transcribed_text}\"")
        print(f"   • Parsed: {len(parse_result.get('instructions', []))} CAD instruction(s)")
        print(f"   • File Type: {parse_result.get('file_type', 'N/A').upper()}")
    else:
        print("❌ Workflow test failed")
        if not transcribed_text:
            print("   • Transcription step failed")
        if not parse_result:
            print("   • Parsing step failed")
    print("=" * 70)

if __name__ == "__main__":
    main()

