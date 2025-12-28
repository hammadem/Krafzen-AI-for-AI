# Inference Scripts

This folder contains scripts for running inference (generation) with the fine-tuned CAD-LLM model.

## Scripts

### `infer.py`
**Purpose**: Direct model loading for GPU/Cloud environments

Loads the model directly on a GPU machine (e.g., cloud instances with CUDA) for testing the model locally on a GPU server.

**Usage**:
```bash
# Use defaults from .env
python infer.py

# Custom prompt
python infer.py "Create a kitchen with sink and stove"

# Override adapter path
python infer.py "Create a bedroom" --adapter_path /workspace/cadllm/checkpoint-21000

# Adjust generation parameters
python infer.py "Create a circle" --max_new_tokens 200 --temperature 0.5
```

**Configuration** (via `.env`):
- `ADAPTER_PATH`: Path to LoRA adapter checkpoint directory
- `BASE_MODEL`: Base model identifier (default: `Qwen/Qwen2.5-Coder-3B-Instruct`)

**Command-line Arguments**:
- `prompt`: CAD description prompt (positional)
- `--adapter_path`: Override `ADAPTER_PATH` from `.env`
- `--base_model`: Override `BASE_MODEL` from `.env`
- `--max_new_tokens`: Maximum tokens to generate (default: 400)
- `--temperature`: Sampling temperature (default: 0.7)

**When to Use**:
- Testing on GPU servers/cloud instances
- Direct model loading without API overhead
- Debugging model behavior with full control

---

### `infer_local_mac.py`
**Purpose**: Local inference on Mac using Ollama

Uses Ollama's HTTP API for local inference on Mac. Offloads model management to Ollama, making it simpler than direct model loading.

**Usage**:
```bash
# Use defaults from .env
python infer_local_mac.py

# Custom prompt
python infer_local_mac.py "Create a bedroom with a bed and desk"
```

**Configuration** (via `.env`):
- `OLLAMA_MODEL_NAME`: Ollama model name (default: `cadllm`)
- `OLLAMA_BASE_URL`: Ollama server URL (default: `http://localhost:11434`)

**Prerequisites**:
1. Ollama installed and running
2. Model deployed to Ollama: `make deploy-ollama`

**When to Use**:
- Local testing on Mac
- Quick inference without GPU
- Testing Ollama deployment

---

## Testing

For API testing (Hugging Face Inference API, Space API, or Ollama), see the `testing/` folder.

## Output Format

Both scripts generate output in DSL format:
```
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=3000 h=3000 center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
BED: rect w=1500 h=2000 center=(0,-500) layer=FURNITURE closed=true anchor_wall=south
```

This DSL output can be converted to DXF using `utils/dsl_parser.py`.

