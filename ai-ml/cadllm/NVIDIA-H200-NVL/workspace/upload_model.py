#!/usr/bin/env python3
"""
Merge LoRA adapter with base model and upload to Hugging Face.

The Hugging Face Inference API requires a full merged model, not just a LoRA adapter.
This script merges the adapter with the base model and uploads it.

Usage:
    python upload_model.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, login
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration
HF_TOKEN = os.getenv("HF_TOKEN")
HF_USERNAME = os.getenv("HF_USERNAME")
HF_FINE_TUNED_MODEL_NAME = os.getenv("HF_FINE_TUNED_MODEL_NAME")
# Adapter path - can be set via ADAPTER_PATH env var or defaults to cad-agent-qwen-2d
ADAPTER_PATH_STR = os.getenv("ADAPTER_PATH")
if ADAPTER_PATH_STR:
    # Expand user home directory (~ or $HOME)
    ADAPTER_PATH_STR = os.path.expanduser(ADAPTER_PATH_STR)
    # Expand environment variables (e.g., $HOME)
    ADAPTER_PATH_STR = os.path.expandvars(ADAPTER_PATH_STR)
    ADAPTER_PATH = Path(ADAPTER_PATH_STR)
    if not ADAPTER_PATH.is_absolute():
        # If relative path, make it relative to script directory
        ADAPTER_PATH = Path(__file__).parent / ADAPTER_PATH
else:
    # Default to cad-agent-qwen-2d in script directory
    ADAPTER_PATH = Path(__file__).parent / "cad-agent-qwen-2d"
BASE_MODEL = os.getenv("BASE_MODEL", "Qwen/Qwen2.5-Coder-3B-Instruct")
PRIVATE = True

# Construct repository ID from username and fine-tuned model name
if HF_USERNAME and HF_FINE_TUNED_MODEL_NAME:
    REPO_ID = f"{HF_USERNAME}/{HF_FINE_TUNED_MODEL_NAME}"
else:
    REPO_ID = None

def generate_model_card(adapter_path: Path, base_model: str, repo_id: str) -> str:
    """
    Generate a model card (README.md) based on the adapter path and model information.
    
    Args:
        adapter_path: Path to the LoRA adapter
        base_model: Base model identifier
        repo_id: Hugging Face repository ID
    
    Returns:
        Model card content as string
    """
    # Check if existing README is a template (contains "[More Information Needed]")
    adapter_readme = adapter_path / "README.md"
    is_template = False
    if adapter_readme.exists():
        existing_content = adapter_readme.read_text(encoding="utf-8")
        # Check if it's a PEFT template
        if "[More Information Needed]" in existing_content or "Model Card for Model ID" in existing_content:
            is_template = True
            print(f"   📄 Found template README.md in adapter path, generating new model card...")
        elif repo_id in existing_content and "base_model" in existing_content.lower():
            # It's a proper model card, use it
            print(f"   📄 Found existing model card in adapter path, using it...")
            return existing_content
        else:
            # It's a custom README but not a template, enhance it
            print(f"   📄 Found custom README.md in adapter path, enhancing it...")
            if repo_id not in existing_content:
                enhanced = f"# {repo_id}\n\n"
                enhanced += f"**Base Model:** {base_model}\n\n"
                enhanced += "---\n\n"
                enhanced += existing_content
                return enhanced
            return existing_content
    
    # Generate new model card (either no README or template detected)
    
    # Generate new model card
    adapter_name = adapter_path.name
    current_date = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    
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
pipeline_tag: text-generation
---

# {repo_id}

Fine-tuned CAD-LLM model for generating 2D CAD coordinates from natural language descriptions.

## Model Details

- **Base Model:** [{base_model}](https://huggingface.co/{base_model})
- **Fine-tuning Method:** LoRA (Low-Rank Adaptation)
- **Adapter Path:** `{adapter_path}`
- **Model Type:** Causal Language Model
- **Language:** English
- **Task:** Text-to-CAD Coordinates Generation

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

## Usage

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

- **Training Data:** CADLLM 2D dataset
- **Training Method:** LoRA fine-tuning
- **Adapter Location:** `{adapter_path}`
- **Training Date:** {current_date}

## Limitations

- Primarily designed for 2D CAD coordinate generation
- May require post-processing to convert coordinates to DXF format
- Best results with clear, specific CAD descriptions

## Citation

If you use this model, please cite:

```bibtex
@misc{{{repo_id.replace("/", "_")}}},
  title={{CAD-LLM: Fine-tuned Model for 2D CAD Coordinate Generation}},
  author={{KRAFZEN AI}},
  year={{2024}},
  publisher={{Hugging Face}},
  howpublished={{\\url{{https://huggingface.co/{repo_id}}}}}
}}
```

## License

This model is licensed under Apache 2.0, same as the base model.
"""
    return model_card

def validate_config():
    """Validate required configuration."""
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN not found in .env file. Please add HF_TOKEN=your_token_here")
    if not HF_USERNAME:
        raise ValueError("HF_USERNAME not found in .env file. Please add HF_USERNAME=your_username")
    if not HF_FINE_TUNED_MODEL_NAME:
        raise ValueError("HF_FINE_TUNED_MODEL_NAME not found in .env file. Please add HF_FINE_TUNED_MODEL_NAME=your_model_name")
    if not REPO_ID:
        raise ValueError("REPO_ID could not be constructed. Check HF_USERNAME and HF_FINE_TUNED_MODEL_NAME in .env file")
    if not ADAPTER_PATH.exists():
        raise ValueError(f"Adapter path not found: {ADAPTER_PATH}")
    
    # Check if adapter path contains adapter_config.json (LoRA adapter) or is a merged model
    adapter_config = ADAPTER_PATH / "adapter_config.json"
    config_json = ADAPTER_PATH / "config.json"
    
    # If not found at root, search recursively
    if not adapter_config.exists() and not config_json.exists():
        print(f"   🔍 'adapter_config.json' or 'config.json' not found at root, searching subdirectories...")
        found_adapters = list(ADAPTER_PATH.rglob("adapter_config.json"))
        found_configs = list(ADAPTER_PATH.rglob("config.json"))
        
        if found_adapters:
            print(f"   ✅ Found {len(found_adapters)} LoRA adapter(s) in subdirectories")
            # Validation passed - adapter exists in subdirectory
        elif found_configs:
            print(f"   ⚠️  Found {len(found_configs)} merged model(s) in subdirectories")
            print(f"   WARNING: Path '{ADAPTER_PATH}' appears to contain merged models, not LoRA adapters.")
            print(f"   This script is designed to merge LoRA adapters. If you want to upload an already-merged model,")
            print(f"   you may need to use a different approach or ensure the path points to a LoRA adapter directory.")
            print(f"   Continuing anyway...")
        else:
            raise ValueError(
                f"Adapter path '{ADAPTER_PATH}' does not contain a valid model.\n"
                f"Expected either:\n"
                f"  - LoRA adapter with 'adapter_config.json'\n"
                f"  - Merged model with 'config.json'\n"
                f"\nSearched recursively but found neither.\n"
                f"Files found in directory:\n"
                f"  {list(ADAPTER_PATH.iterdir())[:10] if ADAPTER_PATH.is_dir() else 'Not a directory'}"
            )
    else:
        # Found at root level
        if config_json.exists() and not adapter_config.exists():
            print(f"⚠️  WARNING: Path '{ADAPTER_PATH}' appears to be a merged model, not a LoRA adapter.")
            print(f"   This script is designed to merge LoRA adapters. If you want to upload an already-merged model,")
            print(f"   you may need to use a different approach or ensure the path points to a LoRA adapter directory.")
            print(f"   Continuing anyway...")

def merge_model():
    """Merge LoRA adapter with base model."""
    print("=" * 60)
    print("Merging LoRA Adapter with Base Model")
    print("=" * 60)
    print(f"Base model: {BASE_MODEL}")
    print(f"Adapter: {ADAPTER_PATH}")
    print(f"Output: {REPO_ID}")
    print()
    
    # Load tokenizer first from adapter (to get the correct vocab size)
    print("📥 Loading tokenizer from adapter...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(ADAPTER_PATH), trust_remote_code=True)
        print(f"   Tokenizer vocab size: {len(tokenizer)}")
    except Exception as e:
        print(f"   ⚠️  Could not load tokenizer from adapter: {e}")
        print("   Falling back to base model tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
        print(f"   Base model tokenizer vocab size: {len(tokenizer)}")
    
    # Load base model with the tokenizer to ensure vocabulary matches
    print("\n📥 Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Resize token embeddings if needed to match tokenizer
    tokenizer_vocab_size = len(tokenizer)
    model_vocab_size = base_model.get_input_embeddings().weight.shape[0]
    
    if tokenizer_vocab_size != model_vocab_size:
        print(f"\n⚠️  Vocabulary size mismatch detected!")
        print(f"   Tokenizer vocab size: {tokenizer_vocab_size}")
        print(f"   Model vocab size: {model_vocab_size}")
        print(f"   Resizing model embeddings to match tokenizer...")
        base_model.resize_token_embeddings(tokenizer_vocab_size)
        print(f"   ✅ Model embeddings resized to {tokenizer_vocab_size}")
    
    print("📥 Loading LoRA adapter...")
    # Check if adapter_config.json exists
    adapter_config = ADAPTER_PATH / "adapter_config.json"
    
    # If not found, try to find it in subdirectories
    actual_adapter_path = ADAPTER_PATH
    if not adapter_config.exists():
        print(f"   ⚠️  'adapter_config.json' not found at '{ADAPTER_PATH}'")
        print(f"   🔍 Searching for adapter in subdirectories...")
        
        # Search for adapter_config.json in subdirectories
        found_adapters = list(ADAPTER_PATH.rglob("adapter_config.json"))
        
        if found_adapters:
            print(f"   ✅ Found {len(found_adapters)} adapter(s):")
            for i, adapter in enumerate(found_adapters, 1):
                print(f"      {i}. {adapter.parent}")
            
            # Use the one in a 'cadllm' subdirectory if exists, otherwise first one
            preferred = None
            for adapter in found_adapters:
                if "cadllm" in str(adapter.parent).lower():
                    preferred = adapter.parent
                    break
            
            if preferred:
                actual_adapter_path = preferred
                print(f"   📌 Using adapter at: {actual_adapter_path}")
            else:
                actual_adapter_path = found_adapters[0].parent
                print(f"   📌 Using first adapter found at: {actual_adapter_path}")
        else:
            raise ValueError(
                f"LoRA adapter not found at '{ADAPTER_PATH}'.\n"
                f"Expected 'adapter_config.json' file in the adapter directory.\n"
                f"\nThis path may contain a merged model instead of a LoRA adapter.\n"
                f"\nTo fix:\n"
                f"  1. Point ADAPTER_PATH to a directory containing 'adapter_config.json'\n"
                f"  2. Or if this is a merged model, you may need to upload it directly without merging\n"
                f"\nFiles found in directory:\n"
                f"  {list(ADAPTER_PATH.iterdir())[:10] if ADAPTER_PATH.is_dir() else 'Not a directory'}"
            )
    else:
        print(f"   ✅ Found adapter_config.json at: {ADAPTER_PATH}")
    
    model = PeftModel.from_pretrained(base_model, str(actual_adapter_path))
    
    print("🔧 Merging adapter with base model...")
    merged_model = model.merge_and_unload()
    
    print("✅ Model merged successfully!")
    return merged_model, tokenizer, actual_adapter_path

def upload_merged_model(merged_model, tokenizer, adapter_path: Path):
    """Upload merged model to Hugging Face Hub."""
    print("\n" + "=" * 60)
    print("Uploading Merged Model to Hugging Face Hub")
    print("=" * 60)
    
    # Login
    print("🔐 Logging in to Hugging Face...")
    login(token=HF_TOKEN)
    
    # Initialize API
    api = HfApi()
    
    # Create repository
    print(f"📦 Creating repository: {REPO_ID}")
    try:
        api.create_repo(
            repo_id=REPO_ID,
            repo_type="model",
            private=PRIVATE,
            exist_ok=True
        )
        print(f"✅ Repository created: https://huggingface.co/{REPO_ID}")
    except Exception as e:
        if "403" in str(e) or "rights" in str(e).lower():
            print(f"❌ Permission denied: {e}")
            print("   Make sure your token has 'Write' permissions")
            raise
        print(f"⚠️  Repository creation: {e}")
    
    # Save model and tokenizer locally first
    print("\n💾 Saving merged model locally...")
    temp_dir = Path(__file__).parent / "merged_model_temp"
    temp_dir.mkdir(exist_ok=True)
    
    merged_model.save_pretrained(str(temp_dir))
    tokenizer.save_pretrained(str(temp_dir))
    
    # Add README.md for proper model recognition
    readme_content = generate_model_card(adapter_path, BASE_MODEL, REPO_ID)
    readme_path = temp_dir / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    print("   ✅ Generated README.md (model card) for model recognition")
    
    # Upload
    print(f"\n📤 Uploading to {REPO_ID}...")
    api.upload_folder(
        folder_path=str(temp_dir),
        repo_id=REPO_ID,
        repo_type="model",
        commit_message="Merged LoRA adapter with base model for Inference API"
    )
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print(f"🧹 Cleaned up temporary files")
    
    print(f"\n✅ Merged model uploaded successfully!")
    print(f"   View at: https://huggingface.co/{REPO_ID}")
    print(f"\n📝 Update your .env file with:")
    print(f"   HF_MODEL_NAME={REPO_ID}")
    print(f"\n   Or construct it from:")
    print(f"   HF_USERNAME={HF_USERNAME}")
    print(f"   HF_FINE_TUNED_MODEL_NAME={HF_FINE_TUNED_MODEL_NAME}")
    return REPO_ID

def check_model_status(repo_id):
    """Check the status of the uploaded model and provide guidance."""
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
    try:
        validate_config()
        
        # Merge model
        merged_model, tokenizer, actual_adapter_path = merge_model()
        
        # Upload
        merged_repo_id = upload_merged_model(merged_model, tokenizer, actual_adapter_path)
        
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

