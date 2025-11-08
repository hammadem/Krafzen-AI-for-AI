#!/usr/bin/env python3
"""
Simple test script for KRAFZEN AI endpoints
Usage: python test_endpoints.py
"""

import requests
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_health():
    """Test basic health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health/")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health Check: {data.get('status', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_detailed_health():
    """Test detailed health endpoint"""
    print("\n🔍 Testing Detailed Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health/detailed")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status: {data.get('status', 'unknown')}")
        print(f"   Environment: {data.get('environment', 'unknown')}")
        print(f"   Version: {data.get('version', 'unknown')}")
        
        deps = data.get('dependencies', {})
        print(f"   OpenAI: {deps.get('openai', 'unknown')}")
        print(f"   Database: {deps.get('database', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ Detailed Health Check Failed: {e}")
        return False

def test_transcribe(audio_file_path=None):
    """Test transcription endpoint"""
    print("\n🎤 Testing Transcription Endpoint...")
    
    if not audio_file_path:
        print("⚠️  No audio file provided. Skipping transcription test.")
        print("   To test: python test_endpoints.py --audio /path/to/audio.mp3")
        return None
    
    if not Path(audio_file_path).exists():
        print(f"❌ Audio file not found: {audio_file_path}")
        return None
    
    try:
        with open(audio_file_path, 'rb') as f:
            files = {'file': f}
            params = {'language': 'en'}
            response = requests.post(
                f"{BASE_URL}/api/v1/transcribe",
                files=files,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success':
                print(f"✅ Transcription Successful!")
                print(f"   Text: {data.get('text', '')[:100]}...")
                print(f"   Language: {data.get('language', 'unknown')}")
                print(f"   Duration: {data.get('duration', 0)}s")
                return data.get('text')
            else:
                print(f"❌ Transcription Failed: {data}")
                return None
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json() if e.response else {}
        print(f"❌ Transcription HTTP Error: {error_data.get('detail', str(e))}")
        return None
    except Exception as e:
        print(f"❌ Transcription Failed: {e}")
        return None

def test_parse(text=None):
    """Test parsing endpoint"""
    print("\n🤖 Testing Parsing Endpoint...")
    
    if not text:
        # Use a default test text
        text = "Create a rectangle with width 100 and height 50"
        print(f"   Using default test text: {text}")
    
    try:
        data = {
            "text": text,
            "file_type": "dxf",
            "additional_context": "Test parsing"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/parse",
            json=data
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get('status') == 'success':
            print(f"✅ Parsing Successful!")
            instructions = result.get('instructions', [])
            print(f"   Found {len(instructions)} instruction(s):")
            for i, inst in enumerate(instructions, 1):
                print(f"   {i}. {inst.get('command', 'unknown')} "
                      f"(confidence: {inst.get('confidence', 0):.2f})")
            return result
        else:
            print(f"❌ Parsing Failed: {result}")
            return None
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json() if e.response else {}
        print(f"❌ Parsing HTTP Error: {error_data.get('detail', str(e))}")
        return None
    except Exception as e:
        print(f"❌ Parsing Failed: {e}")
        return None

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 KRAFZEN AI Endpoint Testing")
    print("=" * 60)
    
    # Parse command line arguments
    audio_file = None
    if len(sys.argv) > 1:
        if '--audio' in sys.argv:
            idx = sys.argv.index('--audio')
            if idx + 1 < len(sys.argv):
                audio_file = sys.argv[idx + 1]
    
    # Run tests
    results = {
        'health': test_health(),
        'detailed_health': test_detailed_health(),
    }
    
    # Test transcription if audio file provided
    transcribed_text = None
    if audio_file:
        transcribed_text = test_transcribe(audio_file)
    else:
        test_transcribe()
    
    # Test parsing
    if transcribed_text:
        # Use transcribed text
        results['parse'] = test_parse(transcribed_text)
    else:
        # Use default text
        results['parse'] = test_parse()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Health Check: {'✅' if results['health'] else '❌'}")
    print(f"Detailed Health: {'✅' if results['detailed_health'] else '❌'}")
    print(f"Parsing: {'✅' if results.get('parse') else '❌'}")
    
    if audio_file:
        print(f"Transcription: {'✅' if transcribed_text else '❌'}")
    else:
        print("Transcription: ⚠️  (not tested - no audio file)")
    
    print("\n💡 Tips:")
    print("   - Add OpenAI API key to backend/.env to test Whisper/GPT-4")
    print("   - Test with audio: python test_endpoints.py --audio /path/to/audio.mp3")
    print("   - View API docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main()

