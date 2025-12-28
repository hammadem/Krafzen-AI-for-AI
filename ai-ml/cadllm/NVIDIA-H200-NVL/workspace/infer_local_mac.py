#!/usr/bin/env python3
"""
Local inference script for Mac (CPU or MPS).

This script runs the fine-tuned CAD model locally on your Mac.
It works with both CPU and Apple Silicon (MPS) acceleration.

Usage:
    python infer_local_mac.py
    python infer_local_mac.py "Create a circle with radius 10mm"
"""

import os
import sys
import torch
from pathlib import Path
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration from .env
BASE_MODEL = os.getenv("BASE_MODEL")
if not BASE_MODEL:
    raise ValueError(
        "BASE_MODEL not set in .env file.\n"
        "Please set BASE_MODEL (e.g., Qwen/Qwen2.5-Coder-3B-Instruct)"
    )

MODEL_PATH = os.getenv("MODEL_PATH")  # For merged models
ADAPTER_PATH = os.getenv("ADAPTER_PATH")  # For LoRA adapters

if not MODEL_PATH and not ADAPTER_PATH:
    raise ValueError(
        "Either MODEL_PATH or ADAPTER_PATH must be set in .env file.\n"
        "  MODEL_PATH: Path to merged model (faster, recommended)\n"
        "  ADAPTER_PATH: Path to LoRA adapter (slower, requires base model download)"
    )

# Expand paths
if MODEL_PATH:
    MODEL_PATH = os.path.expanduser(MODEL_PATH)
    MODEL_PATH = os.path.expandvars(MODEL_PATH)
    MODEL_PATH = Path(MODEL_PATH)
    if not MODEL_PATH.is_absolute():
        MODEL_PATH = Path(__file__).parent / MODEL_PATH
    USE_MERGED = True
else:
    ADAPTER_PATH = os.path.expanduser(ADAPTER_PATH)
    ADAPTER_PATH = os.path.expandvars(ADAPTER_PATH)
    ADAPTER_PATH = Path(ADAPTER_PATH)
    if not ADAPTER_PATH.is_absolute():
        ADAPTER_PATH = Path(__file__).parent / ADAPTER_PATH
    USE_MERGED = False

# Determine device
# Note: MPS has limitations with large models (2^32 bytes limit)
# For 3B models, CPU may be more reliable
use_mps = False
if torch.backends.mps.is_available():
    # Check if we should use MPS (can be disabled via env var)
    if os.getenv("USE_MPS", "false").lower() == "true":
        use_mps = True
        device = "mps"
        print("🍎 Using Apple Silicon (MPS) acceleration")
    else:
        device = "cpu"
        print("💻 Using CPU (MPS disabled by default for stability)")
        print("   To enable MPS, set USE_MPS=true in .env file")
elif torch.cuda.is_available():
    device = "cuda"
    print("🚀 Using CUDA GPU")
else:
    device = "cpu"
    print("💻 Using CPU")

# Determine dtype based on device
if device == "mps":
    # MPS doesn't support bfloat16, use float16
    # But MPS has memory limitations, so we'll try CPU first
    dtype = torch.float16
elif device == "cuda":
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
else:
    dtype = torch.float32  # CPU works best with float32

print(f"   Device: {device}, dtype: {dtype}\n")

# ---------------------------
# LOAD MODEL
# ---------------------------
if USE_MERGED:
    # Load merged model directly (faster)
    print("📥 Loading merged model...")
    print(f"   Model: {MODEL_PATH}")
    
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH), trust_remote_code=True)
    # Load on CPU first to avoid MPS memory issues
    load_dtype = torch.float32  # Always load in float32 first
    model = AutoModelForCausalLM.from_pretrained(
        str(MODEL_PATH),
        torch_dtype=load_dtype,
        device_map=None,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    
    # Try to move to device, with fallback to CPU if MPS fails
    if device == "mps":
        try:
            model = model.to(device)
            # Convert to float16 after moving to MPS
            model = model.to(dtype)
        except (RuntimeError, AssertionError) as e:
            if "MPS" in str(e) or "NDArray" in str(e) or "2**32" in str(e):
                print(f"   ⚠️  MPS memory limit exceeded, falling back to CPU")
                device = "cpu"
                dtype = torch.float32
                # Model is already on CPU, just ensure dtype
                model = model.to(dtype)
            else:
                raise
    else:
        model = model.to(device)
        if device != "cpu":
            model = model.to(dtype)
    
    model = model.eval()
else:
    # Load base model + LoRA adapter
    print("📥 Loading tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(ADAPTER_PATH), trust_remote_code=True)
        print(f"   ✅ Tokenizer loaded from adapter")
    except Exception as e:
        print(f"   ⚠️  Could not load tokenizer from adapter: {e}")
        print("   Falling back to base model tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
        print(f"   ✅ Tokenizer loaded from base model")
    
    print("\n📥 Loading base model (this may take a few minutes)...")
    print(f"   Model: {BASE_MODEL}")
    print(f"   This is a one-time download if not cached")
    
    # For MPS, we need to be careful about memory limits
    # Load on CPU first, then move to device if needed
    load_device = "cpu" if device == "mps" else device
    load_dtype = torch.float32 if device == "mps" else dtype
    
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=load_dtype,
        device_map=None,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    
    # Try to move to MPS, but fallback to CPU if it fails
    if device == "mps":
        try:
            base_model = base_model.to(device)
            # Convert to float16 after moving to MPS
            base_model = base_model.to(dtype)
        except (RuntimeError, AssertionError) as e:
            if "MPS" in str(e) or "NDArray" in str(e) or "2**32" in str(e):
                print(f"   ⚠️  MPS memory limit exceeded, falling back to CPU")
                device = "cpu"
                dtype = torch.float32
                base_model = base_model.to(device)
            else:
                raise
    else:
        base_model = base_model.to(device)
    
    # Resize embeddings to match tokenizer
    vocab_size = len(tokenizer)
    if base_model.get_input_embeddings().weight.shape[0] != vocab_size:
        print(f"   Resizing token embeddings to match tokenizer: {vocab_size}")
        base_model.resize_token_embeddings(vocab_size)
    
    print("\n📥 Loading LoRA adapter...")
    print(f"   Adapter: {ADAPTER_PATH}")
    
    # Find adapter if in subdirectory
    adapter_config = ADAPTER_PATH / "adapter_config.json"
    if not adapter_config.exists():
        found_adapters = list(ADAPTER_PATH.rglob("adapter_config.json"))
        if found_adapters:
            actual_adapter_path = found_adapters[0].parent
            print(f"   Found adapter in subdirectory: {actual_adapter_path.name}")
        else:
            raise ValueError(f"LoRA adapter not found at {ADAPTER_PATH}")
    else:
        actual_adapter_path = ADAPTER_PATH
    
    model = PeftModel.from_pretrained(base_model, str(actual_adapter_path))
    model = model.eval()
    
    # Move to device (with fallback for MPS)
    if device == "mps":
        try:
            model = model.to(device)
        except (RuntimeError, AssertionError) as e:
            if "MPS" in str(e) or "NDArray" in str(e) or "2**32" in str(e):
                print(f"   ⚠️  MPS memory limit exceeded, using CPU instead")
                device = "cpu"
                dtype = torch.float32
                model = model.to(device)
            else:
                raise
    else:
        model = model.to(device)

# Ensure pad token exists
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

print("\n✅ Model ready for inference!\n")

# ---------------------------
# SYSTEM PROMPT (matches training)
# ---------------------------
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


# ---------------------------
# GENERATION FUNCTION
# ---------------------------
def generate(prompt: str, max_new_tokens: int = 400, temperature: float = 0.7):
    """
    Generate CAD coordinates from a prompt.
    
    Args:
        prompt: User instruction (e.g., "Create a circle with radius 10mm")
        max_new_tokens: Maximum tokens to generate
        temperature: Sampling temperature (lower = more deterministic)
    """
    # Format as Qwen chat messages (matches training format)
    # Training uses: [system, user, assistant] format
    # For inference, we use: [system, user] with add_generation_prompt=True
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    
    # Apply Qwen chat template (matches training)
    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,  # We'll tokenize separately
        add_generation_prompt=True,  # Add assistant prompt token
    )

    print("=" * 60)
    print("PROMPT:")
    print("=" * 60)
    print(formatted_prompt)
    print("=" * 60)
    print("\n🔄 Generating...\n")

    # Tokenize (this adds special tokens by default)
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(device)
    prompt_len = inputs["input_ids"].shape[1]

    # Generate
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # Extract only the generated part (after the prompt)
    # Decode only the generated tokens (after prompt)
    generated_ids = output_ids[0][prompt_len:]
    generated = tokenizer.decode(generated_ids, skip_special_tokens=True)

    print("=" * 60)
    print("OUTPUT:")
    print("=" * 60)
    print(generated)
    print("=" * 60)
    
    return generated


# ---------------------------
# MAIN
# ---------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use command-line argument as prompt
        prompt = " ".join(sys.argv[1:])
    else:
        # Default test prompt
        prompt = "Create a circle with radius 10mm centered at origin"
    
    try:
        generate(prompt)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

