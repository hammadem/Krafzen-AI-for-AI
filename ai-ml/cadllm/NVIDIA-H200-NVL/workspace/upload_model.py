#!/usr/bin/env python3
"""
Upload merged model to Hugging Face Hub.

This script uploads an already-merged model to Hugging Face Hub.
For merging a LoRA adapter with the base model, use merge_model.py first.

Usage:
    python upload_model.py [--model_path PATH]
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, login
from transformers import AutoTokenizer

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration from .env (no hardcoded defaults)
# All values must be set in .env file or via command-line arguments


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Upload merged model to Hugging Face Hub"
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default=None,
        help="Path to merged model directory (required: set MODEL_PATH env var or use --model_path)"
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default=None,
        help="Base model identifier for model card (required: set BASE_MODEL env var or use --base_model)"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        default=None,
        help="Make repository private (default: True, use --public to make public)"
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Make repository public (overrides --private)"
    )
    return parser.parse_args()

def generate_model_card(model_path: Path, base_model: str, repo_id: str) -> str:
    """
    Generate a model card (README.md) based on the model path and model information.
    
    Args:
        model_path: Path to the merged model
        base_model: Base model identifier
        repo_id: Hugging Face repository ID
    
    Returns:
        Model card content as string
    """
    # Check if existing README is a template (contains "[More Information Needed]")
    model_readme = model_path / "README.md"
    is_template = False
    if model_readme.exists():
        existing_content = model_readme.read_text(encoding="utf-8")
        # Check if it's a PEFT template
        if "[More Information Needed]" in existing_content or "Model Card for Model ID" in existing_content:
            is_template = True
            print(f"   📄 Found template README.md in model path, generating new model card...")
        elif repo_id in existing_content and "base_model" in existing_content.lower():
            # It's a proper model card, use it
            print(f"   📄 Found existing model card in model path, using it...")
            return existing_content
        else:
            # It's a custom README but not a template, enhance it
            print(f"   📄 Found custom README.md in model path, enhancing it...")
            if repo_id not in existing_content:
                enhanced = f"# {repo_id}\n\n"
                enhanced += f"**Base Model:** {base_model}\n\n"
                enhanced += "---\n\n"
                enhanced += existing_content
                return enhanced
            return existing_content
    
    # Generate new model card (either no README or template detected)
    model_name = model_path.name
    current_date = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    current_year = __import__("datetime").datetime.now().strftime("%Y")
    
    model_card = f"""---
license: apache-2.0
base_model: {base_model}
tags:
  - cad
  - 2d-cad
  - qwen
  - fine-tuned
  - lora
  - cad-llm
  - text-generation
pipeline_tag: text-generation
library_name: transformers
---

# {repo_id}

Fine-tuned CAD-LLM model for generating 2D CAD coordinates from natural language descriptions.

## Model Details

- **Base Model:** [{base_model}](https://huggingface.co/{base_model})
- **Fine-tuning Method:** LoRA (Low-Rank Adaptation)
- **Model Type:** Causal Language Model
- **Language:** English
- **Task:** Text-to-CAD Coordinates Generation
- **Developed by:** KRAFZEN AI
- **Model type:** Text Generation
- **License:** apache-2.0

## Model Description

This model is a fine-tuned version of {base_model} specifically trained for 2D CAD coordinate generation. The model takes natural language CAD descriptions as input and outputs precise 2D CAD coordinates in a structured format.

### Output Format

The model generates coordinates in the following format:
- `<SOL>` - Start of object
- `<Circle>: x=0.0, y=0.0, r=48.0` - Circle with center and radius
- `<Line>: x=47.5, y=-32.0` - Line coordinates (multiple lines form a polyline)
- `<Arc>: x=-8.5, y=-58.0, α=64.0, f=1.0` - Arc with center, angle, and flag
- `<EOS>` - End of sequence

These coordinates are automatically converted to DXF files using coordinate parsers.

## Uses

### Direct Use

This model is designed for generating 2D CAD coordinates from natural language descriptions. It can be used to:
- Convert text descriptions to CAD coordinates
- Generate DXF files from natural language input
- Assist in CAD design workflows

### Downstream Use

The model can be fine-tuned further for specific CAD domains or integrated into CAD software applications.

### Out-of-Scope Use

- 3D CAD generation (model is trained for 2D only)
- Complex multi-object assemblies without explicit instructions
- Non-CAD related text generation

## How to Get Started with the Model

### Using Hugging Face Inference API

```python
from huggingface_hub import InferenceClient

client = InferenceClient(
    model="{repo_id}",
    token="your_token_here"
)

prompt = "Create a circle with radius 10mm centered at origin"
response = client.text_generation(prompt, max_new_tokens=400)
print(response)
```

### Using the CADLLM Client

```python
from cadllm_client import CADLLMClient

client = CADLLMClient("{repo_id}")
dxf_path = client.generate("Create a rectangle 100mm x 50mm")
print(f"DXF file saved to: {{dxf_path}}")
```

## Training Details

### Training Data

The model was trained on the CADLLM 2D dataset, which contains natural language CAD descriptions paired with coordinate outputs.

### Training Procedure

- **Training Method:** LoRA (Low-Rank Adaptation) fine-tuning
- **Base Model:** {base_model}
- **Training Date:** {current_date}

### Training Hyperparameters

- **Training regime:** Mixed precision (fp16)
- **LoRA rank:** 8
- **LoRA alpha:** 16
- **Target modules:** q_proj, v_proj

## Limitations

- Primarily designed for 2D CAD coordinate generation
- May require post-processing to convert coordinates to DXF format
- Best results with clear, specific CAD descriptions
- Accuracy depends on the quality and specificity of input descriptions

## Bias, Risks, and Limitations

The model may generate incorrect coordinates if the input description is ambiguous or unclear. Users should verify generated CAD files before use in production.

## Citation

If you use this model, please cite:

```bibtex
@misc{{{repo_id.replace("/", "_").replace("-", "_")}}},
  title={{CAD-LLM: Fine-tuned Model for 2D CAD Coordinate Generation}},
  author={{KRAFZEN AI}},
  year={{{current_year}}},
  publisher={{Hugging Face}},
  howpublished={{\\url{{https://huggingface.co/{repo_id}}}}}
}}
```

## License

This model is licensed under Apache 2.0, same as the base model.
"""
    return model_card

def validate_config(model_path: Path):
    """Validate required configuration and model path."""
    HF_TOKEN = os.getenv("HF_TOKEN")
    HF_USERNAME = os.getenv("HF_USERNAME")
    HF_FINE_TUNED_MODEL_NAME = os.getenv("HF_FINE_TUNED_MODEL_NAME")
    
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN not found in .env file. Please add HF_TOKEN=your_token_here")
    if not HF_USERNAME:
        raise ValueError("HF_USERNAME not found in .env file. Please add HF_USERNAME=your_username")
    if not HF_FINE_TUNED_MODEL_NAME:
        raise ValueError("HF_FINE_TUNED_MODEL_NAME not found in .env file. Please add HF_FINE_TUNED_MODEL_NAME=your_model_name")
    
    if not model_path.exists():
        raise ValueError(f"Model path not found: {model_path}")
    
    # Check if model path contains config.json (merged model)
    config_json = model_path / "config.json"
    
    if not config_json.exists():
        # Search recursively
        found_configs = list(model_path.rglob("config.json"))
        if not found_configs:
            raise ValueError(
                f"Model path '{model_path}' does not contain a valid merged model.\n"
                f"Expected 'config.json' file in the model directory.\n"
                f"\nIf you have a LoRA adapter, merge it first with:\n"
                f"  python merge_model.py --adapter_path <adapter_path> --output_dir {model_path}\n"
                f"\nFiles found in directory:\n"
                f"  {list(model_path.iterdir())[:10] if model_path.is_dir() else 'Not a directory'}"
            )

def upload_merged_model(model_path: Path, base_model: str, repo_id: str, private: bool = True):
    """Upload merged model to Hugging Face Hub."""
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    print("\n" + "=" * 60)
    print("Uploading Merged Model to Hugging Face Hub")
    print("=" * 60)
    print(f"Model path: {model_path}")
    print(f"Repository: {repo_id}")
    print(f"Private: {private}")
    print()
    
    # Login
    print("🔐 Logging in to Hugging Face...")
    login(token=HF_TOKEN)
    
    # Initialize API
    api = HfApi()
    
    # Create repository
    print(f"📦 Creating repository: {repo_id}")
    try:
        api.create_repo(
            repo_id=repo_id,
            repo_type="model",
            private=private,
            exist_ok=True
        )
        print(f"✅ Repository created: https://huggingface.co/{repo_id}")
    except Exception as e:
        if "403" in str(e) or "rights" in str(e).lower():
            print(f"❌ Permission denied: {e}")
            print("   Make sure your token has 'Write' permissions")
            raise
        print(f"⚠️  Repository creation: {e}")
    
    # Check if README.md exists, generate if not
    readme_path = model_path / "README.md"
    if not readme_path.exists():
        print("\n📝 Generating README.md (model card)...")
        readme_content = generate_model_card(model_path, base_model, repo_id)
        readme_path.write_text(readme_content, encoding="utf-8")
        print("   ✅ Generated README.md (model card) for model recognition")
    else:
        print("\n📄 Using existing README.md")
    
    # Upload
    print(f"\n📤 Uploading to {repo_id}...")
    api.upload_folder(
        folder_path=str(model_path),
        repo_id=repo_id,
        repo_type="model",
        commit_message="Upload merged model for Inference API"
    )
    
    print(f"\n✅ Model uploaded successfully!")
    print(f"   View at: https://huggingface.co/{repo_id}")
    print(f"\n📝 Update your .env file with:")
    print(f"   HF_MODEL_NAME={repo_id}")
    return repo_id

def check_model_status(repo_id):
    """Check the status of the uploaded model and provide guidance."""
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    print("\n" + "=" * 60)
    print("Model Status Check")
    print("=" * 60)
    print(f"Model: {repo_id}\n")
    
    api = HfApi(token=HF_TOKEN)
    try:
        model_info = api.model_info(repo_id)
        
        print(f"✅ Model exists: {model_info.id}")
        print(f"   Private: {model_info.private}")
        print(f"   Pipeline tag: {getattr(model_info, 'pipeline_tag', 'Not set')}")
        
        tags = getattr(model_info, 'tags', [])
        if tags:
            print(f"   Tags: {', '.join(tags[:5])}...")
        
        # Check for README
        files = [f.rfilename if hasattr(f, 'rfilename') else str(f) for f in model_info.siblings]
        has_readme = "README.md" in files
        print(f"   Has README.md: {has_readme}")
        
        print("\n" + "=" * 60)
        print("Inference API Status")
        print("=" * 60)
        
        if model_info.private:
            print("⚠️  Model is PRIVATE")
            print("\nFor private models, the Inference API may need to be enabled manually:")
            print(f"   1. Go to: https://huggingface.co/{repo_id}/settings")
            print("   2. Look for 'Inference API' or 'API' settings")
            print("   3. Enable it if there's an option")
            print("\n   OR wait 10-15 minutes for automatic indexing")
        else:
            print("✅ Model is PUBLIC")
            print("   Should be available on Inference API automatically")
            print("   If not working, wait 5-10 minutes for indexing")
        
        print("\n" + "=" * 60)
        print("Next Steps")
        print("=" * 60)
        
        if model_info.private:
            print("⚠️  IMPORTANT: Private models often don't auto-enable for Inference API")
            print("\n📌 RECOMMENDED: Use a Dedicated Inference Endpoint:")
            print("   1. Go to: https://huggingface.co/inference-endpoints")
            print("   2. Create a new endpoint for your model")
            print("   3. Copy the endpoint URL to your .env file as HF_ENDPOINT_URL")
            print("   4. This works immediately for private models!")
            print("\n   OR make the model public temporarily:")
            print(f"   - Go to: https://huggingface.co/{repo_id}/settings")
            print("   - Change visibility to 'Public'")
            print("   - Wait 2-3 minutes, then test")
            print("   - Can change back to 'Private' after testing")
        else:
            print("1. Wait 5-10 minutes for Hugging Face to index the model")
            print("2. If still not working after 10 minutes, try:")
            print("   - Check model settings for Inference API options")
            print("   - Or use a Dedicated Inference Endpoint")
        
        print("\n📝 Test again:")
        print("   python test_hf_api.py")
        print("\n💡 See enable_inference_api.md for detailed instructions")
        
    except Exception as e:
        print(f"⚠️  Could not check model status: {e}")
        print(f"   Model should be available at: https://huggingface.co/{repo_id}")


def main():
    """Main function."""
    args = parse_args()
    
    # Determine model path (required)
    if args.model_path:
        model_path_str = args.model_path
    else:
        model_path_str = os.getenv("MODEL_PATH")
    
    if not model_path_str:
        raise ValueError(
            "MODEL_PATH is required. Set it in .env file or use --model_path argument.\n"
            "Example: MODEL_PATH=/path/to/merged_model"
        )
    
    model_path_str = os.path.expanduser(model_path_str)
    model_path_str = os.path.expandvars(model_path_str)
    model_path = Path(model_path_str)
    if not model_path.is_absolute():
        model_path = Path(__file__).parent / model_path
    
    # Determine base model (required)
    base_model = args.base_model or os.getenv("BASE_MODEL")
    if not base_model:
        raise ValueError(
            "BASE_MODEL is required. Set it in .env file or use --base_model argument.\n"
            "Example: BASE_MODEL=Qwen/Qwen2.5-Coder-3B-Instruct"
        )
    
    # Determine privacy setting
    if args.public:
        private = False
    elif args.private is not None:
        private = args.private
    else:
        # Read from .env, default to True if not set
        private_str = os.getenv("HF_REPO_PRIVATE", "true").lower()
        private = private_str in ("true", "1", "yes", "on")
    
    # Get repository ID
    HF_USERNAME = os.getenv("HF_USERNAME")
    HF_FINE_TUNED_MODEL_NAME = os.getenv("HF_FINE_TUNED_MODEL_NAME")
    
    if HF_USERNAME and HF_FINE_TUNED_MODEL_NAME:
        repo_id = f"{HF_USERNAME}/{HF_FINE_TUNED_MODEL_NAME}"
    else:
        raise ValueError(
            "REPO_ID could not be constructed. Check HF_USERNAME and HF_FINE_TUNED_MODEL_NAME in .env file"
        )
    
    try:
        validate_config(model_path)
        
        # Upload
        merged_repo_id = upload_merged_model(model_path, base_model, repo_id, private)
        
        print("\n" + "=" * 60)
        print("✅ UPLOAD SUCCESS!")
        print("=" * 60)
        print(f"Your merged model is available at: https://huggingface.co/{merged_repo_id}")
        print(f"\nUpdate your .env file with:")
        print(f"  HF_MODEL_NAME={merged_repo_id}")
        print(f"\n   Or ensure these are set:")
        print(f"  HF_USERNAME={HF_USERNAME}")
        print(f"  HF_FINE_TUNED_MODEL_NAME={HF_FINE_TUNED_MODEL_NAME}")
        
        # Check model status
        check_model_status(merged_repo_id)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

