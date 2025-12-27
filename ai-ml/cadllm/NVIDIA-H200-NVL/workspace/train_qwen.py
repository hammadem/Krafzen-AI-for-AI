#!/usr/bin/env python
"""
Single-GPU LoRA fine-tuning of Qwen2.5-Coder-3B-Instruct on CADLLM.

Run on the H200 box with e.g.:

  python -u train_qwen.py \
    --data_path /workspace/cadllm_processed.jsonl \
    --output_dir /workspace/cad-agent-qwen-full \
    --num_train_epochs 1 \
    --max_seq_length 512 \
    --per_device_train_batch_size 4 \
    --gradient_accumulation_steps 2
"""

import os
import argparse
from typing import Dict, Any, List

import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    set_seed,
)
from peft import LoraConfig, get_peft_model

SYSTEM_PROMPT = (
    "You are a CAD code assistant. Given a simple CAD description, "
    "output ONLY the strict DSL format shown below. Do not use natural language.\n\n"
    "Required DSL Format (STRICT - must match exactly):\n"
    "UNITS: mm\n"
    "ORIGIN_POLICY: room_center_at_(0,0)\n"
    "ROOM: rect w=WIDTH h=HEIGHT center=(0,0)\n"
    "WALLS: rect_perimeter closed=true layer=WALLS\n"
    "OBJECT_NAME: rect w=WIDTH h=HEIGHT center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL\n"
    "OBJECT_NAME: circle r=RADIUS center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL\n\n"
    "Rules:\n"
    "- Always start with UNITS, ORIGIN_POLICY, ROOM, WALLS (in that order)\n"
    "- Use rect or circle primitives only\n"
    "- Entity names must use underscores (e.g., COFFEE_TABLE not COFFEE TABLE)\n"
    "- anchor_wall must be: north, south, east, west, or none (for free placement)\n"
    "- All coordinates in mm, room centered at (0,0)\n"
    "- All objects must be within room bounds\n"
    "- Use circle for round objects (burners, round tables, columns)\n"
    "- Use rect for rectangular objects (tables, desks, appliances)\n\n"
    "Default dimensions if not specified:\n"
    "- Rooms: 3000x3000 (bedroom), 4000x3000 (kitchen), 2000x2000 (bathroom)\n"
    "- Simple shapes: r=100 (circles), 200x200 (squares), 300x200 (rectangles)\n"
)


def is_main_process() -> bool:
    # On this single-GPU run, RANK is usually unset → this returns True.
    return int(os.environ.get("RANK", "0")) == 0


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen2.5-Coder-3B-Instruct",
        help="Base model to fine-tune.",
    )
    parser.add_argument(
        "--data_path",
        type=str,
        default="/workspace/cadllm.jsonl",
        help="Path to CADLLM JSONL (instruction/input/output per line).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./cadllm",
        help="Where to save the final adapter/model.",
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=768,
        help="Max sequence length.",
    )
    parser.add_argument(
        "--per_device_train_batch_size",
        type=int,
        default=4,
        help="Per-GPU batch size.",
    )
    parser.add_argument(
        "--gradient_accumulation_steps",
        type=int,
        default=1,
        help="Gradient accumulation steps.",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=2e-4,
        help="Learning rate.",
    )
    parser.add_argument(
        "--num_train_epochs",
        type=float,
        default=1.0,
        help="Number of epochs.",
    )
    parser.add_argument(
        "--warmup_ratio",
        type=float,
        default=0.03,
        help="Warmup ratio.",
    )
    parser.add_argument(
        "--lr_scheduler_type",
        type=str,
        default="cosine",
        help="LR scheduler type.",
    )
    parser.add_argument(
        "--save_steps",
        type=int,
        default=500,
        help="Save checkpoint every N steps.",
    )
    parser.add_argument(
        "--logging_steps",
        type=int,
        default=50,
        help="Log every N steps.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=-1,
        help="If > 0, override num_train_epochs and train only this many optimizer steps.",
    )

    return parser.parse_args()


def format_example(example: Dict[str, Any]) -> Dict[str, Any]:
    """Format example as Qwen chat messages for better instruction following."""
    instruction = (example.get("instruction") or "").strip()
    inp = (example.get("input") or "").strip()
    out = (example.get("output") or "").strip()

    # Build user message
    user_text = instruction
    if inp and inp.lower() not in ["(none)", "none", ""]:
        user_text += "\n\nInput:\n" + inp

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": out},
        ]
    }


def load_model_and_tokenizer(model_name: str, tokenizer=None):
    if is_main_process():
        print(f"📥 Loading base model: {model_name}", flush=True)

    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
    
    tokenizer.padding_side = "right"

    bf16_supported = (
        torch.cuda.is_available()
        and hasattr(torch.cuda, "is_bf16_supported")
        and torch.cuda.is_bf16_supported()
    )
    dtype = torch.bfloat16 if bf16_supported else torch.float16

    model = AutoModelForCausalLM.from_pretrained(model_name, dtype=dtype)

    # Ensure vocab sizes match in case tokenizer is resized
    model.resize_token_embeddings(len(tokenizer))

    # LoRA config
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )
    model = get_peft_model(model, lora_config)

    # Save activation memory
    model.gradient_checkpointing_enable()
    if hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()

    if hasattr(model.config, "use_cache"):
        model.config.use_cache = False

    if is_main_process():
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())
        print("✅ Model + LoRA loaded", flush=True)
        print(f"   Trainable parameters: {trainable:,} / {total:,}", flush=True)

    return model, tokenizer


class CADDataCollator:
    """Collator that uses Qwen chat template and masks prompt tokens in loss."""
    def __init__(self, tokenizer, max_length: int):
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __call__(self, batch: List[Dict[str, Any]]):
        input_ids_list = []
        labels_list = []
        
        for ex in batch:
            messages = ex["messages"]
            
            # Full conversation (includes assistant answer)
            full = self.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=False,
                return_tensors=None
            )
            
            # Prefix up to assistant - use add_generation_prompt=True for cleaner masking
            prefix = self.tokenizer.apply_chat_template(
                messages[:-1],
                tokenize=True,
                add_generation_prompt=True,
                return_tensors=None
            )
            
            # Truncate to max_length
            full = full[:self.max_length]
            prefix_len = min(len(prefix), len(full))
            
            # Create labels: mask prompt portion, keep assistant response
            labels = full.copy()
            labels[:prefix_len] = [-100] * prefix_len  # Mask prompt tokens
            
            input_ids_list.append(torch.tensor(full, dtype=torch.long))
            labels_list.append(torch.tensor(labels, dtype=torch.long))
        
        # Pad sequences
        input_ids = torch.nn.utils.rnn.pad_sequence(
            input_ids_list, batch_first=True, padding_value=self.tokenizer.pad_token_id
        )
        labels = torch.nn.utils.rnn.pad_sequence(
            labels_list, batch_first=True, padding_value=-100
        )
        attention_mask = (input_ids != self.tokenizer.pad_token_id).long()
        
        # Mask padding tokens in labels
        labels[attention_mask == 0] = -100
        
        return {
            "input_ids": input_ids,
            "labels": labels,
            "attention_mask": attention_mask
        }


def main():
    args = parse_args()
    set_seed(args.seed)

    if is_main_process():
        print("======== LoRA CADLLM Fine-tuning (Qwen 3B) ========")
        print(f"Model:        {args.model_name}")
        print(f"Dataset file: {args.data_path}")
        print(f"Output dir:   {args.output_dir}")
        print(f"Max seq len:  {args.max_seq_length}")
        print(f"Epochs:       {args.num_train_epochs}")
        print(f"LR:           {args.learning_rate}")
        print(f"Per-GPU BS:   {args.per_device_train_batch_size}")
        print(f"Grad accum.:  {args.gradient_accumulation_steps}")
        print("===================================================")
        print("__ Loading CADLLM dataset...", flush=True)

    raw_dset = load_dataset("json", data_files=args.data_path)
    full_train = raw_dset["train"]

    # Shuffle before splitting to ensure representative eval set
    full_train = full_train.shuffle(seed=args.seed)
    
    # First 2k for eval, rest for train
    eval_size = min(2000, len(full_train))
    eval_raw = full_train.select(range(eval_size))
    train_raw = full_train.select(range(eval_size, len(full_train)))

    if is_main_process():
        print(f"   Total examples: {len(full_train)}", flush=True)
        print(f"   Train examples: {len(train_raw)}", flush=True)
        print(f"   Eval examples:  {len(eval_raw)}", flush=True)
        print("__ Loading tokenizer for length computation...", flush=True)
    
    # Load tokenizer early for length computation (needed for group_by_length)
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if is_main_process():
        print("__ Formatting examples and computing lengths...", flush=True)

    def format_and_compute_length(example):
        """Format example and compute tokenized length for group_by_length."""
        formatted = format_example(example)
        messages = formatted["messages"]
        # Compute length of full conversation
        full = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=False,
            return_tensors=None
        )
        formatted["length"] = len(full)
        return formatted

    train_dataset = train_raw.map(
        format_and_compute_length,
        remove_columns=train_raw.column_names,
    )
    eval_dataset = eval_raw.map(
        format_and_compute_length,
        remove_columns=eval_raw.column_names,
    )

    if is_main_process():
        print("__ Loading model...", flush=True)

    model, _ = load_model_and_tokenizer(args.model_name, tokenizer=tokenizer)
    data_collator = CADDataCollator(tokenizer, max_length=args.max_seq_length)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.num_train_epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        lr_scheduler_type=args.lr_scheduler_type,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=3,
        # Explicit evaluation strategy
        eval_strategy="steps",
        eval_steps=args.logging_steps,  # Evaluate at same frequency as logging
        save_strategy="steps",
        # Performance optimizations for NVIDIA GPUs
        optim="adamw_torch_fused",  # Faster on NVIDIA GPUs
        tf32=True,  # Enable TensorFloat-32 for faster training on Ampere+
        group_by_length=True,  # Group similar-length sequences to reduce padding
        bf16=(
            torch.cuda.is_available()
            and hasattr(torch.cuda, "is_bf16_supported")
            and torch.cuda.is_bf16_supported()
        ),
        report_to=[],
        remove_unused_columns=False,
        do_train=True,
        do_eval=True,
        # No DDP flags here – single GPU.
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    if is_main_process():
        print("🚀 Starting training...", flush=True)

    trainer.train()

    if is_main_process():
        print("✅ Training complete, saving model...", flush=True)

    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    if is_main_process():
        print("✅ All done.", flush=True)


if __name__ == "__main__":
    main()
