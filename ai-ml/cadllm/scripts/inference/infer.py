#!/usr/bin/env python3
"""
Inference script for fine-tuned CAD model (GPU/Cloud testing).

This script is for testing on GPU machines (e.g., cloud instances with CUDA).
For local Mac testing, use infer_local_mac.py which uses Ollama.

This script uses the same Qwen chat template format as training.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

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
# CONFIG
# ---------------------------
BASE_MODEL = "Qwen/Qwen2.5-Coder-3B-Instruct"
ADAPTER_DIR = "/workspace/cad-agent-qwen-full"

device = "cuda" if torch.cuda.is_available() else "cpu"
torch.set_default_device(device)

# ---------------------------
# LOAD TOKENIZER
# ---------------------------
print("\n🔹 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR, trust_remote_code=True)

# Ensure pad token exists
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# ---------------------------
# LOAD BASE MODEL
# ---------------------------
print("🔹 Loading base model...")
base = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map=None,
    trust_remote_code=True,
)

# Resize embeddings to match LoRA tokenizer
vocab_size = len(tokenizer)
print(f"🔹 Resizing token embeddings to: {vocab_size}")
base.resize_token_embeddings(vocab_size)

# ---------------------------
# LOAD LORA ADAPTER
# ---------------------------
print("🔹 Loading LoRA adapter...")
model = PeftModel.from_pretrained(base, ADAPTER_DIR)
model = model.eval()

print("\n✅ Model ready.\n")


# ---------------------------
# GENERATION FUNCTION
# ---------------------------
def generate(user_prompt: str, max_new_tokens: int = 400, temperature: float = 0.7):
    """
    Generate CAD coordinates from a user prompt.
    
    Uses the same Qwen chat template format as training.
    
    Args:
        user_prompt: User instruction (e.g., "Create a bedroom with a bed and desk")
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


# ---------------------------
# TEST PROMPT
# ---------------------------
if __name__ == "__main__":
    test_prompt = "Create a bedroom with a bed and a desk"
    generate(test_prompt)
