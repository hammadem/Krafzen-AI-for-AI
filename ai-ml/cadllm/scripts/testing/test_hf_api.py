#!/usr/bin/env python3
"""
Test script for CAD-LLM model inference via multiple methods.

This script tests the CAD-LLM model using one of:
- Hugging Face Inference API (default, for cloud/remote testing)
- Hugging Face Space API (for testing deployed Space)
- Ollama (for local testing on Mac)

It loads all configuration from the .env file and provides a simple way
to test model inference.

Usage:
    # Use Hugging Face Inference API (default)
    python test_hf_api.py
    
    # Use Hugging Face Space API
    python test_hf_api.py --space
    
    # Use Ollama for local testing
    python test_hf_api.py --ollama
    
    # With a custom prompt
    python test_hf_api.py "Create a rectangle 50x30mm"
    python test_hf_api.py --space "Create a rectangle 50x30mm"
    python test_hf_api.py --ollama "Create a rectangle 50x30mm"
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

# Add utils directory to path for cadllm_client import
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from cadllm_client import CADLLMClient

# Load environment variables from .env file (look in project root)
# This script is in scripts/testing/, so go up 4 levels to reach project root
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print("✅ Loaded configuration from .env file")
else:
    print("⚠️  Warning: .env file not found. Using environment variables only.")
    print("   Create .env file with: HF_TOKEN=your_token and HF_MODEL_NAME=your-username/model-name")

# Get configuration from environment variables
HF_TOKEN = os.getenv("HF_TOKEN")
HF_USERNAME = os.getenv("HF_USERNAME")
HF_FINE_TUNED_MODEL_NAME = os.getenv("HF_FINE_TUNED_MODEL_NAME")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")

# Construct HF_MODEL_NAME from HF_USERNAME and HF_FINE_TUNED_MODEL_NAME if not set
if not HF_MODEL_NAME and HF_USERNAME and HF_FINE_TUNED_MODEL_NAME:
    HF_MODEL_NAME = f"{HF_USERNAME}/{HF_FINE_TUNED_MODEL_NAME}"

# Optional: Only needed if you create a dedicated Inference Endpoint
# Leave this unset/empty to use the standard Inference API (recommended for most users)
# To get an endpoint URL:
#   1. Go to https://huggingface.co/inference-endpoints
#   2. Create a new endpoint for your model
#   3. Copy the endpoint URL (e.g., https://xxx.us-east-1.aws.endpoints.huggingface.cloud)
#   4. Add to .env: HF_ENDPOINT_URL=https://xxx.us-east-1.aws.endpoints.huggingface.cloud
HF_ENDPOINT_URL = os.getenv("HF_ENDPOINT_URL")

# Default test prompt
DEFAULT_PROMPT = "Create a circle with radius 10mm centered at origin"

# Ollama configuration
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "cadllm")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Hugging Face Space configuration
HF_SPACE_REPO = os.getenv("HF_SPACE_REPO")
HF_SPACE_URL = os.getenv("HF_SPACE_URL")  # Optional: direct URL override


def validate_config():
    """
    Validate that required configuration is present.
    
    Note: This function should be called after HF_MODEL_NAME is constructed
    from HF_USERNAME and HF_FINE_TUNED_MODEL_NAME if needed.
    
    Raises:
        ValueError: If required configuration is missing
    """
    """
    Validate that required configuration is present.
    
    Raises:
        ValueError: If required configuration is missing
    """
    if not HF_TOKEN:
        raise ValueError(
            "HF_TOKEN not found in .env file or environment.\n"
            "Please add it to your .env file: HF_TOKEN=your_token_here"
        )
    
    # Validate that we have either HF_MODEL_NAME or both HF_USERNAME and HF_FINE_TUNED_MODEL_NAME
    if not HF_MODEL_NAME:
        if not (HF_USERNAME and HF_FINE_TUNED_MODEL_NAME):
            raise ValueError(
                "HF_MODEL_NAME not found in .env file or environment.\n"
                "Please add one of the following to your .env file:\n"
                "  Option 1: HF_MODEL_NAME=your-username/model-name\n"
                "  Option 2: HF_USERNAME=your-username and HF_FINE_TUNED_MODEL_NAME=model-name"
            )


def test_with_space(prompt: str):
    """Test using Hugging Face Space API."""
    print("=" * 60)
    print("CAD-LLM Hugging Face Space API Test")
    print("=" * 60)
    
    # Determine Space URL
    if HF_SPACE_URL:
        space_url = HF_SPACE_URL.rstrip('/')
    elif HF_SPACE_REPO:
        # Construct Space URL from repo name (format: username/space-name)
        # Hugging Face Spaces use format: https://username-space-name.hf.space
        repo_parts = HF_SPACE_REPO.split('/')
        if len(repo_parts) == 2:
            username, space_name = repo_parts
            space_url = f"https://{username}-{space_name}.hf.space"
        else:
            print("❌ Error: HF_SPACE_REPO must be in format 'username/space-name'")
            print(f"   Got: {HF_SPACE_REPO}")
            sys.exit(1)
    else:
        # Try to construct from HF_MODEL_NAME or HF_USERNAME/HF_FINE_TUNED_MODEL_NAME
        if HF_MODEL_NAME:
            # Assume Space has similar name (this is a fallback)
            model_parts = HF_MODEL_NAME.split('/')
            if len(model_parts) == 2:
                username, model_name = model_parts
                # Try common Space naming patterns
                space_name = model_name.replace('_', '-').lower()
                space_url = f"https://{username}-{space_name}.hf.space"
            else:
                print("❌ Error: Cannot determine Space URL from HF_MODEL_NAME.")
                print("   Please set HF_SPACE_URL or HF_SPACE_REPO in .env file.")
                sys.exit(1)
        elif HF_USERNAME:
            print("❌ Error: Cannot determine Space URL.")
            print("   Please set HF_SPACE_URL or HF_SPACE_REPO in .env file.")
            print("   Example: HF_SPACE_REPO=username/space-name")
            print("   Or: HF_SPACE_URL=https://username-space-name.hf.space")
            sys.exit(1)
        else:
            print("❌ Error: Cannot determine Space URL.")
            print("   Please set HF_SPACE_URL or HF_SPACE_REPO in .env file.")
            print("   Example: HF_SPACE_REPO=username/space-name")
            print("   Or: HF_SPACE_URL=https://username-space-name.hf.space")
            sys.exit(1)
    
    print(f"Space URL: {space_url}")
    print(f"Prompt: {prompt}")
    print("=" * 60)
    
    # Test Space API endpoint
    api_url = f"{space_url}/generate"
    
    payload = {
        "instruction": prompt,
        "max_new_tokens": 400,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    try:
        print("\n🔄 Generating response from Space...")
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        generated_text = result.get("output", "").strip()
        
        print("\n" + "=" * 60)
        print("✅ GENERATED OUTPUT (Space API)")
        print("=" * 60)
        print(generated_text)
        print("=" * 60)
        print(f"\n✅ Space API test completed successfully!")
        print(f"   Space URL: {space_url}")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to Space at {space_url}")
        print("   The Space may still be building or the URL is incorrect.")
        print("\n📝 To fix this:")
        print("   1. Check that the Space is deployed: https://huggingface.co/spaces")
        print("   2. Wait for the Space to finish building (check the Space page)")
        print("   3. Verify the Space URL is correct")
        print("   4. Try accessing the Space in your browser first")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response: {e.response.text[:500]}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_with_ollama(prompt: str):
    """Test using Ollama (local inference)."""
    print("=" * 60)
    print("CAD-LLM Ollama Test (Local)")
    print("=" * 60)
    print(f"Model: {OLLAMA_MODEL_NAME}")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Prompt: {prompt}")
    print("=" * 60)
    
    # Check if Ollama is running
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code != 200:
            raise Exception("Ollama not accessible")
    except Exception as e:
        print(f"\n❌ Ollama is not running or not accessible: {e}")
        print(f"   Expected URL: {OLLAMA_BASE_URL}")
        print("\n📝 To fix this:")
        print("   1. Make sure Ollama is installed: https://ollama.ai")
        print("   2. Start Ollama (it should run automatically)")
        print("   3. Deploy the model: make deploy-ollama")
        sys.exit(1)
    
    # Generate using Ollama
    payload = {
        "model": OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 400,
        }
    }
    
    try:
        print("\n🔄 Generating response...")
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        generated_text = result.get("response", "").strip()
        
        print("\n" + "=" * 60)
        print("✅ GENERATED OUTPUT")
        print("=" * 60)
        print(generated_text)
        print("=" * 60)
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """
    Main function to test the Hugging Face Inference API or Ollama.
    
    Loads configuration from .env, initializes the client, and generates
    a response for the test prompt.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Test CAD-LLM model inference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with Hugging Face Inference API (default)
  python test_hf_api.py
  
  # Test with Hugging Face Space API
  python test_hf_api.py --space
  
  # Test with Ollama (local)
  python test_hf_api.py --ollama
  
  # Custom prompt with Space API
  python test_hf_api.py --space "Create a kitchen with sink and stove"
        """
    )
    parser.add_argument(
        "--ollama",
        action="store_true",
        help="Use Ollama for local inference instead of Hugging Face API"
    )
    parser.add_argument(
        "--space",
        action="store_true",
        help="Use Hugging Face Space API instead of Inference API"
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Custom prompt (optional)"
    )
    args = parser.parse_args()
    
    # Get prompt
    if args.prompt:
        prompt = " ".join(args.prompt)
    else:
        prompt = DEFAULT_PROMPT
    
    # Use Ollama if requested
    if args.ollama:
        test_with_ollama(prompt)
        return
    
    # Use Space API if requested
    if args.space:
        test_with_space(prompt)
        return
    
    # Otherwise use Hugging Face API
    print("=" * 60)
    print("CAD-LLM Hugging Face Inference API Test")
    print("=" * 60)
    
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n📝 To fix this:")
        print("   1. Create a .env file in the workspace directory")
        print("   2. Add the following lines:")
        print("      HF_TOKEN=your_huggingface_token_here")
        print("      HF_USERNAME=your-username")
        print("      HF_FINE_TUNED_MODEL_NAME=your-model-name")
        print("      # Or set HF_MODEL_NAME directly:")
        print("      # HF_MODEL_NAME=your-username/your-model-name")
        print("      # Optional (only if using dedicated endpoint):")
        print("      # HF_ENDPOINT_URL=https://your-endpoint-url")
        print("   3. Run this script again")
        sys.exit(1)
    
    # Prompt is already set above from args.prompt or DEFAULT_PROMPT
    print(f"\n📝 Prompt: {prompt}")
    
    print(f"   Model: {HF_MODEL_NAME}")
    if HF_ENDPOINT_URL:
        print(f"   Using custom endpoint: {HF_ENDPOINT_URL}")
    else:
        print(f"   Using standard Inference API")
    print(f"   Prompt: {prompt}")
    
    # Initialize client
    try:
        print("\n🔧 Initializing CAD-LLM client...")
        client = CADLLMClient(
            model_name=HF_MODEL_NAME,
            token=HF_TOKEN,
            endpoint_url=HF_ENDPOINT_URL if HF_ENDPOINT_URL else None
        )
        print("✅ Client initialized successfully")
    except Exception as e:
        print(f"\n❌ Failed to initialize client: {e}")
        print("\n📝 Troubleshooting:")
        print("   - Check that your HF_TOKEN is valid")
        print("   - Verify that HF_MODEL_NAME is correct")
        print("   - Make sure the model exists and you have access to it")
        sys.exit(1)
    
    # Generate response
    try:
        print("\n🔄 Generating response...")
        print("   (This may take 1-3 seconds)")
        result = client.generate(prompt)
        
        print("\n" + "=" * 60)
        print("✅ GENERATED OUTPUT")
        print("=" * 60)
        print(result)
        print("=" * 60)
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Generation failed:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e) if str(e) else repr(e)}")
        
        # Show more details if available
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"   Cause: {e.__cause__}")
        
        print("\n📝 Troubleshooting:")
        print("   - Check your internet connection")
        print("   - Verify your HF_TOKEN is valid and has access to the model")
        print("   - Check that the model exists: https://huggingface.co/" + HF_MODEL_NAME)
        print("   - If model is private, make sure your token has access")
        print("   - Try running: python test_hf_api.py 'test prompt' to see more details")
        
        # Print full traceback for debugging
        import traceback
        print("\n📋 Full error details:")
        traceback.print_exc()
        
        sys.exit(1)


if __name__ == "__main__":
    main()
