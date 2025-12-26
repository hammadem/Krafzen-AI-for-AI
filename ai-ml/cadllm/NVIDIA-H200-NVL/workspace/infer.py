import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

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
def generate(prompt: str):
    print("\n================== PROMPT ==================\n")
    print(prompt)
    print("\n================= OUTPUT ===================\n")

    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    output_ids = model.generate(
        **inputs,
        max_new_tokens=400,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
    )

    text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    print(text)
    print("\n============================================\n")
    return text


# ---------------------------
# TEST PROMPT
# ---------------------------
test_prompt = """
You are a CAD code assistant. Produce ezdxf-ready CAD operations 
and enhanced geometry reasoning.

### Instruction
Create a DXF drawing of a 100x50 rectangle with 5mm rounded corners, 
centered at origin. Put it on layer OUTLINE.

### Input
(none)

### Enhanced CAD Prompt (DXF-ready)
"""

generate(test_prompt)
