#!/usr/bin/env python3
"""
Merge LoRA adapter with base model.

This script merges a LoRA adapter with the base model to create a full merged model
that can be used for inference or uploaded to Hugging Face.

Usage:
    python merge_model.py [--adapter_path PATH] [--model_output_dir PATH] [--base_model MODEL]
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration from .env (no hardcoded defaults)
# All values must be set in .env file or via command-line arguments


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Merge LoRA adapter with base model"
    )
    parser.add_argument(
        "--adapter_path",
        type=str,
        default=None,
        help="Path to LoRA adapter directory (required: set ADAPTER_PATH env var or use --adapter_path)"
    )
    parser.add_argument(
        "--model_output_dir",
        type=str,
        default=None,
        help="Output directory for merged model (required: set MODEL_OUTPUT_DIR env var or use --model_output_dir)"
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default=None,
        help="Base model identifier (required: set BASE_MODEL env var or use --base_model)"
    )
    return parser.parse_args()


def find_adapter_path(adapter_path: Path) -> Path:
    """
    Find the actual adapter path, searching subdirectories if needed.
    
    Args:
        adapter_path: Initial adapter path to search
        
    Returns:
        Path to the adapter directory containing adapter_config.json
    """
    adapter_config = adapter_path / "adapter_config.json"
    
    # If found at root, return it
    if adapter_config.exists():
        print(f"   ✅ Found adapter_config.json at: {adapter_path}")
        return adapter_path
    
    # Search in subdirectories
    print(f"   ⚠️  'adapter_config.json' not found at '{adapter_path}'")
    print(f"   🔍 Searching for adapter in subdirectories...")
    
    found_adapters = list(adapter_path.rglob("adapter_config.json"))
    
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
        
        return actual_adapter_path
    else:
        raise ValueError(
            f"LoRA adapter not found at '{adapter_path}'.\n"
            f"Expected 'adapter_config.json' file in the adapter directory.\n"
            f"\nThis path may contain a merged model instead of a LoRA adapter.\n"
            f"\nTo fix:\n"
            f"  1. Point --adapter_path to a directory containing 'adapter_config.json'\n"
            f"  2. Or if this is a merged model, it's already ready to use\n"
            f"\nFiles found in directory:\n"
            f"  {list(adapter_path.iterdir())[:10] if adapter_path.is_dir() else 'Not a directory'}"
        )


def merge_model(adapter_path: Path, model_output_dir: Path, base_model: str):
    """
    Merge LoRA adapter with base model.
    
    Args:
        adapter_path: Path to LoRA adapter directory
        model_output_dir: Output directory for merged model
        base_model: Base model identifier
    """
    print("=" * 60)
    print("Merging LoRA Adapter with Base Model")
    print("=" * 60)
    print(f"Base model: {base_model}")
    print(f"Adapter: {adapter_path}")
    print(f"Output: {model_output_dir}")
    print()
    
    # Validate adapter path exists
    if not adapter_path.exists():
        # Check if there are checkpoint directories in the parent
        parent_dir = adapter_path.parent
        if parent_dir.exists():
            checkpoints = [d for d in parent_dir.iterdir() if d.is_dir() and d.name.startswith("checkpoint-")]
            if checkpoints:
                checkpoints.sort(key=lambda x: int(x.name.split("-")[1]) if x.name.split("-")[1].isdigit() else 0)
                latest = checkpoints[-1]
                raise ValueError(
                    f"Adapter path does not exist: {adapter_path}\n\n"
                    f"💡 Found checkpoint directories in {parent_dir}:\n"
                    f"   Latest: {latest.name}\n"
                    f"   All: {', '.join([c.name for c in checkpoints[-5:]])}\n\n"
                    f"Try using a checkpoint directory:\n"
                    f"  python merge_model.py --adapter_path {latest}\n"
                    f"  Or: make merge-model ADAPTER_PATH={latest.name}"
                )
        raise ValueError(
            f"Adapter path does not exist: {adapter_path}\n\n"
            f"💡 Make sure the adapter path points to a directory containing 'adapter_config.json'\n"
            f"   This could be:\n"
            f"   - A checkpoint directory (e.g., checkpoint-21000)\n"
            f"   - The final model output directory\n"
            f"   - A LoRA adapter directory"
        )
    
    # Find actual adapter path (may be in subdirectory)
    actual_adapter_path = find_adapter_path(adapter_path)
    
    # Load tokenizer first from adapter (to get the correct vocab size)
    print("📥 Loading tokenizer from adapter...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(actual_adapter_path), trust_remote_code=True)
        print(f"   Tokenizer vocab size: {len(tokenizer)}")
    except Exception as e:
        print(f"   ⚠️  Could not load tokenizer from adapter: {e}")
        print("   Falling back to base model tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
        print(f"   Base model tokenizer vocab size: {len(tokenizer)}")
    
    # Load base model with the tokenizer to ensure vocabulary matches
    print("\n📥 Loading base model...")
    # Use device_map=None to avoid wrapping issues with PEFT
    # Determine device and dtype
    device = "cuda" if torch.cuda.is_available() else "cpu"
    bf16_supported = (
        torch.cuda.is_available()
        and hasattr(torch.cuda, "is_bf16_supported")
        and torch.cuda.is_bf16_supported()
    )
    dtype = torch.bfloat16 if bf16_supported else torch.float16
    
    base_model_obj = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=dtype,
        device_map=None,  # Don't use auto to avoid wrapping issues
        trust_remote_code=True
    )
    
    # Move model to device manually
    base_model_obj = base_model_obj.to(device)
    print(f"   Model loaded on device: {device}, dtype: {dtype}")
    
    # Resize token embeddings if needed to match tokenizer
    tokenizer_vocab_size = len(tokenizer)
    model_vocab_size = base_model_obj.get_input_embeddings().weight.shape[0]
    
    if tokenizer_vocab_size != model_vocab_size:
        print(f"\n⚠️  Vocabulary size mismatch detected!")
        print(f"   Tokenizer vocab size: {tokenizer_vocab_size}")
        print(f"   Model vocab size: {model_vocab_size}")
        print(f"   Resizing model embeddings to match tokenizer...")
        base_model_obj.resize_token_embeddings(tokenizer_vocab_size)
        print(f"   ✅ Model embeddings resized to {tokenizer_vocab_size}")
    
    print("📥 Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base_model_obj, str(actual_adapter_path))
    
    print("🔧 Merging adapter with base model...")
    merged_model = model.merge_and_unload()
    
    print("💾 Saving merged model...")
    model_output_dir.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(str(model_output_dir))
    tokenizer.save_pretrained(str(model_output_dir))
    
    print(f"✅ Model merged and saved successfully to: {model_output_dir}")
    return merged_model, tokenizer


def main():
    """Main function."""
    args = parse_args()
    
    # Determine adapter path (required)
    if args.adapter_path:
        adapter_path_str = args.adapter_path
    else:
        adapter_path_str = os.getenv("ADAPTER_PATH")
    
    if not adapter_path_str:
        # Try to find latest checkpoint as fallback
        workspace_dir = Path(__file__).parent
        checkpoints = [d for d in workspace_dir.iterdir() 
                      if d.is_dir() and d.name.startswith("checkpoint-")]
        if checkpoints:
            checkpoints.sort(key=lambda x: int(x.name.split("-")[1]) if x.name.split("-")[1].isdigit() else 0)
            adapter_path = checkpoints[-1]
            print(f"💡 ADAPTER_PATH not set, using latest checkpoint: {adapter_path.name}")
        else:
            raise ValueError(
                "ADAPTER_PATH is required. Set it in .env file or use --adapter_path argument.\n"
                "Example: ADAPTER_PATH=/path/to/adapter or ADAPTER_PATH=checkpoint-21000"
            )
    else:
        adapter_path_str = os.path.expanduser(adapter_path_str)
        adapter_path_str = os.path.expandvars(adapter_path_str)
        adapter_path = Path(adapter_path_str)
        if not adapter_path.is_absolute():
            adapter_path = Path(__file__).parent / adapter_path
    
    # Determine output directory (required)
    if args.model_output_dir:
        model_output_dir_str = args.model_output_dir
    else:
        model_output_dir_str = os.getenv("MODEL_OUTPUT_DIR")
    
    if not model_output_dir_str:
        raise ValueError(
            "MODEL_OUTPUT_DIR is required. Set it in .env file or use --model_output_dir argument.\n"
            "Example: MODEL_OUTPUT_DIR=/path/to/merged_model"
        )
    
    model_output_dir_str = os.path.expanduser(model_output_dir_str)
    model_output_dir_str = os.path.expandvars(model_output_dir_str)
    model_output_dir = Path(model_output_dir_str)
    if not model_output_dir.is_absolute():
        model_output_dir = Path(__file__).parent / model_output_dir
    
    # Determine base model (required)
    base_model = args.base_model or os.getenv("BASE_MODEL")
    if not base_model:
        raise ValueError(
            "BASE_MODEL is required. Set it in .env file or use --base_model argument.\n"
            "Example: BASE_MODEL=Qwen/Qwen2.5-Coder-3B-Instruct"
        )
    
    try:
        merge_model(adapter_path, model_output_dir, base_model)
        
        print("\n" + "=" * 60)
        print("✅ MERGE SUCCESS!")
        print("=" * 60)
        print(f"Merged model saved to: {model_output_dir}")
        print(f"\nYou can now upload it with:")
        print(f"  python upload_model.py --model_path {model_output_dir}")
        print(f"\nOr use the Makefile target:")
        print(f"  make upload-model MODEL_PATH={model_output_dir}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

