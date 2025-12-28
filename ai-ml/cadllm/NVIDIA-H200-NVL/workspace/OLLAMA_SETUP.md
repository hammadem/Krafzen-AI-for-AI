# Running CAD-LLM Model Locally with Ollama

This guide explains how to run your fine-tuned CAD model locally on your Mac using Ollama.

## Important Note

**Ollama requires models in GGUF format**, which is different from the PyTorch format your model is currently in. You have two options:

1. **Use the Python inference script** (Recommended for Mac) - Works immediately, no conversion needed
2. **Convert to GGUF and use Ollama** - More complex but integrates with Ollama ecosystem

**Note:** The model outputs **DSL format** (not coordinate format), which can be converted to DXF using `dsl_parser.py`.

## Option 1: Python Inference Script (Easiest)

The easiest way to run your model locally on Mac is using the provided Python script:

### Setup

1. **Install dependencies:**
```bash
cd ai-ml/cadllm/NVIDIA-H200-NVL/workspace
pip install -r requirements.txt
```

2. **Set up .env file:**
```bash
# Create .env file in workspace directory
cat > .env << EOF
BASE_MODEL=Qwen/Qwen2.5-Coder-3B-Instruct
ADAPTER_PATH=~/Projects/models/cadllm
EOF
```

3. **Run inference:**
```bash
python infer_local_mac.py "Create a circle with radius 10mm"
```

**Performance:**
- **Apple Silicon (M1/M2/M3)**: Uses MPS acceleration, reasonably fast
- **Intel Mac**: Uses CPU, slower but works
- **Memory**: Requires ~6-8GB RAM for the 3B model

### Using the Script

```bash
# With a prompt
python infer_local_mac.py "Create a rectangle 100mm x 50mm"

# Interactive mode (uses default test prompt)
python infer_local_mac.py
```

## Option 2: Using Ollama (Advanced)

To use Ollama, you need to convert your merged model to GGUF format. This is a multi-step process:

### Step 1: Merge Your Model

First, ensure you have a merged model (not just LoRA adapter):

```bash
make merge-model
# Or manually:
python merge_model.py
```

### Step 2: Convert to GGUF Format

You'll need to use `llama.cpp` tools to convert the model:

1. **Install llama.cpp:**
```bash
# Option 1: Homebrew (recommended)
brew install llama.cpp

# Option 2: From source (uses CMake)
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
mkdir build && cd build
cmake ..
cmake --build .
cd ..  # Go back to llama.cpp root directory
```

**After building from source**, add to your `.env` file:
```bash
LLAMA_CPP_PATH=/path/to/llama.cpp
```

**Important:** Point `LLAMA_CPP_PATH` to the **root** of the cloned llama.cpp directory (where `convert_hf_to_gguf.py` is located), not the `build` subdirectory.

2. **Convert PyTorch model to GGUF:**
```bash
# Install python dependencies for conversion
pip install transformers accelerate

# Convert (this is a complex process - you may need to adapt based on your model)
python convert-hf-to-gguf.py \
    --outdir ./gguf-models \
    --outfile cadllm.gguf \
    /path/to/merged_model \
    --outtype f16
```

**Note:** The exact conversion process depends on your model architecture. Qwen models may require specific conversion scripts.

### Step 3: Create Ollama Modelfile

Create a `Modelfile`:

```
FROM /path/to/cadllm.gguf

SYSTEM """You are a CAD code assistant. Given a simple CAD description, 
output ONLY the strict DSL format shown below. Do not use natural language.

Required DSL Format (STRICT - must match exactly):
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=WIDTH h=HEIGHT center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
OBJECT_NAME: rect w=WIDTH h=HEIGHT center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL
OBJECT_NAME: circle r=RADIUS center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL

Rules:
- Always start with UNITS, ORIGIN_POLICY, ROOM, WALLS (in that order)
- Use rect or circle primitives only
- Entity names must use underscores (e.g., COFFEE_TABLE not COFFEE TABLE)
- anchor_wall must be: north, south, east, west, or none (for free placement)
- All coordinates in mm, room centered at (0,0)
- All objects must be within room bounds
- Use circle for round objects (burners, round tables, columns)
- Use rect for rectangular objects (tables, desks, appliances)

Default dimensions if not specified:
- Rooms: 3000x3000 (bedroom), 4000x3000 (kitchen), 2000x2000 (bathroom)
- Simple shapes: r=100 (circles), 200x200 (squares), 300x200 (rectangles)
"""

# Note: Ollama should automatically use Qwen's chat template format for Qwen models
# If your model is based on Qwen, the template will be handled automatically
# You may not need a custom TEMPLATE parameter

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 400
```

**Important Notes:**
- The SYSTEM prompt matches the training format exactly (from `train_qwen.py`)
- Ollama should automatically apply Qwen's chat template (`<|im_start|>system`, `<|im_start|>user`, etc.) for Qwen-based models
- If Ollama doesn't automatically detect Qwen format, you may need to check Ollama's documentation for Qwen-specific template handling
- The model outputs **DSL format** (UNITS: mm, ROOM: rect..., etc.), not coordinate format
- You can convert DSL output to DXF using `dsl_parser.py` (see main README)

### Step 4: Create Ollama Model

```bash
ollama create cadllm -f Modelfile
```

### Step 5: Use the Model

```bash
ollama run cadllm "Create a circle with radius 10mm"
```

## Recommendation

**For Mac users, I recommend using the Python inference script (`infer_local_mac.py`)** because:

1. ✅ **No conversion needed** - Works directly with your PyTorch model
2. ✅ **Uses Apple Silicon acceleration** (MPS) if available
3. ✅ **Simpler setup** - Just install requirements and run
4. ✅ **Full control** - Easy to modify prompts and parameters
5. ✅ **Works with LoRA adapters** - No need to merge first (though merging is faster)

The Ollama approach is better if you:
- Want to integrate with other Ollama-based tools
- Need the model to be accessible via Ollama's API
- Want to use Ollama's model management features

## Performance Tips for Mac

1. **Use merged model** - Merging the LoRA adapter first will be faster than loading adapter each time
2. **Reduce precision** - The script automatically uses float16 on MPS for better performance
3. **Close other apps** - Free up RAM for better performance
4. **Use shorter prompts** - Reduces memory usage

## Troubleshooting

### Out of Memory

If you get out of memory errors:
- Close other applications
- Use a smaller model if available
- Reduce `max_new_tokens` parameter
- Use CPU instead of MPS (slower but uses less memory)

### Slow Performance

- Ensure you're using MPS on Apple Silicon (check the output message)
- Consider using the Hugging Face Inference API instead (works great on Mac, no local resources needed)

### Model Not Found

Make sure your `ADAPTER_PATH` in `.env` points to the correct directory containing `adapter_config.json`.

