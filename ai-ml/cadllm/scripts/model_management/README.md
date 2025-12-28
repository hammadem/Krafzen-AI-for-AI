# Model Management Scripts

This folder contains scripts for managing trained models: merging adapters, uploading to Hugging Face, and managing datasets.

## Scripts

### `merge_model.py`
**Purpose**: Merge LoRA adapter with base model

Combines the fine-tuned LoRA adapter weights with the base model to create a single, deployable model.

**Usage**:
```bash
# Use defaults from .env
python merge_model.py

# Specify paths
python merge_model.py --adapter_path /workspace/cadllm/checkpoint-21000 --output_dir ./merged_model
```

**Configuration** (via `.env`):
- `ADAPTER_PATH`: Path to LoRA adapter checkpoint directory
- `MODEL_PATH` (or `MODEL_OUTPUT_DIR`): Output directory for merged model
- `BASE_MODEL`: Base model identifier (default: `Qwen/Qwen2.5-Coder-3B-Instruct`)

**Command-line Arguments**:
- `--adapter_path`: Override adapter path
- `--output_dir`: Override output directory
- `--base_model`: Override base model

**Makefile Target**:
```bash
make merge-model
```

**Output**:
- Merged model saved to `MODEL_PATH` or `MODEL_OUTPUT_DIR`
- Ready for deployment or upload

---

### `upload_model.py`
**Purpose**: Upload merged model to Hugging Face Hub

Uploads the merged model to Hugging Face Hub with automatic model card generation.

**Usage**:
```bash
# Use defaults from .env
python upload_model.py

# Specify model path
python upload_model.py --model_path ./merged_model
```

**Configuration** (via `.env`):
- `MODEL_PATH` (or `MODEL_OUTPUT_DIR`): Path to merged model directory
- `HF_TOKEN`: Hugging Face authentication token (required)
- `HF_USERNAME`: Your Hugging Face username
- `HF_FINE_TUNED_MODEL_NAME`: Model name for upload
- `HF_DATASET_NAME`: Optional dataset name (adds link to model card)
- `PRIVATE`: Whether repository is private (default: `false`)

**Command-line Arguments**:
- `--model_path`: Override model path
- `--repo_id`: Override repository ID (format: `username/model-name`)
- `--private`: Make repository private
- `--public`: Make repository public

**Makefile Target**:
```bash
make upload-model
```

**Features**:
- Automatic model card generation
- Dataset link integration (if `HF_DATASET_NAME` is set)
- Progress tracking
- Error handling

**Output**:
- Model uploaded to: `https://huggingface.co/{HF_USERNAME}/{HF_FINE_TUNED_MODEL_NAME}`
- Model card (README.md) automatically generated

---

### `upload_dataset.py`
**Purpose**: Upload JSONL dataset to Hugging Face Hub

Uploads training datasets to Hugging Face Hub with automatic dataset card generation.

**Usage**:
```bash
# Use defaults from .env
python upload_dataset.py

# Specify dataset file
python upload_dataset.py --dataset_file ./dataset.jsonl
```

**Configuration** (via `.env`):
- `DATASET_FILE`: Path to JSONL dataset file
- `HF_TOKEN`: Hugging Face authentication token (required)
- `HF_USERNAME`: Your Hugging Face username
- `HF_DATASET_NAME`: Dataset name for upload
- `PRIVATE`: Whether repository is private (default: `false`)

**Command-line Arguments**:
- `--dataset_file`: Override dataset file path
- `--repo_id`: Override repository ID (format: `username/dataset-name`)
- `--private`: Make repository private
- `--public`: Make repository public

**Makefile Target**:
```bash
make upload-dataset
```

**Features**:
- JSONL format validation
- Automatic dataset card generation
- Progress tracking
- Record count and structure documentation

**Output**:
- Dataset uploaded to: `https://huggingface.co/datasets/{HF_USERNAME}/{HF_DATASET_NAME}`
- Dataset card (README.md) automatically generated

## Workflow

1. **Train Model**: Use `training/train_qwen.py` to fine-tune the model
2. **Merge Model**: Use `merge_model.py` to combine adapter with base model
3. **Upload Model**: Use `upload_model.py` to upload to Hugging Face
4. **Upload Dataset** (optional): Use `upload_dataset.py` to share training data
5. **Deploy**: Use `deployment/` scripts to deploy the model

## Model Card Integration

When `HF_DATASET_NAME` is set in `.env`, `upload_model.py` automatically:
- Adds dataset information to the model card
- Creates a link to the dataset repository
- Documents the training data used

This helps users understand what data the model was trained on.

