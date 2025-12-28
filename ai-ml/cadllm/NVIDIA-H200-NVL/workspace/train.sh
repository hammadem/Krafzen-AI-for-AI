#!/usr/bin/env bash
set -euo pipefail

# ---- training env ----
export PYTHONUNBUFFERED=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

# If you want to force gloo (generally NOT recommended for multi-GPU training),
# keep this. Otherwise remove it and let torch use NCCL.
# export DIST_BACKEND=gloo

# Default values (can be overridden by environment variables or command-line args)
DATA_PATH="${DATA_PATH:-/workspace/dataset/jsonl/cadllm.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-/workspace/cadllm}"

# Parse command-line arguments if provided
RESUME_FROM_CHECKPOINT=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --data_path)
            DATA_PATH="$2"
            shift 2
            ;;
        --output_dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --resume_from_checkpoint)
            RESUME_FROM_CHECKPOINT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--data_path PATH] [--output_dir DIR] [--resume_from_checkpoint CHECKPOINT_PATH]"
            exit 1
            ;;
    esac
done

LOG_DIR=/workspace/logs
mkdir -p "$LOG_DIR"
TS=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/train_qwen_${TS}.log"

echo "Starting training at $(date -u)" | tee "$LOG_FILE"
echo "Logging to: $LOG_FILE" | tee -a "$LOG_FILE"
echo "Data path: $DATA_PATH" | tee -a "$LOG_FILE"
echo "Output dir: $OUTPUT_DIR" | tee -a "$LOG_FILE"

# Single-GPU:
RESUME_ARG=""
if [[ -n "$RESUME_FROM_CHECKPOINT" ]]; then
    RESUME_ARG="--resume_from_checkpoint $RESUME_FROM_CHECKPOINT"
    echo "Resuming from checkpoint: $RESUME_FROM_CHECKPOINT" | tee -a "$LOG_FILE"
fi

python -u train_qwen.py \
  --data_path "$DATA_PATH" \
  --output_dir "$OUTPUT_DIR" \
  --num_train_epochs 1 \
  --max_seq_length 512 \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 2 \
  $RESUME_ARG \
  2>&1 | tee -a "$LOG_FILE"

echo "Training finished at $(date -u)" | tee -a "$LOG_FILE"
