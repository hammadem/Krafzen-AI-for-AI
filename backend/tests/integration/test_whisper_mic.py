#!/usr/bin/env python3
"""
Test Whisper transcription with microphone input
Records audio from microphone and sends it to the transcription endpoint
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
    print("📦 Installing sounddevice and soundfile...")
    os.system("pip install sounddevice soundfile numpy")
    import sounddevice as sd
    import soundfile as sf
    import numpy as np

def record_audio(duration=5, sample_rate=44100, filename="test_audio.wav"):
    """
    Record audio from microphone
    
    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate (Hz)
        filename: Output filename
    """
    print(f"🎤 Recording for {duration} seconds...")
    print("   Speak now!")
    
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
    print(f"✅ Audio saved: {filename} ({file_size:.2f} KB)")
    
    return filename

def transcribe_file(file_path, base_url="http://localhost:8000"):
    """
    Send audio file to transcription endpoint
    
    Args:
        file_path: Path to audio file
        base_url: Backend API base URL
    """
    print(f"\n📤 Sending audio to transcription endpoint...")
    
    try:
        with open(file_path, 'rb') as audio_file:
            files = {'file': (os.path.basename(file_path), audio_file, 'audio/wav')}
            params = {'language': 'en'}
            
            response = requests.post(
                f"{base_url}/api/v1/transcribe",
                files=files,
                params=params,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Transcription successful!")
            print(f"\n📝 Transcribed Text:")
            print(f"   {result.get('text', 'N/A')}")
            print(f"\n📊 Details:")
            print(f"   Language: {result.get('language', 'N/A')}")
            print(f"   Duration: {result.get('duration', 'N/A')} seconds")
            print(f"   Status: {result.get('status', 'N/A')}")
            return result
        else:
            print(f"❌ Transcription failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        return None

def main():
    """Main function"""
    print("=" * 60)
    print("🎤 Whisper Transcription - Microphone Test")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend server is not responding")
            sys.exit(1)
    except Exception as e:
        print("❌ Cannot connect to backend server at http://localhost:8000")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
        sys.exit(1)
    
    print("✅ Backend server is running\n")
    
    # Get recording duration
    try:
        duration = float(input("Enter recording duration in seconds (default: 5): ") or "5")
    except ValueError:
        duration = 5
    
    # Record audio
    audio_file = record_audio(duration=duration)
    
    # Transcribe
    result = transcribe_file(audio_file)
    
    # Cleanup
    cleanup = input("\n🗑️  Delete test audio file? (y/n, default: y): ").lower()
    if cleanup != 'n':
        try:
            os.remove(audio_file)
            print(f"✅ Deleted {audio_file}")
        except:
            pass
    
    if result:
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Test failed")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
