#!/usr/bin/env python3
"""
Inference script for fine-tuned CAD model (GPU/Cloud testing with direct model loading).

This script loads the model directly on a GPU machine (e.g., cloud instances with CUDA).
It's for testing the model locally on a GPU server, NOT for testing remote APIs.

For different use cases:
- Local Mac testing: use infer_local_mac.py (uses Ollama)
- Remote API testing (HF Space/Inference API): use testing/test_hf_api.py
- Direct model loading on GPU: use this script (infer.py)

This script uses the same Qwen chat template format as training.

Usage:
    python infer.py [prompt] [--adapter_path PATH] [--max_new_tokens N] [--temperature T]
    
    # Example:
    python infer.py "Create a bedroom with a bed and desk"
    python infer.py "Create a kitchen" --adapter_path /workspace/cadllm/checkpoint-21000
"""

import os
import sys
import argparse
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

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


def load_model_and_tokenizer(adapter_dir: Path, base_model: str):
    """
    Load model and tokenizer from adapter directory.
    
    Args:
        adapter_dir: Path to LoRA adapter checkpoint directory
        base_model: Base model identifier
    
    Returns:
        Tuple of (model, tokenizer, device)
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.set_default_device(device)
    
    print(f"\n🔹 Loading tokenizer from: {adapter_dir}")
    tokenizer = AutoTokenizer.from_pretrained(str(adapter_dir), trust_remote_code=True)
    
    # Ensure pad token exists
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    print(f"🔹 Loading base model: {base_model}")
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map=None,
        trust_remote_code=True,
    )
    
    # Resize embeddings to match LoRA tokenizer
    vocab_size = len(tokenizer)
    print(f"🔹 Resizing token embeddings to: {vocab_size}")
    base.resize_token_embeddings(vocab_size)
    
    print(f"🔹 Loading LoRA adapter from: {adapter_dir}")
    model = PeftModel.from_pretrained(base, str(adapter_dir))
    model = model.eval()
    
    print(f"\n✅ Model ready (device: {device}).\n")
    return model, tokenizer, device


def generate(user_prompt: str, model, tokenizer, device, max_new_tokens: int = 400, temperature: float = 0.7):
    """
    Generate CAD DSL format from a user prompt.
    
    Uses the same Qwen chat template format as training.
    
    Args:
        user_prompt: User instruction (e.g., "Create a bedroom with a bed and desk")
        model: Loaded model
        tokenizer: Loaded tokenizer
        device: Device to run on
        max_new_tokens: Maximum tokens to generate
        temperature: Sampling temperature
    """
    # Format as Qwen chat messages (matches training format)
    # Training uses: [system, user, assistant] format
    # For inference, we use: [system, user] with add_generation_prompt=True
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    
    # Apply Qwen chat template (matches training)
    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,  # We'll tokenize separately
        add_generation_prompt=True,  # Add assistant prompt token
    )

    print("\n================== PROMPT ==================\n")
    print(formatted_prompt)
    print("\n================= OUTPUT ===================\n")

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
    
    print(generated)
    print("\n============================================\n")
    return generated


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test CAD-LLM model with direct model loading (GPU/Cloud)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default prompt
  python infer.py
  
  # Custom prompt
  python infer.py "Create a kitchen with sink and stove"
  
  # Override adapter path
  python infer.py "Create a bedroom" --adapter_path /workspace/cadllm/checkpoint-21000
  
  # Adjust generation parameters
  python infer.py "Create a circle" --max_new_tokens 200 --temperature 0.5
        """
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        default=["Create a bedroom with a bed and a desk"],
        help="CAD description prompt (default: 'Create a bedroom with a bed and a desk')"
    )
    parser.add_argument(
        "--adapter_path",
        type=str,
        default=None,
        help="Path to LoRA adapter checkpoint (overrides ADAPTER_PATH from .env)"
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default=None,
        help="Base model identifier (overrides BASE_MODEL from .env)"
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=400,
        help="Maximum tokens to generate (default: 400)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)"
    )
    
    args = parser.parse_args()
    
    # Determine base model
    base_model = args.base_model or os.getenv("BASE_MODEL", "Qwen/Qwen2.5-Coder-3B-Instruct")
    
    # Determine adapter path
    if args.adapter_path:
        adapter_path = Path(args.adapter_path).expanduser().resolve()
    else:
        adapter_path_str = os.getenv("ADAPTER_PATH")
        if not adapter_path_str:
            # Try default server path
            adapter_path_str = "/workspace/cadllm"
            if not Path(adapter_path_str).exists():
                print("❌ Error: ADAPTER_PATH not set in .env file and default path doesn't exist.")
                print("   Please set ADAPTER_PATH in .env file or use --adapter_path argument.")
                print("   Example: ADAPTER_PATH=/workspace/cadllm/checkpoint-21000")
                sys.exit(1)
        
        adapter_path = Path(adapter_path_str).expanduser().expandvars().resolve()
    
    if not adapter_path.exists():
        print(f"❌ Error: Adapter directory does not exist: {adapter_path}")
        sys.exit(1)
    
    # Get prompt
    if isinstance(args.prompt, list):
        test_prompt = " ".join(args.prompt) if args.prompt else "Create a bedroom with a bed and a desk"
    else:
        test_prompt = args.prompt
    
    # Load model
    model, tokenizer, device = load_model_and_tokenizer(adapter_path, base_model)
    
    # Generate
    print(f"📝 Prompt: {test_prompt}\n")
    generate(test_prompt, model, tokenizer, device, 
             max_new_tokens=args.max_new_tokens, 
             temperature=args.temperature)


if __name__ == "__main__":
    main()
