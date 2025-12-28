# CADLLM - CAD Language Model Training

This repository contains the training infrastructure and fine-tuned models for CAD (Computer-Aided Design) language models based on Qwen2.5-Coder-3B-Instruct. The models are fine-tuned on the CADLLM dataset to generate precise 2D CAD coordinates from natural language descriptions, which are then converted to DXF files.

## Quick Start

### Using Makefile (Recommended)

The project includes a Makefile for common operations:

```bash
# See all available commands
make help

# Install Python dependencies
make setup

# Prepare dataset (download, recreate with descriptions, clean)
make prepare-dataset

# Create package for upload to RunPod
make package

# Test Hugging Face API (requires .env file)
make test-api

# Show project information
make info
```

**See [Makefile Commands](#makefile-commands) section below for complete list.**

### Manual Setup

See [Setting Up a New RunPod Machine](#setting-up-a-new-runpod-machine) section below.

## Training Environment

### Hardware Specifications

The models were trained on a **RunPod** cloud instance with the following specifications:

- **GPU**: NVIDIA H200 NVL 1x (or equivalent: H100 NVL, H100 SXM, RTX PRO 6000)
- **vCPU**: 16+ cores
- **Memory**: 94+ GB RAM (recommended: 125+ GB)
- **Container Disk**: 20 GB
- **Pod Volume**: 20 GB (mounted at `/workspace`)
- **Location**: US-MD-1 (Secure Cloud)

**Recommended GPU Alternatives (if H200 NVL unavailable):**
- **RTX PRO 6000** (96GB VRAM, $1.84/hr) - Best value, high availability
- **H100 SXM** (80GB VRAM, $2.69/hr) - Best availability, excellent performance
- **H100 NVL** (94GB VRAM, $3.07/hr) - Closest to H200, low availability
- **L40S** (48GB VRAM, $0.86/hr) - Budget option, sufficient for 3B model with LoRA

### Software Environment

- **Container Image**: `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`
- **Template**: `runpod-torch-v240`
- **PyTorch Environment**: Ready-to-use PyTorch + Python development environment with:
  - Jupyter Notebook 6.5.5
  - JupyterLab with widgets and extensions
  - Pre-configured workspace directory
  - SSH access (Port 22, TCP)
  - NGINX server
  - Development tools

**Ports**:
- Jupyter: Port 8888 (HTTP)
- SSH: Port 22 (TCP)

## Setting Up a New RunPod Machine

This section provides step-by-step instructions for deploying a new training pod on RunPod.io and uploading all necessary files.

### Step 1: Create a New Pod on RunPod

1. **Log in to RunPod.io** and navigate to "Pods"
2. **Click "Deploy"** to create a new pod
3. **Configure the pod** with these settings:
   - **GPU**: NVIDIA H200 NVL (or similar high-memory GPU)
   - **Container Image**: `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`
   - **Template**: `runpod-torch-v240` (if available)
   - **Pod Volume**: 20 GB minimum (recommended: 50 GB+ for dataset storage)
   - **Container Disk**: 20 GB
   - **Location**: Choose based on your preference (US-MD-1 recommended)

4. **Deploy the pod** and wait for it to initialize

### Step 2: Connect to the Pod

You can connect via:
- **SSH**: Use the provided SSH command from RunPod dashboard
- **Jupyter**: Access via the Jupyter URL (Port 8888)
- **Terminal**: Use RunPod's web terminal

### Step 3: Prepare Files to Upload

**Recommended: Use the Makefile** (easiest method):

```bash
# From the cadllm directory
make package
```

This creates `cadllm-workspace.tar.gz` with all required files, excluding:
- Model checkpoints (generated during training)
- Raw dataset files (download on pod)
- Log files (generated during training)
- Cache files and temporary data

**Manual Method:**

Create a compressed archive of the following files and directories:

**Required Files:**
```
workspace/
├── train_qwen.py                    # Main training script
├── infer.py                         # Inference script
├── requirements.txt                 # Python dependencies
├── train.sh                         # Training launcher script
├── run.sh                           # Tmux session manager (auto-installs deps)
├── dsl_parser.py                    # DSL format to DXF parser
└── dataset/
    ├── scripts/                     # Dataset processing scripts
    │   ├── download_dataset.py
    │   ├── recreate_dataset_with_descriptions.py
    │   └── clean_dataset.py
    └── jsonl/                       # Processed dataset files
        └── cadllm_2d_cleaned.jsonl  # Your cleaned dataset (recommended)
```

**Optional Files (if you have them):**
- `.env` file (for Hugging Face API access)
- `cadllm_client.py` (for API testing)
- `test_hf_api.py` (for API testing)
- `upload_model.py` (for model upload to Hugging Face)

**Note:** Do NOT upload:
- Model checkpoints (they will be generated during training)
- Raw dataset files (download them on the pod instead)
- Log files (they will be generated during training)

### Step 4: Upload Files to the Pod

#### Option A: Using Makefile + SCP (Recommended)

From your local machine:

```bash
# Create package using Makefile
cd /path/to/cadllm
make package

# Upload to RunPod (replace with your pod's SSH details)
scp cadllm-workspace.tar.gz root@<pod-ip>:/workspace/

# SSH into the pod
ssh root@<pod-ip>

# Extract the files (--no-same-owner suppresses harmless ownership warnings)
cd /workspace
tar --no-same-owner --warning=no-unknown-keyword -xzf cadllm-workspace.tar.gz
```

#### Option A2: Manual SCP (Alternative)

```bash
# Create a tarball of the workspace
cd /path/to/cadllm/NVIDIA-H200-NVL
tar -czf workspace.tar.gz workspace/

# Upload to RunPod (replace with your pod's SSH details)
scp workspace.tar.gz root@<pod-ip>:/workspace/

# SSH into the pod
ssh root@<pod-ip>

# Extract the files (--no-same-owner suppresses harmless ownership warnings)
cd /workspace
tar --no-same-owner --warning=no-unknown-keyword -xzf workspace.tar.gz
```

#### Option B: Using RunPod's File Manager

1. Access the pod's file manager via RunPod dashboard
2. Navigate to `/workspace`
3. Upload the compressed archive
4. Extract it using the terminal:
   ```bash
   cd /workspace
   tar --no-same-owner --warning=no-unknown-keyword -xzf cadllm-workspace.tar.gz
   ```
   Note: `--no-same-owner` suppresses harmless ownership warnings from macOS metadata files.

#### Option C: Using Git (If Repository is Available)

```bash
# On the pod
cd /workspace
git clone <your-repo-url> cadllm
cd cadllm/NVIDIA-H200-NVL/workspace
```

### Step 5: Install Dependencies

**Note:** The `run.sh` script automatically installs dependencies from `requirements.txt` when you start training. However, you can also install them manually:

```bash
cd /workspace
pip install -r requirements.txt
```

Or use the Makefile (if available):
```bash
make setup
```

This will install all required Python packages including:
- `transformers`, `datasets`, `peft`, `accelerate`
- `torch`, `tqdm`, `sentencepiece`
- `python-dotenv`, `huggingface-hub`

### Step 6: Download Dataset (If Not Already Uploaded)

**Note:** The `run.sh` script automatically installs Python dependencies, but you still need to prepare the dataset.

If you haven't uploaded the processed dataset, you can download and prepare it on the pod:

```bash
# Using Makefile (if available)
make prepare-dataset

# Or manually
cd /workspace/dataset/scripts
python download_dataset.py
python recreate_dataset_with_descriptions.py \
    --raw-dir ../../cadllm_raw/cad_collection_select_V2/cad_collection_select_V2 \
    --excel-dir ../../cadllm_raw/ccs_description_text \
    --output ../jsonl/cadllm_2d_with_descriptions.jsonl
python clean_dataset.py \
    --input ../jsonl/cadllm_2d_with_descriptions.jsonl \
    --output ../jsonl/cadllm_2d_cleaned.jsonl
```

**Or** if you have the cleaned dataset ready locally, upload it directly to `/workspace/dataset/jsonl/` using the package created with `make package-with-dataset`.

### Step 7: Verify Setup

```bash
# Check GPU availability
nvidia-smi

# Verify Python and packages
python --version
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

# Check dataset
ls -lh /workspace/dataset/jsonl/
```

### Step 8: Start Training

#### Option 1: Using Makefile (Recommended)

```bash
cd /workspace
make train
```

This will:
- Make `train.sh` and `run.sh` executable
- Set dataset path: `/workspace/dataset/jsonl/cadllm.jsonl`
- Set output directory: `/workspace/cadllm`
- **Automatically install Python dependencies** from `requirements.txt` (via `run.sh`)
- Install tmux if needed
- Create a tmux session named "cadllm"
- Start training with the correct configuration
- Save logs to `/workspace/logs/`

**Custom paths:** You can override the defaults:
```bash
DATA_PATH=/workspace/dataset/jsonl/cadllm_2d_cleaned.jsonl \
OUTPUT_DIR=/workspace/my-custom-model \
make train
```

#### Option 2: Using the Training Script Directly

```bash
cd /workspace
chmod +x train.sh run.sh
./run.sh
```

This will:
- **Automatically install Python dependencies** from `requirements.txt` (if not already installed)
- Install tmux if needed
- Create a tmux session named "cadllm"
- Start training with the configuration in `train.sh`
- Save logs to `/workspace/logs/`

#### Option 2: Direct Training Command

```bash
cd /workspace
python -u train_qwen.py \
  --data_path /workspace/dataset/jsonl/cadllm.jsonl \
  --output_dir /workspace/cadllm \
  --num_train_epochs 1 \
  --max_seq_length 512 \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 2
```

#### Option 3: Custom Training Configuration

Edit `train.sh` to modify training parameters, then run:

```bash
./train.sh
```

### Step 9: Monitor Training

**Via Tmux (if using `run.sh`):**
```bash
tmux attach -t cadllm
```

**Via Logs:**
```bash
tail -f /workspace/logs/train_qwen_*.log
```

**Via Jupyter:**
- Access Jupyter at the provided URL
- Open a notebook to monitor training progress

### Step 10: Download Results

After training completes, download the model checkpoints:

```bash
# From your local machine
scp -r root@<pod-ip>:/workspace/cadllm ./local-backup/
```

Or use RunPod's file manager to download the model directory.

### Quick Setup Checklist

- [ ] Pod created with correct GPU and container image
- [ ] Connected to pod via SSH or terminal
- [ ] Files uploaded to `/workspace`
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Dataset available at `/workspace/dataset/jsonl/cadllm.jsonl`
- [ ] GPU verified (`nvidia-smi`)
- [ ] Training script executable (`chmod +x train.sh run.sh`)
- [ ] Training started (`./run.sh` or direct command)
- [ ] Monitoring setup (tmux or log tail)

### Troubleshooting

**Pod won't start:**
- Check GPU availability in your region
- Verify container image name is correct
- Ensure sufficient credits in your RunPod account

**Out of memory errors:**
- Reduce `per_device_train_batch_size` in `train.sh`
- Increase `gradient_accumulation_steps` to maintain effective batch size
- Reduce `max_seq_length` if using long sequences

**Dataset not found:**
- Verify dataset path in `train.sh` matches actual location
- Check file permissions: `ls -la /workspace/dataset/jsonl/`
- Ensure the dataset file exists: `cadllm.jsonl` (default) or set `DATA_PATH` environment variable
- If using cleaned dataset, rename it to `cadllm.jsonl` or set `DATA_PATH=/workspace/dataset/jsonl/cadllm_2d_cleaned.jsonl`

**Training stops unexpectedly:**
- Check logs: `tail -f /workspace/logs/train_qwen_*.log`
- Verify pod hasn't been stopped (check RunPod dashboard)
- Ensure sufficient pod volume space: `df -h`

## Project Structure

```
cadllm/
├── NVIDIA-H200-NVL/
│   └── workspace/
│       ├── train_qwen.py                    # Main training script
│       ├── infer.py                 # Inference script (GPU)
│       ├── cadllm_client.py         # Hugging Face API client
│       ├── test_hf_api.py           # Hugging Face API test script
│       ├── dsl_parser.py             # DSL format to DXF parser
│       ├── upload_model.py          # Merge LoRA and upload to Hugging Face
│       ├── requirements.txt         # Python dependencies
│       ├── train.sh                 # Training launcher script
│       ├── run.sh                   # Tmux session manager (auto-installs deps)
│       ├── cadllm/                 # Fine-tuned model output directory (local)
│       ├── dataset/                 # Dataset and processing scripts
│       │   ├── cadllm_raw/          # Raw dataset files (downloaded)
│       │   ├── jsonl/               # Processed JSONL files
│       │   │   ├── cadllm.jsonl             # Training dataset (default)
│       │   │   ├── cadllm_2d_cleaned.jsonl  # Cleaned dataset (can be renamed to cadllm.jsonl)
│       │   │   └── cadllm_2d_with_descriptions.jsonl
│       │   └── scripts/             # Dataset processing scripts
│       │       ├── download_dataset.py
│       │       ├── recreate_dataset_with_descriptions.py
│       │       └── clean_dataset.py
│       ├── space/                   # Hugging Face Space deployment
│       │   └── cad-llm-api/         # FastAPI server for Space
│       └── logs/                    # Training logs
│       └── logs/                   # Training logs
├── docs/                           # Documentation
│   └── huggingface-deployment.md   # Hugging Face API deployment guide
└── README.md                       # This file
```

## Models

Two fine-tuned models are available:

The fine-tuned model is saved to `/workspace/cadllm` by default. Checkpoints are saved during training at regular intervals (every 500 steps by default).

**Previous model versions:**
- `cad-agent-qwen-2d`: Fine-tuned on 2D CAD data (legacy)
- `cad-agent-qwen-full`: Fine-tuned on full CADLLM dataset (legacy)

Both models use **LoRA (Low-Rank Adaptation)** fine-tuning with the following configuration:
- **Base Model**: `Qwen/Qwen2.5-Coder-3B-Instruct`
- **LoRA Rank (r)**: 16
- **LoRA Alpha**: 32
- **LoRA Dropout**: 0.05
- **Target Modules**: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj

## Setup

### Prerequisites

- Python 3.11+
- CUDA 12.4.1+ (for GPU training)
- PyTorch 2.4.0+

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

The main dependencies include:
- `transformers>=4.45.0,<5.0.0`
- `datasets>=2.16.0,<3.0.0`
- `peft>=0.12.0,<0.13.0`
- `accelerate>=0.33.0,<1.0.0`
- `tqdm>=4.66.0`
- `sentencepiece>=0.1.99`
- `python-dotenv>=1.0.0` - For loading environment variables from `.env`
- `huggingface-hub==0.36.0` - For Hugging Face Inference API access

### Dataset Preparation

1. Download the CADLLM dataset:

```bash
cd dataset/scripts
python download_dataset.py
```

This will download the dataset from Hugging Face (`lanlanguai/CADLLM`) and extract it to `dataset/cadllm_raw/`.

2. Recreate dataset with descriptions from Excel files:

```bash
cd dataset/scripts
python recreate_dataset_with_descriptions.py \
    --raw-dir ../../cadllm_raw/cad_collection_select_V2/cad_collection_select_V2 \
    --excel-dir ../../cadllm_raw/ccs_description_text \
    --output ../jsonl/cadllm_2d_with_descriptions.jsonl
```

3. Clean the dataset (normalize coordinates, close shapes, apply dimensions):

```bash
cd dataset/scripts
python clean_dataset.py \
    --input ../jsonl/cadllm_2d_with_descriptions.jsonl \
    --output ../jsonl/cadllm_2d_cleaned.jsonl
```

The processed JSONL files are located in `dataset/jsonl/`:
- `cadllm_2d_cleaned.jsonl`: **Recommended for training** - Cleaned 2D-focused dataset with:
  - Normalized coordinates (centered at origin 0,0)
  - Closed shapes (unclosed polylines automatically closed)
  - Proper descriptions from Excel files
  - Correct dimensions applied
  - Multiple objects removed when not requested
- `cadllm_2d_with_descriptions.jsonl`: 2D dataset with descriptions (before cleaning)

## Training

### Training Configuration

The training script supports various hyperparameters. Default configuration:

- **Learning Rate**: 2e-4
- **Batch Size**: 4 per device
- **Gradient Accumulation**: 2 steps
- **Max Sequence Length**: 768 (512 for 2D model)
- **Epochs**: 1
- **Warmup Ratio**: 0.03
- **LR Scheduler**: Cosine
- **Precision**: bfloat16 (if supported) or float16

### Running Training

#### Option 1: Direct Training

```bash
python -u train_qwen.py \
  --data_path /workspace/dataset/jsonl/cadllm.jsonl \
  --output_dir /workspace/cadllm \
  --num_train_epochs 1 \
  --max_seq_length 768 \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 2
```

#### Option 2: Using Training Script

For 2D model:
```bash
./train.sh
```

#### Option 3: Using Tmux Session Manager

```bash
./run.sh
```

This will create or attach to a tmux session named "cadllm" and run the training script.

### Training Arguments

Key arguments for `train_qwen.py`:

- `--model_name`: Base model (default: `Qwen/Qwen2.5-Coder-3B-Instruct`)
- `--data_path`: Path to JSONL dataset file
- `--output_dir`: Directory to save checkpoints and final model
- `--max_seq_length`: Maximum sequence length (default: 768)
- `--per_device_train_batch_size`: Batch size per GPU (default: 4)
- `--gradient_accumulation_steps`: Gradient accumulation steps (default: 1)
- `--learning_rate`: Learning rate (default: 2e-4)
- `--num_train_epochs`: Number of training epochs (default: 1.0)
- `--save_steps`: Save checkpoint every N steps (default: 500)
- `--logging_steps`: Log every N steps (default: 50)
- `--seed`: Random seed (default: 42)

## Inference

### Using Hugging Face Inference API (Recommended)

The Hugging Face Inference API works for both local testing and production. It's fast, cost-effective, and requires no infrastructure setup.

**Quick Start:**
```bash
# 1. Install dependencies
cd NVIDIA-H200-NVL/workspace
pip install -r requirements.txt

# 2. Set up .env file with your Hugging Face token
# Copy .env.example to .env and add:
# HF_TOKEN=your_token_here
# HF_USERNAME=your-username

# 3. Use the client
from cadllm_client import CADLLMClient

client = CADLLMClient("your-username/cad-llm-krafzen")
result = client.generate("Create a circle with radius 10mm centered at origin")
print(result)
```

**Performance:**
- Response time: 1-3 seconds
- Cost: ~$0.50-5/month for typical usage
- Works on any machine (Mac, Linux, Windows)
- No GPU required

**For complete setup instructions, see [docs/huggingface-deployment.md](docs/huggingface-deployment.md)**

### Local Inference on Mac

For running the model locally on your Mac (with or without Ollama):

**Quick Start:**
```bash
# 1. Set up .env file
cd NVIDIA-H200-NVL/workspace
cat > .env << EOF
BASE_MODEL=Qwen/Qwen2.5-Coder-3B-Instruct
MODEL_PATH=~/Projects/models/cadllm/merged_model  # For merged model (recommended)
# OR
ADAPTER_PATH=~/Projects/models/cadllm  # For LoRA adapter
EOF

# 2. Run inference
python infer_local_mac.py "Create a circle with radius 10mm"

# Or use Makefile
make infer-local PROMPT="Create a rectangle 100mm x 50mm"
```

**Performance:**
- **Apple Silicon (M1/M2/M3)**: Uses MPS acceleration, reasonably fast
- **Intel Mac**: Uses CPU, slower but works
- **Memory**: Requires ~6-8GB RAM for the 3B model

**Using Merged Model (Recommended):**
- Faster loading (no need to load base + adapter separately)
- Set `MODEL_PATH` in `.env` to your merged model directory

**Using LoRA Adapter:**
- Requires downloading base model on first run
- Set `ADAPTER_PATH` in `.env` to your adapter directory

**For Ollama deployment**, see [Ollama Deployment](#ollama-deployment) section below or [OLLAMA_SETUP.md](NVIDIA-H200-NVL/workspace/OLLAMA_SETUP.md)

### GPU Inference (Training Environment)

For testing on the GPU training environment, use the `infer.py` script:

```bash
python infer.py
```

The script loads the fine-tuned model and generates code for a test prompt. You can modify the `test_prompt` variable in `infer.py` to test with your own prompts.

### Inference Configuration

Default inference settings:
- **Max New Tokens**: 400
- **Temperature**: 0.7
- **Top-p**: 0.9
- **Sampling**: Enabled

### Example Prompt Format

```
You are a CAD code assistant. Produce ezdxf-ready CAD operations 
and enhanced geometry reasoning.

### Instruction
Create a DXF drawing of a 100x50 rectangle with 5mm rounded corners, 
centered at origin. Put it on layer OUTLINE.

### Input
(none)

### Enhanced CAD Prompt (DXF-ready)
```

## Model Checkpoints

Checkpoints are saved during training at regular intervals (every 500 steps by default). Each checkpoint includes:

- `adapter_model.safetensors`: LoRA adapter weights
- `adapter_config.json`: LoRA configuration
- `tokenizer.json`, `tokenizer_config.json`: Tokenizer files
- `training_args.bin`: Training arguments
- `trainer_state.json`: Training state
- Optimizer and scheduler states (for resuming training)

### Resuming Training from Checkpoints

If your training was interrupted (e.g., server restart), you can resume from the last checkpoint.

#### Quick Resume (Automatic Detection)

The training script **automatically detects** the latest checkpoint in your output directory. Simply run the same training command again:

```bash
python -u train_qwen.py \
  --data_path /workspace/dataset/jsonl/cadllm.jsonl \
  --output_dir /workspace/cadllm \
  --num_train_epochs 1 \
  --max_seq_length 512 \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 2
```

The script will automatically find and resume from the latest checkpoint (e.g., `checkpoint-21000`).

#### Manual Resume (Specify Checkpoint)

If you want to resume from a specific checkpoint:

```bash
python -u train_qwen.py \
  --data_path /workspace/dataset/jsonl/cadllm.jsonl \
  --output_dir /workspace/cadllm \
  --resume_from_checkpoint /workspace/cadllm/checkpoint-21000 \
  --num_train_epochs 1 \
  --max_seq_length 512 \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 2
```

#### Using Makefile

You can also use the Makefile target:

```bash
# Auto-detect latest checkpoint
make train-resume

# Or specify a checkpoint
make train-resume CHECKPOINT=/workspace/cadllm/checkpoint-21000
```

#### Finding Your Checkpoint

Checkpoints are saved in subdirectories within your `output_dir`:

```bash
# List all checkpoints
ls -la /workspace/cadllm/checkpoint-*

# Find the latest checkpoint by step number
ls -1 /workspace/cadllm/checkpoint-* | sort -V | tail -1
```

#### What Gets Resumed?

When resuming from a checkpoint, the following are restored:
- ✅ Model weights (LoRA adapter)
- ✅ Optimizer state
- ✅ Learning rate scheduler state
- ✅ Training step number
- ✅ All training arguments

Training will continue from exactly where it left off, so you won't lose any progress!

#### Troubleshooting Resume Issues

**PyTorch Version Error (CVE-2025-32434)**

If you see this error:
```
ValueError: Due to a serious vulnerability issue in `torch.load`, even with `weights_only=True`, 
we now require users to upgrade torch to at least v2.6 in order to use the function.
```

**Solution**: Upgrade PyTorch and torchvision to compatible versions:

```bash
pip install --upgrade "torch>=2.6.0" "torchvision>=0.21.0"
```

This is required because checkpoints contain optimizer/scheduler state files that use `torch.load()`, which has a security vulnerability in older versions.

**Torchvision Compatibility Error**

If you see this error:
```
RuntimeError: operator torchvision::nms does not exist
```

**Solution**: This happens when torchvision is not compatible with your torch version. Upgrade both together:

```bash
pip install --upgrade "torch>=2.6.0" "torchvision>=0.21.0"
```

Or reinstall both to ensure compatibility:

```bash
pip uninstall torch torchvision -y
pip install "torch>=2.6.0" "torchvision>=0.21.0"
```

**No checkpoint found**: Make sure your `--output_dir` path is correct and checkpoints exist in that directory.

**Checkpoint mismatch**: Ensure you're using the same model, dataset, and training arguments as when the checkpoint was created.

## Training Logs

Training logs are saved in the `logs/` directory with timestamps:
- Format: `train_qwen_YYYYMMDD_HHMMSS.log`

## System Prompt

The models are trained with the following system prompt (from `train_qwen.py`):

```
You are a CAD code assistant. Given a simple CAD description, 
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
```

The model generates structured DSL format:
- `UNITS: mm` - Measurement units
- `ORIGIN_POLICY: room_center_at_(0,0)` - Coordinate system policy
- `ROOM: rect w=WIDTH h=HEIGHT center=(0,0)` - Room dimensions
- `WALLS: rect_perimeter closed=true layer=WALLS` - Wall perimeter
- `OBJECT_NAME: rect w=WIDTH h=HEIGHT center=(X,Y) layer=LAYER closed=true anchor_wall=WALL` - Rectangular objects
- `OBJECT_NAME: circle r=RADIUS center=(X,Y) layer=LAYER closed=true anchor_wall=WALL` - Circular objects

The DSL output is then converted to DXF files using `dsl_parser.py`.

## Notes

- The models use **gradient checkpointing** to save memory during training
- **bfloat16** precision is used when supported by the GPU (H200 supports it)
- The dataset is automatically split: first 2000 examples for evaluation, rest for training
- Training uses single-GPU setup (no distributed training)

## Deployment

**🚀 Recommended: Hugging Face Inference API**

The Hugging Face Inference API is the recommended solution for both local testing and production:
- **Easiest setup**: 5 minutes to deploy
- **Cost-effective**: ~$0.50-5/month for typical usage
- **Zero infrastructure**: Fully managed
- **Fast**: 1-3 second response times
- **Works everywhere**: Mac, Linux, Windows - no GPU needed

**See [Hugging Face Deployment Guide](docs/huggingface-deployment.md)** for complete setup instructions.

The guide covers:
- Model upload to Hugging Face Hub
- API setup and authentication
- Code examples and integration
- Privacy settings and costs
- Troubleshooting

## Makefile Commands

The project includes a comprehensive Makefile for automating common tasks:

### Dataset Operations

- `make download-dataset` - Download raw CADLLM dataset from Hugging Face
- `make recreate-dataset` - Recreate dataset with descriptions from Excel files
- `make clean-dataset` - Clean dataset (normalize coordinates, close shapes, apply dimensions)
- `make prepare-dataset` - Complete dataset pipeline (download → recreate → clean)

### Package Management

- `make package` - Create tarball for upload to RunPod (excludes large files)
- `make package-with-dataset` - Create tarball including cleaned dataset
- `make package-with-enhanced-dataset` - Create tarball including enhanced dataset (for simple prompts)
- `make unarchive` - Verify extraction (use after manual `tar --no-same-owner --warning=no-unknown-keyword -xzf cadllm-workspace.tar.gz`)
- `make extract` - Alias for `make unarchive`
- `make setup` - Install Python dependencies from requirements.txt

### Training

- `make train` - **Start training on RunPod server** (chmods scripts, sets correct paths, runs training)
- `make train-resume` - **Resume training from latest checkpoint** (auto-detects) or specify `CHECKPOINT=path/to/checkpoint`

### Model Management

- `make merge-model` - **Merge LoRA adapter with base model** (use `ADAPTER_PATH` and `MODEL_OUTPUT_DIR` env vars)
- `make upload-model` - **Upload merged model to Hugging Face** (use `MODEL_PATH` env var)
- `make deploy-ollama` - **Deploy merged model to Ollama** (requires llama.cpp, see [Ollama Setup](#ollama-deployment))

**Required Environment Variables (.env file):**

Create a `.env` file in the `workspace/` directory with the following variables:

```bash
# Hugging Face Configuration (required for upload_model.py)
HF_TOKEN=your_huggingface_token_here
HF_USERNAME=your-username
HF_FINE_TUNED_MODEL_NAME=your-model-name

# Model Configuration (required for both scripts)
BASE_MODEL=Qwen/Qwen2.5-Coder-3B-Instruct

# Merge Model Configuration (required for merge_model.py)
ADAPTER_PATH=/path/to/adapter
OUTPUT_DIR=/path/to/merged_model

# Upload Model Configuration (required for upload_model.py)
MODEL_PATH=/path/to/merged_model

# Ollama Deployment Configuration (optional, for deploy_ollama.py)
MODEL_OUTPUT_DIR=/path/to/merged_model  # Same as MODEL_PATH after merging
OLLAMA_MODEL_NAME=cadllm  # Optional, defaults to 'cadllm'
GGUF_OUTPUT_DIR=./ollama-models  # Optional, defaults to ./ollama-models
LLAMA_CPP_PATH=/path/to/llama.cpp  # Optional, auto-detects Homebrew and common locations

# Repository Privacy Setting (optional, default: true)
HF_REPO_PRIVATE=true
```

**Note:** All configuration values must be set in the `.env` file or passed as command-line arguments. There are no hardcoded defaults.

### Testing & Deployment

- `make test-api` - Test Hugging Face API with default prompt
- `make test-api-custom PROMPT="your prompt"` - Test API with custom prompt

### Utilities

- `make info` - Show project information and file sizes
- `make clean` - Remove generated files (package, cache, etc.)
- `make clean-all` - Remove all generated files including processed datasets
- `make help` - Show all available commands

### Example Workflow

```bash
# Complete setup workflow (local)
make prepare-dataset      # Download and prepare dataset
make package              # Create upload package (includes Makefile)
make info                 # Check what was created

# On RunPod after upload
cd /workspace
tar --no-same-owner --warning=no-unknown-keyword -xzf cadllm-workspace.tar.gz  # Extract (--no-same-owner suppresses warnings)
make train                # Start training (chmods scripts, sets paths, auto-installs deps)
```

**Note:** The `make train` command on the server will:
- Make `train.sh` and `run.sh` executable
- Set dataset path: `/workspace/dataset/jsonl/cadllm.jsonl`
- Set output directory: `/workspace/cadllm`
- Automatically install dependencies via `run.sh`
- Start training in a tmux session

**Custom paths:** Override defaults with environment variables:
```bash
DATA_PATH=/workspace/dataset/jsonl/cadllm_2d_cleaned.jsonl \
OUTPUT_DIR=/workspace/my-custom-model \
make train
```

## Ollama Deployment

Deploy your merged model to Ollama for local inference:

### Prerequisites

1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai) or via Homebrew:
   ```bash
   brew install ollama
   ```

2. **Install llama.cpp**: Required for converting models to GGUF format:
   ```bash
   brew install llama.cpp
   ```
   Or clone from source (uses CMake):
   ```bash
   git clone https://github.com/ggerganov/llama.cpp.git
   cd llama.cpp
   mkdir build && cd build
   cmake ..
   cmake --build .
   ```
   
   **After building from source**, add to your `.env` file:
   ```bash
   LLAMA_CPP_PATH=/path/to/llama.cpp
   ```
   
   Note: Point `LLAMA_CPP_PATH` to the **root** of the cloned llama.cpp directory (where `convert_hf_to_gguf.py` is located), not the `build` directory.

### Deployment Steps

1. **Merge your model** (if not already merged):
   ```bash
   make merge-model
   ```

2. **Deploy to Ollama**:
   ```bash
   make deploy-ollama
   ```

   This will:
   - Convert the merged model to GGUF format using llama.cpp
   - Create an Ollama Modelfile with the correct system prompt (matching training format)
   - Create the Ollama model using `ollama create`

3. **Test your model**:
   ```bash
   ollama run cadllm "Create a circle with radius 10mm"
   ```

### Configuration

Set these variables in your `.env` file (optional, defaults provided):
- `MODEL_OUTPUT_DIR` - Path to merged model (required, same as `MODEL_PATH` after merging)
- `OLLAMA_MODEL_NAME` - Name for Ollama model (default: `cadllm`)
- `GGUF_OUTPUT_DIR` - Output directory for GGUF file (default: `./ollama-models`)
- `LLAMA_CPP_PATH` - Path to llama.cpp root directory (auto-detects Homebrew and common locations)

**After cloning llama.cpp from source**, add this to your `.env` file:
```bash
LLAMA_CPP_PATH=$HOME/llama.cpp
```

**Important:** 
- Point `LLAMA_CPP_PATH` to the **root** of the cloned llama.cpp directory (where `convert_hf_to_gguf.py` is located)
- **NOT** the `build` subdirectory
- The script will auto-detect Homebrew installations, so you only need to set this if you cloned from source

**Example:**
```bash
# If you cloned to ~/llama.cpp
LLAMA_CPP_PATH=$HOME/llama.cpp

# Or use absolute path
LLAMA_CPP_PATH=/Users/kiruthika/llama.cpp
```

### Manual Deployment

You can also run the deployment script directly:
```bash
python deploy_ollama.py \
  --model_path /path/to/merged_model \
  --ollama_model_name cadllm \
  --llama_cpp_path /path/to/llama.cpp
```

**Note:** The script automatically detects:
- Homebrew installations of llama.cpp
- llama.cpp in common locations (`~/llama.cpp`, `~/code/llama.cpp`, etc.)
- Conversion scripts in `bin/` or `libexec/` directories

For more detailed setup instructions, see [OLLAMA_SETUP.md](NVIDIA-H200-NVL/workspace/OLLAMA_SETUP.md).

## License

Please refer to the base model license (Qwen2.5-Coder-3B-Instruct) and the CADLLM dataset license for usage terms.

## References

- **Base Model**: [Qwen2.5-Coder-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct)
- **Dataset**: [CADLLM](https://huggingface.co/datasets/lanlanguai/CADLLM)
- **LoRA**: Parameter-Efficient Fine-Tuning via Low-Rank Adaptation

