#!/usr/bin/env python3
"""
Local inference script for Mac using Ollama.

This script runs the fine-tuned CAD model locally on your Mac using Ollama.
It requires the model to be deployed to Ollama first (use `make deploy-ollama`).

Usage:
    python infer_local_mac.py
    python infer_local_mac.py "Create a circle with radius 10mm"
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration from .env
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "cadllm")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# System prompt (matches training format)
SYSTEM_PROMPT = (
    "You are a CAD code assistant. Given a simple CAD description, "
    "output ONLY the strict DSL format shown below. Do not use natural language.\n\n"
    "Required DSL Format (STRICT - must match exactly):\n"
    "UNITS: mm\n"
    "ORIGIN_POLICY: room_center_at_(0,0)\n"
    "ROOM: rect w=WIDTH h=HEIGHT center=(0,0)\n"
    "WALLS: rect_perimeter closed=true layer=WALLS\n"
    "OBJECT_NAME: rect w=WIDTH h=HEIGHT center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL\n"
    "OBJECT_NAME: circle r=RADIUS center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL\n\n"
    "Rules:\n"
    "- Always start with UNITS, ORIGIN_POLICY, ROOM, WALLS (in that order)\n"
    "- Use rect or circle primitives only\n"
    "- Entity names must use underscores (e.g., COFFEE_TABLE not COFFEE TABLE)\n"
    "- anchor_wall must be: north, south, east, west, or none (for free placement)\n"
    "- All coordinates in mm, room centered at (0,0)\n"
    "- All objects must be within room bounds\n"
    "- Use circle for round objects (burners, round tables, columns)\n"
    "- Use rect for rectangular objects (tables, desks, appliances)\n\n"
    "Default dimensions if not specified:\n"
    "- Rooms: 3000x3000 (bedroom), 4000x3000 (kitchen), 2000x2000 (bathroom)\n"
    "- Simple shapes: r=100 (circles), 200x200 (squares), 300x200 (rectangles)\n"
)


def check_ollama_running():
    """Check if Ollama is running."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def check_model_exists(model_name: str):
    """Check if the model exists in Ollama."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m.get("name", "").startswith(model_name) for m in models)
        return False
    except Exception as e:
        print(f"   ⚠️  Error checking models: {e}")
        return False


def generate(prompt: str, max_tokens: int = 400, temperature: float = 0.7):
    """
    Generate CAD DSL output from a prompt using Ollama.
    
    Args:
        prompt: User instruction (e.g., "Create a circle with radius 10mm")
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (lower = more deterministic)
    """
    print("=" * 60)
    print("CAD-LLM Local Inference (Ollama)")
    print("=" * 60)
    print(f"Model: {OLLAMA_MODEL_NAME}")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Prompt: {prompt}")
    print("=" * 60)
    print("\n🔄 Generating...\n")
    
    # Ollama uses a simple prompt format
    # The system prompt is already in the Modelfile, so we just send the user prompt
    # Ollama will automatically apply the chat template from the Modelfile
    payload = {
        "model": OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_predict": max_tokens,
        }
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120  # 2 minute timeout
        )
        response.raise_for_status()
        
        result = response.json()
        generated_text = result.get("response", "").strip()
        
        print("=" * 60)
        print("OUTPUT:")
        print("=" * 60)
        print(generated_text)
        print("=" * 60)
        
        return generated_text
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error calling Ollama API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response: {e.response.text}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


def main():
    """Main function."""
    # Check if Ollama is running
    print("🔍 Checking Ollama connection...")
    if not check_ollama_running():
        print("\n❌ Ollama is not running or not accessible")
        print(f"   Expected URL: {OLLAMA_BASE_URL}")
        print("\n📝 To fix this:")
        print("   1. Make sure Ollama is installed: https://ollama.ai")
        print("   2. Start Ollama (it should run automatically after installation)")
        print("   3. Verify it's running: ollama list")
        print("   4. If using a different URL, set OLLAMA_BASE_URL in .env")
        sys.exit(1)
    print("   ✅ Ollama is running")
    
    # Check if model exists
    print(f"🔍 Checking if model '{OLLAMA_MODEL_NAME}' exists...")
    if not check_model_exists(OLLAMA_MODEL_NAME):
        print(f"\n❌ Model '{OLLAMA_MODEL_NAME}' not found in Ollama")
        print("\n📝 To fix this:")
        print(f"   1. Deploy the model to Ollama: make deploy-ollama")
        print(f"   2. Or manually: ollama pull {OLLAMA_MODEL_NAME}")
        print(f"   3. Check available models: ollama list")
        print(f"   4. If using a different model name, set OLLAMA_MODEL_NAME in .env")
        sys.exit(1)
    print(f"   ✅ Model '{OLLAMA_MODEL_NAME}' found")
    
    # Get prompt from command line or use default
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "Create a circle with radius 10mm centered at origin"
    
    try:
        generate(prompt)
        print("\n✅ Inference completed successfully!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
