# API Testing Scripts

This folder contains scripts for testing the CAD-LLM model via various APIs (Hugging Face Inference API, Space API, and Ollama).

## Scripts

### `test_hf_api.py`
**Purpose**: Test CAD-LLM model inference via multiple methods

Tests the model using one of:
- Hugging Face Inference API (default, for cloud/remote testing)
- Hugging Face Space API (for testing deployed Space)
- Ollama (for local testing on Mac)

**Usage**:
```bash
# Test with Hugging Face Inference API (default)
python test_hf_api.py

# Test with Hugging Face Space API
python test_hf_api.py --space

# Test with Ollama (local)
python test_hf_api.py --ollama

# Custom prompt with Space API
python test_hf_api.py --space "Create a kitchen with sink and stove"

# Custom prompt with Inference API
python test_hf_api.py "Create a rectangle 50x30mm"
```

**Configuration** (via `.env`):

For **Hugging Face Inference API**:
- `HF_TOKEN`: Your Hugging Face token (required)
- `HF_MODEL_NAME`: Model identifier (e.g., `username/model-name`)
  - OR use `HF_USERNAME` + `HF_FINE_TUNED_MODEL_NAME`
- `HF_ENDPOINT_URL`: Optional custom endpoint URL

For **Hugging Face Space API**:
- `HF_SPACE_REPO`: Space repository (e.g., `username/space-name`)
  - OR `HF_SPACE_URL`: Direct Space URL (e.g., `https://username-space-name.hf.space`)

For **Ollama**:
- `OLLAMA_MODEL_NAME`: Ollama model name (default: `cadllm`)
- `OLLAMA_BASE_URL`: Ollama server URL (default: `http://localhost:11434`)

**Command-line Arguments**:
- `--space`: Use Hugging Face Space API instead of Inference API
- `--ollama`: Use Ollama for local inference
- `prompt`: Custom prompt (optional, positional)

**Examples**:
```bash
# Test Inference API with default prompt
python test_hf_api.py

# Test Space API with custom prompt
python test_hf_api.py --space "Create a bedroom with bed and desk"

# Test Ollama locally
python test_hf_api.py --ollama "Create a circle with radius 10mm"
```

**Prerequisites**:

For **Inference API**:
- Valid `HF_TOKEN` with access to the model
- Model uploaded to Hugging Face Hub

For **Space API**:
- Space deployed to Hugging Face (see `deployment/` folder)
- Space must be running (not building)

For **Ollama**:
- Ollama installed and running
- Model deployed: `make deploy-ollama`

**Troubleshooting**:

1. **Inference API errors**:
   - Verify `HF_TOKEN` is valid
   - Check model exists: `https://huggingface.co/{HF_MODEL_NAME}`
   - Ensure token has access to private models

2. **Space API connection errors**:
   - Check Space is deployed and running
   - Verify Space URL is correct
   - Wait for Space to finish building

3. **Ollama errors**:
   - Ensure Ollama is running: `ollama serve`
   - Check model exists: `ollama list`
   - Deploy model if missing: `make deploy-ollama`

## Output Format

The script outputs the generated DSL format:
```
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=3000 h=3000 center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
...
```

This can be converted to DXF using `utils/dsl_parser.py`.

