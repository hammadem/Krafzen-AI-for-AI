#!/usr/bin/env python3
"""
Test script for Hugging Face Inference API.

This script tests the CAD-LLM model using the Hugging Face Inference API.
It loads all configuration from the .env file and provides a simple way
to test model inference.

Usage:
    python test_hf_api.py
    
    Or with a custom prompt:
    python test_hf_api.py "Create a rectangle 50x30mm"
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from cadllm_client import CADLLMClient

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
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


def main():
    """
    Main function to test the Hugging Face Inference API.
    
    Loads configuration from .env, initializes the client, and generates
    a response for the test prompt.
    """
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
    
    # Get prompt from command line or use default
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(f"\n📝 Using custom prompt from command line")
    else:
        prompt = DEFAULT_PROMPT
        print(f"\n📝 Using default test prompt")
    
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
