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
├── dxf_parser.py                    # Coordinate to DXF parser
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

# Extract the files
cd /workspace
make unarchive
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

# Extract the files
cd /workspace
make unarchive  # or: tar -xzf workspace.tar.gz
```

#### Option B: Using RunPod's File Manager

1. Access the pod's file manager via RunPod dashboard
2. Navigate to `/workspace`
3. Upload the compressed archive
4. Extract it using the terminal:
   ```bash
   cd /workspace
   make unarchive  # or: tar -xzf cadllm-workspace.tar.gz
   ```

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
│       ├── dxf_parser.py             # Coordinate to DXF parser
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

To resume training from a checkpoint, modify the `--output_dir` argument to point to the checkpoint directory.

## Training Logs

Training logs are saved in the `logs/` directory with timestamps:
- Format: `train_qwen_YYYYMMDD_HHMMSS.log`

## System Prompt

The models are trained with the following system prompt:

```
You are a CAD code assistant. Given a CAD description, 
generate precise 2D CAD coordinates. Always center shapes at origin (0, 0). 
Use exact dimensions specified. Generate single, closed shapes unless multiple objects are explicitly requested.
```

The model generates coordinates in this format:
- `<SOL>` - Start of object
- `<Circle>: x=0.0, y=0.0, r=48.0` - Circle with center and radius
- `<Line>: x=47.5, y=-32.0` - Line coordinates (multiple lines form a polyline)
- `<Arc>: x=-8.5, y=-58.0, α=64.0, f=1.0` - Arc with center, angle, and flag
- `<EOS>` - End of sequence

These coordinates are then converted to DXF files using `dxf_parser.py`.

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
- `make unarchive` - Extract workspace package on training machine (RunPod)
- `make extract` - Alias for `make unarchive`
- `make setup` - Install Python dependencies from requirements.txt

### Training

- `make train` - **Start training on RunPod server** (chmods scripts, sets correct paths, runs training)

### Testing & Deployment

- `make test-api` - Test Hugging Face API with default prompt
- `make test-api-custom PROMPT="your prompt"` - Test API with custom prompt
- `make upload-model` - Merge LoRA adapter and upload to Hugging Face

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
make unarchive            # Extract the package
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

## License

Please refer to the base model license (Qwen2.5-Coder-3B-Instruct) and the CADLLM dataset license for usage terms.

## References

- **Base Model**: [Qwen2.5-Coder-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct)
- **Dataset**: [CADLLM](https://huggingface.co/datasets/lanlanguai/CADLLM)
- **LoRA**: Parameter-Efficient Fine-Tuning via Low-Rank Adaptation

