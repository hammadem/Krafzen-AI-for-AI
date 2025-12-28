# Deployment Scripts

This folder contains scripts for deploying the CAD-LLM model to various platforms: Ollama (local) and Hugging Face Spaces (cloud).

## Scripts

### `deploy_ollama.py`
**Purpose**: Deploy merged model to Ollama for local inference

Converts the merged Hugging Face model to GGUF format and deploys it to Ollama for local inference on Mac or other systems.

**Usage**:
```bash
# Use defaults from .env
python deploy_ollama.py

# Specify model path
python deploy_ollama.py --model_path ./merged_model
```

**Configuration** (via `.env`):
- `MODEL_PATH` (or `MODEL_OUTPUT_DIR`): Path to merged model directory
- `LLAMA_CPP_PATH`: Path to `llama.cpp` root directory (required)
- `GGUF_OUTPUT_DIR`: Directory for GGUF output (default: `./gguf_output`)
- `OLLAMA_MODEL_NAME`: Name for Ollama model (default: `cadllm`)

**Prerequisites**:
1. **llama.cpp installed**:
   ```bash
   git clone https://github.com/ggerganov/llama.cpp.git
   cd llama.cpp
   mkdir build && cd build
   cmake .. && cmake --build .
   ```
   Set `LLAMA_CPP_PATH` to the root of the cloned directory.

2. **Ollama installed**: https://ollama.ai

3. **Dependencies**: `numpy` (for conversion)

**Makefile Target**:
```bash
make deploy-ollama
```

**Process**:
1. Converts Hugging Face model to GGUF format using `llama.cpp`
2. Creates Ollama Modelfile with Qwen chat template
3. Deploys model to Ollama using `ollama create`

**Output**:
- GGUF model file in `GGUF_OUTPUT_DIR`
- Ollama model available as `OLLAMA_MODEL_NAME`

**Testing**:
After deployment, test with:
```bash
# Using Ollama CLI
ollama run cadllm "Create a bedroom with bed and desk"

# Using testing script
python testing/test_hf_api.py --ollama "Create a bedroom"
```

---

### `deploy_space.py`
**Purpose**: Deploy Space app to Hugging Face Spaces

Deploys the Space application (FastAPI) to Hugging Face Spaces for cloud inference.

**Usage**:
```bash
# Use defaults from .env
python deploy_space.py

# Specify Space directory
python deploy_space.py --space_dir ./space/cad-llm-api
```

**Configuration** (via `.env`):
- `HF_SPACE_REPO`: Space repository (format: `username/space-name`)
- `HF_TOKEN`: Hugging Face authentication token (required)
- `HF_MODEL_NAME`: Model identifier for Space to load

**Prerequisites**:
1. **Hugging Face account** with valid token
2. **Model uploaded** to Hugging Face Hub
3. **Space directory** prepared (see `space/cad-llm-api/`)

**Makefile Target**:
```bash
make deploy-space
```

**Process**:
1. Validates Space directory structure
2. Creates Space repository if it doesn't exist
3. Detects Space SDK type (docker, gradio, etc.)
4. Pushes Space files to Hugging Face repository
5. Triggers Space build and deployment

**Features**:
- Automatic repository creation
- SDK type detection
- Dynamic git repository (no embedded .git)
- Error handling and validation

**Output**:
- Space deployed to: `https://huggingface.co/spaces/{HF_SPACE_REPO}`
- API endpoint: `https://{username}-{space-name}.hf.space/generate`

**Testing**:
After deployment, test with:
```bash
# Using testing script
python testing/test_hf_api.py --space "Create a bedroom"
```

---

## Space Application

The Space application is located in `space/cad-llm-api/`:
- `app.py`: FastAPI application with `/generate` endpoint
- `Dockerfile`: Container configuration
- `requirements.txt`: Python dependencies
- `README.md`: Space documentation

**API Endpoint**:
```bash
POST /generate
Content-Type: application/json

{
  "instruction": "Create a bedroom with bed and desk",
  "max_new_tokens": 400,
  "temperature": 0.7,
  "top_p": 0.9
}
```

**Response**:
```json
{
  "output": "UNITS: mm\nORIGIN_POLICY: room_center_at_(0,0)\n...",
  "model": "Qwen/Qwen2.5-Coder-3B-Instruct",
  "device": "cuda"
}
```

## Deployment Workflow

1. **Train Model**: Use `training/train_qwen.py`
2. **Merge Model**: Use `model_management/merge_model.py`
3. **Upload Model**: Use `model_management/upload_model.py`
4. **Deploy**:
   - **Ollama** (local): `make deploy-ollama`
   - **Space** (cloud): `make deploy-space`
5. **Test**: Use `testing/test_hf_api.py`

## Ollama Management

Additional Makefile targets for managing Ollama:

```bash
# Start Ollama server
make ollama-start

# Stop Ollama server
make ollama-stop

# Start Ollama + Open WebUI
make ollama-start-all

# Stop Ollama + Open WebUI
make ollama-stop-all
```

## Troubleshooting

### Ollama Deployment
- **llama.cpp not found**: Set `LLAMA_CPP_PATH` in `.env`
- **Conversion errors**: Ensure `numpy` is installed
- **Model not found**: Verify `MODEL_PATH` is correct

### Space Deployment
- **Repository not found**: Script will create it automatically
- **Authentication errors**: Verify `HF_TOKEN` is valid
- **Build failures**: Check Space logs on Hugging Face

