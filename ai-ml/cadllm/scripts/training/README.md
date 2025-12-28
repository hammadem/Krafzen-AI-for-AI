# Training Scripts

This folder contains scripts for fine-tuning the CAD-LLM model using LoRA (Low-Rank Adaptation).

## Scripts

### `train_qwen.py`
**Purpose**: Main training script for fine-tuning Qwen2.5-Coder-3B-Instruct

Fine-tunes the base model on CAD dataset using LoRA for parameter-efficient training.

**Usage**:
```bash
# On GPU server (RunPod, etc.)
cd scripts/training
./run.sh

# Or directly with Python
python train_qwen.py
```

**Configuration** (via environment variables or `.env`):
- `DATA_PATH`: Path to JSONL training dataset (default: `/workspace/dataset/jsonl/cadllm.jsonl`)
- `OUTPUT_DIR`: Directory to save checkpoints (default: `/workspace/cadllm`)
- `BASE_MODEL`: Base model identifier (default: `Qwen/Qwen2.5-Coder-3B-Instruct`)
- `NUM_EPOCHS`: Number of training epochs
- `BATCH_SIZE`: Training batch size
- `LEARNING_RATE`: Learning rate for training

**Features**:
- LoRA (Low-Rank Adaptation) for efficient fine-tuning
- Automatic checkpoint saving
- Resume training from checkpoints
- Qwen chat template format
- System prompt for DSL output format

**Output**:
- Checkpoints saved in `OUTPUT_DIR/checkpoint-{step}`
- Training logs and metrics
- Adapter weights for merging

### `train.sh`
**Purpose**: Training script wrapper

Sets up environment and runs training with proper configuration.

### `run.sh`
**Purpose**: Training runner with dependency installation

Automatically installs dependencies and runs training.

## Makefile Targets

From the project root:

```bash
# Start training
make train

# Resume training from latest checkpoint
make train-resume

# Resume from specific checkpoint
make train-resume CHECKPOINT=/workspace/cadllm/checkpoint-21000
```

## Training Process

1. **Prepare Dataset**: Ensure JSONL dataset is ready (see `dataset/` folder)
2. **Set Environment Variables**: Configure `DATA_PATH` and `OUTPUT_DIR`
3. **Start Training**: Run `make train` or `./run.sh`
4. **Monitor Progress**: Check logs for training metrics
5. **Resume if Needed**: Use `make train-resume` to continue from checkpoint

## Checkpoints

Checkpoints are automatically saved during training:
- Location: `OUTPUT_DIR/checkpoint-{step}`
- Contains: Model adapter weights, optimizer state, training state
- Resume: Automatically detects latest checkpoint or specify with `CHECKPOINT` env var

## Output Format

The model is trained to generate DSL (Domain-Specific Language) format:
```
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=WIDTH h=HEIGHT center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
OBJECT_NAME: rect w=WIDTH h=HEIGHT center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL
```

This DSL output can be converted to DXF using `utils/dsl_parser.py`.

## Next Steps

After training:
1. **Merge Model**: Use `model_management/merge_model.py` to merge adapter with base model
2. **Upload Model**: Use `model_management/upload_model.py` to upload to Hugging Face
3. **Deploy**: Use `deployment/` scripts to deploy to Ollama or Hugging Face Space
4. **Test**: Use `testing/test_hf_api.py` to test the deployed model

