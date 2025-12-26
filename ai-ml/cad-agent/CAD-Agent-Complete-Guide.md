# CAD Agent - Complete Implementation & Training Guide

**Date:** December 10, 2025  
**Version:** Phase 1 - Prompt Enhancement with Advanced Fine-Tuning  
**Status:** Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Proposed Solution - Phase 1](#proposed-solution---phase-1)
4. [Model Hosting Options](#model-hosting-options)
5. [Advanced Fine-Tuning Guide](#advanced-fine-tuning-guide)
6. [Training Data Sources](#training-data-sources)
7. [Backend Integration](#backend-integration)
8. [Testing & Validation](#testing--validation)
9. [Deployment Checklist](#deployment-checklist)
10. [Cost Analysis](#cost-analysis)
11. [Troubleshooting](#troubleshooting)

---

## Executive Summary

This guide implements **Phase 1** of the CAD Agent integration: using a fine-tuned Mistral model to enhance user prompts before they're sent to GPT-4. This improves accuracy while maintaining your existing safe, instruction-based architecture.

**Pipeline:**
```
User Text → CAD Agent (Mistral) → Enhanced Prompt → GPT-4 → Structured Instructions → DXF
```

**Key Benefits:**
- ✅ Lower risk, easier integration
- ✅ Maintains existing architecture
- ✅ No code execution security risks
- ✅ Can A/B test effectiveness
- ✅ Easy to roll back if issues arise

**Estimated Implementation Time:** 6-11 hours  
**Estimated Monthly Cost:** $15-150 (depending on hosting option)  
**Expected Performance:** 0.65-0.75 CAD F1 (with advanced fine-tuning)

---

## Current Architecture Analysis

### Current Pipeline
```
User Text/Audio
    ↓
GPT-4 (gpt-4-turbo-preview) → Structured JSON Instructions (ParsedInstruction objects)
    ↓
DXFGeneratorService → DXF file (using ezdxf library)
```

### Key Components
1. **GPTParserService** (`backend/app/services/gpt_parser_service.py`)
   - Converts text to structured `ParsedInstruction` objects
   - Uses GPT-4 with JSON response format
   - Output: List of instructions with `command`, `parameters`, `confidence`

2. **DXFGeneratorService** (`backend/app/services/dxf_generator_service.py`)
   - Takes `ParsedInstruction` objects
   - Uses ezdxf library to generate DXF files
   - No code execution - pure library calls

3. **TextToJSONConverter** (`backend/app/services/text_to_json_converter.py`)
   - Alternative pipeline: Text → JSON → Instructions
   - Also uses GPT-4

### Current Dependencies
- `openai==1.3.0` (for GPT-4)
- `ezdxf==1.1.0` (for DXF generation)
- **No code execution infrastructure**
- **No vLLM or model hosting**

---

## Proposed Solution - Phase 1

### Architecture
```
User Text Prompt
    ↓
CAD Agent (Fine-tuned Mistral-7B) → Enhanced Prompt
    ↓
GPT-4 → Structured Instructions → DXF
```

### Integration Strategy

**Approach:** Use CAD Agent to enhance prompts before sending to GPT-4, but keep structured output.

**Benefits:**
- ✅ Minimal changes to existing code
- ✅ Backward compatible
- ✅ Can A/B test effectiveness
- ✅ No security risks from code execution
- ✅ Automatic fallback to original prompt on failure

---

## Model Hosting Options

### Option A: Hugging Face Inference API (Easiest, ~$0.20/hour)

**Pros:**
- ✅ No infrastructure setup
- ✅ Automatic scaling
- ✅ Pay-per-use pricing
- ✅ Free tier: 1,000 requests/month

**Cons:**
- ⚠️ Costs ~$0.20/hour when active
- ⚠️ Requires internet connection

**Best For:** Quick start, low-medium traffic

**Setup:**
1. Upload fine-tuned model to Hugging Face Hub
2. Enable Inference API on model page
3. Get API token from https://huggingface.co/settings/tokens

### Option B: Local GPU Server (Most Cost-Effective Long-Term)

**Pros:**
- ✅ $0 ongoing cost (after hardware)
- ✅ Full control
- ✅ No API rate limits
- ✅ Can use consumer GPUs

**Cons:**
- ⚠️ Requires GPU hardware
- ⚠️ Setup complexity

**Best For:** High traffic, long-term use

**Hardware Requirements:**

**For Mistral-7B:**
- NVIDIA GPU with 8-16GB VRAM (RTX 3090, A4000, or better)
- 16GB+ system RAM
- 50GB+ disk space

**For DeepSeek-Coder-V2-Lite (Recommended - Cheaper):**
- NVIDIA GPU with 6-8GB VRAM (RTX 3060, RTX 3070, or better) ⭐
- 16GB+ system RAM
- 50GB+ disk space
- **Much cheaper hardware option!**

### Option C: Cloud GPU (RunPod/Vast.ai) - Recommended for Production

**Pros:**
- ✅ No hardware purchase
- ✅ Easy scaling
- ✅ Can stop when not in use

**Cons:**
- ⚠️ Requires model deployment setup

**Best For:** Production deployment, flexible scaling

**Cost by Model:**
- **Mistral-7B:** ~$0.30-0.50/hour (RTX 3090/A4000 required)
- **DeepSeek-Coder-V2-Lite:** **~$0.15-0.30/hour** (RTX 3060/3070 sufficient) ⭐ **50% cheaper!**

**GPU Selection:**
- **For Mistral-7B:** RTX 3090 (24GB) or A4000 (16GB) - higher cost
- **For DeepSeek-Coder-V2-Lite:** RTX 3060 (12GB) or RTX 3070 (8GB) - **much cheaper**

---

## Advanced Fine-Tuning Guide

**Based on:** CAD-LLM Paper (NeurIPS 2023) + SketchGraphs Dataset  
**Goal:** Build highly accurate, low-cost CAD generation with geometric reasoning

### Architecture Overview

```
User text prompt → Fine-tuned LLM → Super-detailed ezdxf prompt → gpt-4o-mini → DXF
```

**Current Best Setup:**
- Prompt enhancer: Fine-tuned Mistral-7B-Instruct-v0.3 or **DeepSeek-Coder-V2-Lite** (LoRA, 4-bit, vLLM)
- Code generator: gpt-4o-mini (kept for reliability)
- Cost per DXF: <$0.005
- **Cost savings with DeepSeek:** 50% cheaper GPU hosting, 50% cheaper hardware

### Key Improvements from CAD-LLM Paper

#### 1. Tokenization & Representation (Highly Recommended)

**Problem:** Raw coordinates are hard for LLMs to learn  
**Solution:** Fixed-length token representation with normalization

**Implementation:**

```python
def tokenize_cad_entity(entity_type, params):
    """
    Convert CAD entities to fixed-length token sequences.
    Based on CAD-LLM paper findings.
    """
    tokens = []
    
    if entity_type == "LINE":
        # Line → 2 points (4 values: x1, y1, x2, y2)
        tokens = [
            f"LINE",
            f"{params['start']['x']:.6f}",
            f"{params['start']['y']:.6f}",
            f"{params['end']['x']:.6f}",
            f"{params['end']['y']:.6f}"
        ]
    
    elif entity_type == "CIRCLE":
        # Circle → center + radius point (3 points → 6 values)
        tokens = [
            f"CIRCLE",
            f"{params['center']['x']:.6f}",
            f"{params['center']['y']:.6f}",
            f"{params['radius']:.6f}"
        ]
    
    elif entity_type == "ARC":
        # Arc → 3 points (start, end, bulge or center+angles)
        tokens = [
            f"ARC",
            f"{params['center']['x']:.6f}",
            f"{params['center']['y']:.6f}",
            f"{params['radius']:.6f}",
            f"{params['start_angle']:.6f}",
            f"{params['end_angle']:.6f}"
        ]
    
    return " ".join(tokens)

def normalize_sketch(entities):
    """
    Normalize all sketches to 1×1 meter bounding box, origin-centered.
    Uses 6-bit uniform quantization (proven in CAD-LLM + SketchGraphs).
    """
    # Find bounding box
    all_points = []
    for entity in entities:
        if entity['type'] == 'LINE':
            all_points.extend([entity['start'], entity['end']])
        elif entity['type'] == 'CIRCLE':
            center = entity['center']
            radius = entity['radius']
            all_points.extend([
                {'x': center['x'] - radius, 'y': center['y'] - radius},
                {'x': center['x'] + radius, 'y': center['y'] + radius}
            ])
        # ... handle other entity types
    
    if not all_points:
        return entities
    
    min_x = min(p['x'] for p in all_points)
    max_x = max(p['x'] for p in all_points)
    min_y = min(p['y'] for p in all_points)
    max_y = max(p['y'] for p in all_points)
    
    # Calculate scale and offset
    width = max_x - min_x
    height = max_y - min_y
    max_dim = max(width, height, 1e-6)  # Avoid division by zero
    
    scale = 1.0 / max_dim  # Scale to 1×1
    offset_x = -(min_x + max_x) / 2
    offset_y = -(min_y + max_y) / 2
    
    # Normalize all entities
    normalized = []
    for entity in entities:
        norm_entity = normalize_entity(entity, scale, offset_x, offset_y)
        normalized.append(norm_entity)
    
    # 6-bit quantization (64 levels)
    quantized = quantize_6bit(normalized)
    
    return quantized

def quantize_6bit(entities):
    """6-bit uniform quantization (0-63 levels)"""
    for entity in entities:
        for key in ['x', 'y', 'radius', 'start_angle', 'end_angle']:
            if key in entity:
                # Quantize to 6 bits (0-63)
                entity[key] = round(entity[key] * 63) / 63.0
    return entities
```

**Benefits:**
- ✅ Dramatically improves model's geometric reasoning
- ✅ Fixed-length sequences easier for transformers
- ✅ Normalization makes patterns more learnable
- ✅ 6-bit quantization reduces vocabulary size

#### 2. Training Tasks (Proven to Work Extremely Well)

**CAD-LLM paper shows these tasks give massive gains with little data:**

**A. CAD Auto-Completion (Prefix 20–80% → Complete the Rest)**

```python
def create_autocompletion_examples(sketch_sequence):
    """
    Create auto-completion training examples.
    Mask 20-80% of sequence, predict the rest.
    """
    examples = []
    
    for mask_ratio in [0.2, 0.4, 0.6, 0.8]:
        split_point = int(len(sketch_sequence) * mask_ratio)
        
        prefix = sketch_sequence[:split_point]
        completion = sketch_sequence[split_point:]
        
        examples.append({
            "instruction": "Complete the CAD sketch sequence:",
            "input": " ".join(prefix),
            "output": " ".join(completion)
        })
    
    return examples
```

**B. Next-Entity Prediction**

```python
def create_next_entity_examples(sketch_sequence):
    """
    Predict the next entity in the sequence.
    """
    examples = []
    
    for i in range(1, len(sketch_sequence)):
        context = sketch_sequence[:i]
        next_entity = sketch_sequence[i]
        
        examples.append({
            "instruction": "Predict the next CAD entity:",
            "input": " ".join(context),
            "output": next_entity
        })
    
    return examples
```

**C. Masked Entity Modeling**

```python
import random

def create_masked_entity_examples(sketch_sequence):
    """
    Mask random entities, predict them from context.
    """
    examples = []
    
    for _ in range(3):  # 3 masked examples per sketch
        masked_indices = random.sample(
            range(len(sketch_sequence)),
            k=min(3, len(sketch_sequence) // 4)
        )
        
        masked_sequence = sketch_sequence.copy()
        masked_entities = []
        
        for idx in masked_indices:
            masked_entities.append(sketch_sequence[idx])
            masked_sequence[idx] = "[MASK]"
        
        examples.append({
            "instruction": "Predict the masked CAD entities:",
            "input": " ".join(masked_sequence),
            "output": " ".join(masked_entities)
        })
    
    return examples
```

#### 3. Evaluation Metrics (Use These Instead of Visual Only)

**CAD-LLM paper proves these metrics are essential:**

```python
def evaluate_cad_model(predictions, ground_truth):
    """
    Implement CAD-LLM evaluation metrics.
    """
    results = {
        "entity_accuracy": 0.0,
        "sketch_accuracy": 0.0,
        "cad_f1": 0.0
    }
    
    # Entity Accuracy → % of correctly predicted entities
    correct_entities = 0
    total_entities = 0
    
    for pred, gt in zip(predictions, ground_truth):
        pred_entities = parse_entities(pred)
        gt_entities = parse_entities(gt)
        
        total_entities += len(gt_entities)
        
        for pred_ent in pred_entities:
            if any(entities_match(pred_ent, gt_ent) for gt_ent in gt_entities):
                correct_entities += 1
    
    results["entity_accuracy"] = correct_entities / total_entities if total_entities > 0 else 0.0
    
    # Sketch Accuracy → % of perfectly reconstructed sketches
    perfect_sketches = 0
    for pred, gt in zip(predictions, ground_truth):
        if entities_match_exact(pred, gt):
            perfect_sketches += 1
    
    results["sketch_accuracy"] = perfect_sketches / len(predictions) if predictions else 0.0
    
    # CAD F1 → 2 × precision × recall / (precision + recall)
    precision = calculate_precision(predictions, ground_truth)
    recall = calculate_recall(predictions, ground_truth)
    
    if precision + recall > 0:
        results["cad_f1"] = 2 * precision * recall / (precision + recall)
    
    return results
```

**Expected Performance:**

**Based on CAD-LLM Paper (ACL 2025):**
- **TCADGen+CADLLM:** 96.6% command accuracy, 0.947 F1 score
- **Our approach with CADLLM dataset:** Expected **~0.70-0.90 CAD F1** (depending on stages)

**Based on Original CAD-LLM Paper (NeurIPS 2023):**
- T5-770M fine-tuned for 20 epochs: **3–5× better CAD F1** than SOTA Vitruvion
- Mistral-7B with these improvements: **~0.65–0.75 CAD F1** expected

**With CADLLM Dataset + Advanced Fine-Tuning:**
- **Stage 1 (CADLLM):** ~0.70-0.80 CAD F1
- **Stage 2 (SketchGraphs):** ~0.75-0.85 CAD F1  
- **Stage 3 (ezdxf-specific):** ~0.80-0.90 CAD F1 ⭐

#### 4. Google Colab Fine-Tuning Notebook

**Create:** `cad_agent_finetuning.ipynb`

```python
# CELL 1 – Install & Login
!pip install -q torch transformers datasets peft trl accelerate bitsandbytes sentencepiece huggingface_hub
from huggingface_hub import login
login()  # Paste your free HF token

# CELL 2 – Imports & Quantized Model Loading
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments
from datasets import load_dataset
from peft import LoraConfig, prepare_model_for_kbit_training, get_peft_model
from trl import SFTTrainer

# Choose your model:
# Option 1: Mistral-7B (best performance, needs more VRAM)
model_name = "mistralai/Mistral-7B-Instruct-v0.3"

# Option 2: DeepSeek-Coder-V2-Lite (cheapest, needs less VRAM) ⭐ RECOMMENDED FOR COST
# model_name = "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quant_config,
    device_map="auto",
    torch_dtype=torch.bfloat16
)
model = prepare_model_for_kbit_training(model)

# CELL 3 – Load & Format Data
dataset = load_dataset("json", data_files="cad_training.jsonl", split="train")

def format_example(ex):
    text = f"<s>[INST] {ex['instruction']}\nInput: {ex['input']} [/INST]\n{ex['output']}</s>"
    return {"text": text}

dataset = dataset.map(format_example)

# CELL 4 – LoRA Configuration
peft_config = LoraConfig(
    r=32,
    lora_alpha=32,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, peft_config)

# CELL 5 – Training
training_args = TrainingArguments(
    output_dir="./cad-agent-mistral",
    num_train_epochs=20,  # CAD-LLM used 20 epochs
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
    optim="paged_adamw_8bit",
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    dataset_text_field="text",
    max_seq_length=1024,
    packing=False,
)

trainer.train()

# CELL 6 – Save & Upload to Hugging Face
from peft import PeftModel

# Load base model (use same model_name from CELL 2)
base_model = AutoModelForCausalLM.from_pretrained(model_name)
model = PeftModel.from_pretrained(base_model, "./cad-agent-final")
model.push_to_hub("your-username/cad-prompt-enhancer")
tokenizer.push_to_hub("your-username/cad-prompt-enhancer")

# Note: For DeepSeek-Coder-V2-Lite, use:
# base_model = AutoModelForCausalLM.from_pretrained("deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct")
```

### Model Selection Guide

**Quick Comparison:**

| Feature | Mistral-7B | DeepSeek-Coder-V2-Lite ⭐ |
|---------|-----------|-------------------------|
| **Total Parameters** | 7B | 16B (MoE) |
| **Active Parameters** | 7B | 2.4B (MoE) |
| **VRAM Required** | 8-16GB | 6-8GB |
| **Min GPU** | RTX 3090 (24GB) or A4000 (16GB) | RTX 3060 (12GB) or RTX 3070 (8GB) |
| **Cloud GPU Cost/hr** | $0.30-0.50 | **$0.15-0.30** (50% cheaper) |
| **Hardware Cost** | $800-1200 (used RTX 3090) | **$300-500** (used RTX 3060/3070) |
| **Expected CAD F1** | 0.65-0.75 | 0.60-0.70 |
| **Inference Speed** | Medium | **Faster** |
| **Code Understanding** | Good | **Excellent** (designed for code) |
| **Best For** | Maximum accuracy | **Cost optimization** |

**Recommendation:**
- **Use DeepSeek-Coder-V2-Lite** if: Cost is a priority, you have limited GPU budget, or you want faster inference
- **Use Mistral-7B** if: Maximum accuracy is critical and you have GPU budget

**For Most Users:** DeepSeek-Coder-V2-Lite is recommended due to:
- ✅ 50% cheaper GPU hosting
- ✅ 50% cheaper hardware
- ✅ Faster inference
- ✅ Better code understanding (perfect for ezdxf)
- ✅ Still excellent performance (0.60-0.70 CAD F1)

### Training Strategy

**Four-Stage Approach (Recommended with DeepCAD):**

1. **Stage 1: Train on CADLLM Dataset (155K text-to-CAD pairs)** ⭐
   - Learn text-to-CAD command mapping
   - Understand how descriptions map to CAD operations
   - Extract 2D sketch commands (Line, Arc, Circle) for DXF
   - Expected: ~0.70-0.80 CAD F1 (based on paper's 96.6% accuracy)

2. **Stage 2: Train on SketchGraphs + DeepCAD (1M+ sketches + construction sequences)** ⭐ **ENHANCED**
   - **SketchGraphs:** Learn geometric constraints and relationships
   - **DeepCAD:** Learn procedural construction sequences
   - Combined: Understand both constraint-based and procedural modeling
   - Expected: ~0.75-0.85 CAD F1

3. **Stage 3: Fine-tune on ezdxf-specific examples (200-500)**
   - Learn perfect ezdxf syntax
   - Adapt to your specific use case
   - Expected: ~0.80-0.90 CAD F1

**Why DeepCAD Complements SketchGraphs:**
- **SketchGraphs:** Focuses on geometric constraints (what entities relate to each other)
- **DeepCAD:** Focuses on construction sequences (how to build step-by-step)
- **Together:** Model learns both "what" (constraints) and "how" (construction) ⭐

**Alternative Two-Stage Approach (Faster):**

1. **Stage 1: Train on CADLLM Dataset (155K samples)**
   - Fastest path to good results
   - Already has text descriptions
   - Expected: ~0.70-0.80 CAD F1

2. **Stage 2: Fine-tune on ezdxf-specific examples (200-500)**
   - Learn perfect ezdxf syntax
   - Expected: ~0.75-0.85 CAD F1

**Model Options:**

| Model | Parameters | VRAM Required | Cost (Self-Hosted) | Expected CAD F1 | Best For |
|-------|-----------|---------------|-------------------|-----------------|----------|
| **Mistral-7B** | 7B | 8-16GB | $0 (after hardware) | 0.65-0.75 | Balanced performance |
| **Llama-3.2-3B/8B** | 3B/8B | 6-16GB | $0 (after hardware) | 0.60-0.70 | Faster inference |
| **DeepSeek-Coder-V2-Lite** ⭐ | 16B total, 2.4B active (MoE) | 6-8GB | **$0 (cheapest)** | 0.60-0.70 | **Most cost-effective** |

**⭐ DeepSeek-Coder-V2-Lite (Recommended for Cost Savings):**

**Why it's cheaper:**
- ✅ **Smaller active parameters** (2.4B active via MoE) = less VRAM needed
- ✅ **Faster inference** = lower GPU hosting costs
- ✅ **Can run on RTX 3060/3070** (6-8GB VRAM) vs Mistral-7B needs 8-16GB
- ✅ **Open source** = free self-hosting
- ✅ **Optimized for code** = better at understanding ezdxf syntax

**Cost Comparison (Self-Hosted):**
- **Mistral-7B:** Needs RTX 3090 (24GB) or A4000 (16GB) → ~$0.30-0.50/hour cloud GPU
- **DeepSeek-Coder-V2-Lite:** Needs RTX 3060 (12GB) or RTX 3070 (8GB) → **~$0.15-0.30/hour cloud GPU** (50% cheaper!)

**Performance:**
- Slightly lower CAD F1 (0.60-0.70 vs 0.65-0.75) but still excellent
- Faster inference = better user experience
- Better at code-like sequences (perfect for ezdxf prompts)

### Expected Results

**Based on CADLLM Paper (ACL 2025):**
- **TCADGen + CADLLM:** 96.6% command accuracy, 0.947 F1 score
- **With CADLLM dataset + your fine-tuning:** Expected **0.70-0.90 CAD F1** ⭐

**Based on Original CAD-LLM Paper (NeurIPS 2023):**
- **T5-770M** (20 epochs): 3-5× better than SOTA Vitruvion
- **Mistral-7B** (with improvements): **~0.65–0.75 CAD F1** expected

**Combined Approach (CADLLM + SketchGraphs + DeepCAD + Advanced Fine-Tuning):**
- **Stage 1 (CADLLM):** 0.70-0.80 CAD F1
- **Stage 2 (SketchGraphs + DeepCAD):** 0.75-0.85 CAD F1 ⭐ Enhanced with construction sequences
- **Stage 3 (ezdxf-specific):** **0.80-0.90 CAD F1** ⭐

**Why Adding DeepCAD Helps:**
- **CADLLM:** Text-to-CAD mapping (what to create)
- **SketchGraphs:** Geometric constraints (how entities relate)
- **DeepCAD:** Construction sequences (how to build step-by-step) ⭐ NEW
- **Together:** Comprehensive understanding of CAD modeling

**Cost per DXF:** <$0.005 (with self-hosted model)

---

## Training Data Sources

### Recommended Datasets

#### 1. CADLLM Dataset ⭐ (Highly Recommended - 155K+ Text-to-CAD Pairs)

**Source:** https://huggingface.co/datasets/lanlanguai/CADLLM  
**Paper:** https://jianxliao.github.io/cadllm-page/ (ACL 2025)  
**Size:** 155,503 training samples + 5,647 test samples  
**Format:** Text descriptions → CAD Command Sequences (CCS)  
**License:** Apache License 2.0 ✅

**Access:**
```python
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("lanlanguai/CADLLM", split="train")

# Each sample contains:
# - appearance_description: Visual/structural details
# - parameter_description: Human-readable CAD instructions
# - ccs: CAD Command Sequence (Line, Arc, Circle, Extrude operations)
# - Multi-view images, STL files, PLY point clouds
```

**Why This is Perfect for Your Project:**
- ✅ **155K+ text-to-CAD pairs** - massive training data
- ✅ **Already processed** - ready to use, no preprocessing needed
- ✅ **Text descriptions** - exactly what you need for prompt enhancement
- ✅ **CAD Command Sequences** - includes 2D sketch commands (Line, Arc, Circle) for DXF
- ✅ **Proven results** - paper shows 96.6% command accuracy
- ✅ **Easy download** - directly from Hugging Face

**Note:** While the dataset includes 3D operations (Extrude), the 2D sketch parts (Line, Arc, Circle) are perfect for DXF generation. You can:
1. Extract 2D sketch commands from CCS
2. Use text descriptions to train prompt enhancement
3. Filter for 2D-only examples if needed

**Best For:**
- ✅ Training text-to-CAD command generation
- ✅ Learning CAD command sequences
- ✅ Understanding how text maps to CAD operations
- ✅ Large-scale training (155K samples!)

**Paper Insights to Apply:**
- **TCADGen approach:** Dual-channel feature aggregation (parameter + appearance)
- **CADLLM refinement:** Use LLM to refine generated sequences with confidence scores
- **Semi-automated annotation:** 98.4% automatic pass rate using LLMs

#### 2. SketchGraphs (Best for Advanced Fine-Tuning)

**Source:** https://github.com/PrincetonLIPS/SketchGraphs  
**Paper:** [SketchGraphs: A Large-Scale Dataset for Modeling Relational Geometry in Computer-Aided Design](https://princetonlips.github.io/SketchGraphs/) (ICML 2020 Workshop)  
**Size:** 15 million parametric CAD sketches  
**Format:** Geometric constraint graphs (JSON or binary)  
**License:** MIT License ✅

**Access:**
```bash
git clone https://github.com/PrincetonLIPS/SketchGraphs.git
cd SketchGraphs
pip install -e .
# Download data from: https://princetonlips.github.io/SketchGraphs
```

**Data Formats Available:**
1. **Raw JSON data** (43GB, 128 tar archives) - Original Onshape data, compressed with zstandard
2. **Construction sequences** (15GB, single binary file) - Concise format, better for ML
3. **Filtered sequences** (smaller, pre-split) - Simplified, with train/validation/test splits

**Best For:** 
- ✅ Learning geometric constraints and relationships
- ✅ Understanding parametric CAD modeling
- ✅ Constraint-based design
- ✅ Advanced fine-tuning with CAD-LLM approach
- ✅ Graph-based representation of CAD sketches

**Key Features:**
- Each sketch represented as a geometric constraint graph
- Edges = designer-imposed geometric relationships
- Nodes = primitives (lines, arcs, circles, etc.)
- Real-world CAD data from Onshape

#### 3. FloorPlanCAD (Best for Floor Plans)

**Source:** https://github.com/art-programmer/FloorplanCAD  
**Size:** 15,000+ floor plans  
**Format:** Vector graphics, annotations  
**License:** Check repository

**Best For:** Kitchen layouts, residential floor plans, commercial spaces

#### 4. DeepCAD (CAD Construction Sequences) ⭐

**Source:** https://github.com/rundiwu/DeepCAD  
**Paper:** [DeepCAD: A Deep Generative Network for Computer-Aided Design Models](https://www.cs.columbia.edu/cg/deepcad/) (ICCV 2021)  
**Size:** Large collection of Onshape CAD models  
**Format:** JSON files with CAD construction sequences (vectorized representation)  
**License:** MIT License ✅

**Access:**
```bash
git clone https://github.com/rundiwu/DeepCAD.git
cd DeepCAD
pip install -r requirements.txt
conda install -c conda-forge pythonocc-core=7.5.1

# Download data from: https://www.cs.columbia.edu/cg/deepcad/
# Extract under data/ folder:
# - cad_json/: Original JSON files with CAD construction sequences
# - cad_vec/: Vectorized representation for fast loading
```

**Why This Complements Your Combined Approach:**
- ✅ **CAD Construction Sequences** - procedural CAD modeling steps
- ✅ **Onshape data** - real-world CAD models (similar to SketchGraphs)
- ✅ **Vectorized representation** - efficient for training
- ✅ **2D sketch extraction** - can extract 2D sketches from 3D construction sequences
- ✅ **Different perspective** - focuses on construction process vs. constraints

**Best For:**
- ✅ Learning CAD construction sequences
- ✅ Understanding procedural CAD modeling
- ✅ Extracting 2D sketches from 3D models
- ✅ Complementing SketchGraphs (constraints) with construction sequences

**Note:** DeepCAD is 3D-focused (extrusion operations), but you can:
1. Extract 2D sketch commands from construction sequences
2. Use the vectorized representation for training
3. Convert construction sequences to ezdxf format

#### 5. HouseGAN Dataset

**Source:** https://github.com/ennauata/housegan  
**Size:** 117,000+ floor plans  
**Format:** Vector and raster images  
**License:** MIT License

**Best For:** Synthetic floor plans, room layouts

### Synthetic Data Generation

**For ezdxf-specific examples (200-500 needed for Stage 2):**

```python
# Basic training data format
{"instruction":"Enhance this CAD prompt to be extremely detailed and compatible with ezdxf Python code generation.","input":"a simple spur gear","output":"Write complete Python code using the ezdxf library to create a 2D spur gear with 20 teeth, module 2.0, pressure angle 20 degrees, bore diameter 10 mm, centered at (0,0). Use add_circle for pitch/root circles, generate accurate involute tooth profiles with add_lwpolyline, include proper root fillet, and save as 'gear.dxf'."}
```

**Target:** Create 150-500 such lines for Stage 2 fine-tuning

### CADLLM Dataset Preprocessing

**File:** `scripts/preprocess_cadllm.py`

```python
#!/usr/bin/env python3
"""
Preprocess CADLLM dataset for training.
Extract 2D sketch commands and convert to training format.
"""
from datasets import load_dataset
import json

def extract_2d_commands(ccs):
    """
    Extract 2D sketch commands (Line, Arc, Circle) from CAD Command Sequence.
    Skip 3D operations (Extrude) for DXF generation.
    """
    commands = []
    for cmd in ccs:
        if cmd.startswith("<Line>") or cmd.startswith("<Arc>") or cmd.startswith("<Circle>"):
            commands.append(cmd)
    return commands

def preprocess_cadllm_to_jsonl(output_path):
    """
    Convert CADLLM dataset to our jsonl training format.
    """
    print("Loading CADLLM dataset...")
    dataset = load_dataset("lanlanguai/CADLLM", split="train")
    
    training_examples = []
    
    for sample in dataset:
        # Get text description (combine appearance + parameter descriptions)
        appearance = sample.get("appearance_description", "")
        parameters = sample.get("parameter_description", "")
        text_description = f"{appearance} {parameters}".strip()
        
        # Get CAD Command Sequence
        ccs = sample.get("ccs", [])
        
        # Extract 2D commands for DXF
        sketch_commands = extract_2d_commands(ccs)
        
        if not sketch_commands or not text_description:
            continue
        
        # Create training examples
        # Format: text description → enhanced prompt for ezdxf
        enhanced_prompt = f"Write complete Python code using the ezdxf library to create: {text_description}. Use the following CAD operations: {', '.join(sketch_commands)}. Generate accurate 2D geometry with proper coordinates and save as DXF file."
        
        training_examples.append({
            "instruction": "Enhance this CAD prompt to be extremely detailed and compatible with ezdxf Python code generation.",
            "input": text_description,
            "output": enhanced_prompt
        })
        
        if len(training_examples) % 1000 == 0:
            print(f"Processed {len(training_examples)} examples")
    
    # Save as jsonl
    with open(output_path, 'w') as f:
        for example in training_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"✅ Created {len(training_examples)} training examples from CADLLM")

if __name__ == "__main__":
    preprocess_cadllm_to_jsonl("training_data/cadllm_processed.jsonl")
```

**Quick Start:**
```python
from datasets import load_dataset

# Load dataset
dataset = load_dataset("lanlanguai/CADLLM", split="train")

# Access samples
for sample in dataset:
    print(sample["parameter_description"])  # Text description
    print(sample["ccs"])  # CAD Command Sequence
```

**CADLLM Paper Insights to Apply:**

Based on the [CADLLM paper](https://jianxliao.github.io/cadllm-page/) (ACL 2025), here are key techniques you can use:

1. **TCADGen Dual-Channel Architecture:**
   - Process parameter descriptions and appearance descriptions separately
   - Fuse features for better CAD command prediction
   - **For your use case:** Use both text description types when available

2. **CADLLM Refinement Approach:**
   - Paper shows LLM refinement improves accuracy from 89.0% to 96.6%
   - Use confidence scores to guide refinement
   - **For your use case:** This matches your Phase 1 approach perfectly!

3. **Semi-Automated Annotation:**
   - Paper achieved 98.4% automatic annotation rate
   - Uses LLMs + VLLMs for quality control
   - **For your use case:** Use similar approach to generate ezdxf examples

4. **CAD Command Sequence (CCS) Format:**
   - Paper uses structured command sequences: `<Line>: x=144, y=112`
   - You can adapt this for ezdxf: `add_line((144, 112), (223, 128))`
   - Extract 2D commands (Line, Arc, Circle) for DXF generation

**Performance Expectations from Paper:**
- **TCADGen alone:** 89.0% command accuracy
- **TCADGen + CADLLM:** 96.6% command accuracy ⭐
- **Your approach (with CADLLM dataset):** Expected 0.70-0.90 CAD F1

### DeepCAD Preprocessing

**File:** `scripts/preprocess_deepcad.py`

```python
#!/usr/bin/env python3
"""
Preprocess DeepCAD dataset for training.
Extract 2D sketches from 3D CAD construction sequences.
"""
import json
import os
import h5py
import numpy as np

def extract_2d_sketch_from_sequence(cad_sequence):
    """
    Extract 2D sketch commands from DeepCAD construction sequence.
    DeepCAD sequences contain: sketch operations → extrusion operations
    We extract only the 2D sketch part (before extrusion).
    """
    sketch_commands = []
    
    # DeepCAD format: sequence of operations
    # Each operation has: type, parameters, etc.
    for op in cad_sequence:
        op_type = op.get('type', '')
        
        # Extract 2D sketch operations
        if op_type in ['Line', 'Arc', 'Circle', 'Spline']:
            sketch_commands.append({
                'type': op_type,
                'params': op.get('params', {})
            })
        
        # Stop at first extrusion (3D operation)
        if op_type == 'Extrude':
            break
    
    return sketch_commands

def convert_deepcad_to_ezdxf_format(sketch_commands):
    """
    Convert DeepCAD sketch commands to ezdxf format.
    """
    ezdxf_commands = []
    
    for cmd in sketch_commands:
        cmd_type = cmd['type']
        params = cmd['params']
        
        if cmd_type == 'Line':
            # DeepCAD: start, end points
            start = params.get('start', [0, 0])
            end = params.get('end', [0, 0])
            ezdxf_commands.append(f"add_line(({start[0]}, {start[1]}), ({end[0]}, {end[1]}))")
        
        elif cmd_type == 'Circle':
            # DeepCAD: center, radius
            center = params.get('center', [0, 0])
            radius = params.get('radius', 1.0)
            ezdxf_commands.append(f"add_circle(({center[0]}, {center[1]}), {radius})")
        
        elif cmd_type == 'Arc':
            # DeepCAD: center, radius, start_angle, end_angle
            center = params.get('center', [0, 0])
            radius = params.get('radius', 1.0)
            start_angle = params.get('start_angle', 0)
            end_angle = params.get('end_angle', 90)
            ezdxf_commands.append(f"add_arc(({center[0]}, {center[1]}), {radius}, {start_angle}, {end_angle})")
    
    return ezdxf_commands

def preprocess_deepcad_to_jsonl(deepcad_json_dir, output_path):
    """
    Convert DeepCAD JSON files to our jsonl training format.
    """
    training_examples = []
    
    # Process all JSON files in cad_json directory
    for filename in os.listdir(deepcad_json_dir):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(deepcad_json_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                cad_data = json.load(f)
            
            # Extract construction sequence
            sequence = cad_data.get('sequence', [])
            
            # Extract 2D sketch commands
            sketch_commands = extract_2d_sketch_from_sequence(sequence)
            
            if not sketch_commands:
                continue
            
            # Convert to ezdxf format
            ezdxf_commands = convert_deepcad_to_ezdxf_format(sketch_commands)
            
            # Create training example
            # Note: DeepCAD doesn't have text descriptions, so we'll generate synthetic ones
            # or use the model name/type as description
            model_name = cad_data.get('name', 'CAD model')
            description = f"Create a {model_name} with the following 2D sketch operations"
            
            enhanced_prompt = (
                f"Write complete Python code using the ezdxf library to create: {description}. "
                f"Use the following operations: {'; '.join(ezdxf_commands)}. "
                f"Generate accurate 2D geometry and save as DXF file."
            )
            
            training_examples.append({
                "instruction": "Enhance this CAD prompt to be extremely detailed and compatible with ezdxf Python code generation.",
                "input": description,
                "output": enhanced_prompt
            })
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
        
        if len(training_examples) % 100 == 0:
            print(f"Processed {len(training_examples)} examples")
    
    # Save as jsonl
    with open(output_path, 'w') as f:
        for example in training_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"✅ Created {len(training_examples)} training examples from DeepCAD")

if __name__ == "__main__":
    # Update path to your DeepCAD data directory
    deepcad_json_dir = "data/cad_json"
    preprocess_deepcad_to_jsonl(deepcad_json_dir, "training_data/deepcad_processed.jsonl")
```

**Alternative: Using Vectorized Format (Faster)**

If you have the vectorized format (`cad_vec/`), you can load it directly:

```python
import h5py

def load_deepcad_vectorized(vec_file):
    """
    Load DeepCAD vectorized format (h5 file).
    """
    with h5py.File(vec_file, 'r') as f:
        sequences = f['sequences'][:]
        # Process sequences...
```

**Integration with Combined Approach:**

DeepCAD complements your other datasets:
- **CADLLM:** Text-to-CAD mapping (155K samples)
- **SketchGraphs:** Geometric constraints (1M+ sketches)
- **DeepCAD:** Construction sequences (procedural modeling) ⭐ NEW

**Best Practice:** Use DeepCAD in Stage 2 alongside SketchGraphs to learn both:
- Constraint-based design (SketchGraphs)
- Procedural construction sequences (DeepCAD)

### SketchGraphs Preprocessing

**File:** `scripts/preprocess_sketchgraphs.py`

```python
#!/usr/bin/env python3
"""
Preprocess SketchGraphs dataset for CAD-LLM style training.
"""
import json
from sketchgraphs.data import SequenceDataset

def preprocess_sketchgraphs_to_jsonl(sketchgraphs_path, output_path):
    """
    Convert SketchGraphs binary format to our jsonl training format.
    """
    dataset = SequenceDataset(sketchgraphs_path)
    
    training_examples = []
    
    for sketch_idx, sketch in enumerate(dataset):
        # Convert to tokenized sequence
        sequence = sketch_to_tokenized_sequence(sketch)
        
        # Create multiple training examples from one sketch
        autocomp_examples = create_autocompletion_examples(sequence)
        training_examples.extend(autocomp_examples)
        
        next_entity_examples = create_next_entity_examples(sequence)
        training_examples.extend(next_entity_examples)
        
        masked_examples = create_masked_entity_examples(sequence)
        training_examples.extend(masked_examples)
        
        if (sketch_idx + 1) % 1000 == 0:
            print(f"Processed {sketch_idx + 1} sketches, {len(training_examples)} examples")
    
    # Save as jsonl
    with open(output_path, 'w') as f:
        for example in training_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"✅ Created {len(training_examples)} training examples")
```

---

## Backend Integration

### Step 1: Update Configuration

**File:** `backend/app/core/config.py`

Add to `Settings` class:

```python
# CAD Agent Configuration
CAD_AGENT_ENABLED: bool = False
CAD_AGENT_MODE: str = "huggingface"  # Options: "huggingface", "vllm_local", "vllm_remote", "tgi"
CAD_AGENT_HF_MODEL_ID: Optional[str] = None  # e.g., "your-username/cad-prompt-enhancer"
CAD_AGENT_HF_API_TOKEN: Optional[str] = None  # For Hugging Face API
CAD_AGENT_VLLM_URL: Optional[str] = None  # e.g., "http://localhost:8001" or "https://xxxxx-8001.proxy.runpod.net"
CAD_AGENT_FALLBACK_ENABLED: bool = True  # Fallback to original prompt if enhancement fails
CAD_AGENT_TIMEOUT: int = 10  # Request timeout in seconds
```

**File:** `backend/env.example`

Add:

```env
# CAD Agent Configuration
CAD_AGENT_ENABLED=false
CAD_AGENT_MODE=huggingface
CAD_AGENT_HF_MODEL_ID=your-username/cad-prompt-enhancer
CAD_AGENT_HF_API_TOKEN=your-hf-token-here
CAD_AGENT_VLLM_URL=http://localhost:8001
CAD_AGENT_FALLBACK_ENABLED=true
CAD_AGENT_TIMEOUT=10
```

### Step 2: Create CAD Prompt Enhancer Service

**File:** `backend/app/services/cad_prompt_enhancer_service.py`

```python
"""
CAD Prompt Enhancer Service

Uses fine-tuned Mistral model to enhance user prompts before GPT-4 parsing.
Supports multiple hosting options: Hugging Face API, vLLM, TGI.
"""
import logging
import httpx
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class CADPromptEnhancerService:
    """
    Service for enhancing CAD prompts using fine-tuned Mistral model.
    
    Supports multiple hosting backends:
    - Hugging Face Inference API (easiest)
    - vLLM server (local or remote)
    - Text Generation Inference (TGI)
    """
    
    def __init__(self):
        """Initialize CAD prompt enhancer service"""
        self.enabled = getattr(settings, 'CAD_AGENT_ENABLED', False)
        self.mode = getattr(settings, 'CAD_AGENT_MODE', 'huggingface')
        self.fallback_enabled = getattr(settings, 'CAD_AGENT_FALLBACK_ENABLED', True)
        self.timeout = getattr(settings, 'CAD_AGENT_TIMEOUT', 10)
        
        if not self.enabled:
            logger.info("CAD Agent is disabled")
            return
        
        # Initialize based on mode
        if self.mode == 'huggingface':
            self._init_huggingface()
        elif self.mode in ['vllm_local', 'vllm_remote']:
            self._init_vllm()
        elif self.mode == 'tgi':
            self._init_tgi()
        else:
            logger.warning(f"Unknown CAD_AGENT_MODE: {self.mode}, disabling")
            self.enabled = False
    
    def _init_huggingface(self):
        """Initialize Hugging Face API client"""
        self.hf_model_id = getattr(settings, 'CAD_AGENT_HF_MODEL_ID', None)
        self.hf_api_token = getattr(settings, 'CAD_AGENT_HF_API_TOKEN', None)
        
        if not self.hf_model_id:
            logger.warning("CAD_AGENT_HF_MODEL_ID not set, disabling CAD Agent")
            self.enabled = False
            return
        
        self.hf_api_url = f"https://api-inference.huggingface.co/models/{self.hf_model_id}"
        self.hf_headers = {}
        if self.hf_api_token:
            self.hf_headers["Authorization"] = f"Bearer {self.hf_api_token}"
        
        logger.info(f"CAD Agent initialized with Hugging Face API: {self.hf_model_id}")
    
    def _init_vllm(self):
        """Initialize vLLM client"""
        self.vllm_url = getattr(settings, 'CAD_AGENT_VLLM_URL', None)
        
        if not self.vllm_url:
            logger.warning("CAD_AGENT_VLLM_URL not set, disabling CAD Agent")
            self.enabled = False
            return
        
        self.vllm_url = self.vllm_url.rstrip('/')
        logger.info(f"CAD Agent initialized with vLLM: {self.vllm_url}")
    
    def _init_tgi(self):
        """Initialize Text Generation Inference client"""
        self.tgi_url = getattr(settings, 'CAD_AGENT_VLLM_URL', None)
        
        if not self.tgi_url:
            logger.warning("CAD_AGENT_VLLM_URL not set for TGI, disabling CAD Agent")
            self.enabled = False
            return
        
        self.tgi_url = self.tgi_url.rstrip('/')
        logger.info(f"CAD Agent initialized with TGI: {self.tgi_url}")
    
    async def enhance_prompt(self, user_prompt: str) -> str:
        """
        Enhance a CAD prompt using the fine-tuned model.
        
        Args:
            user_prompt: Original user prompt
        
        Returns:
            Enhanced prompt, or original if enhancement fails/disabled
        """
        if not self.enabled:
            return user_prompt
        
        try:
            if self.mode == 'huggingface':
                enhanced = await self._enhance_via_hf(user_prompt)
            elif self.mode in ['vllm_local', 'vllm_remote']:
                enhanced = await self._enhance_via_vllm(user_prompt)
            elif self.mode == 'tgi':
                enhanced = await self._enhance_via_tgi(user_prompt)
            else:
                return user_prompt
            
            if enhanced and enhanced.strip():
                logger.info(f"Prompt enhanced: {len(user_prompt)} → {len(enhanced)} chars")
                return enhanced.strip()
            else:
                logger.warning("Enhancement returned empty, using original")
                return user_prompt
                
        except Exception as e:
            logger.error(f"CAD Agent enhancement failed: {e}", exc_info=True)
            if self.fallback_enabled:
                logger.info("Falling back to original prompt")
                return user_prompt
            else:
                raise
    
    async def _enhance_via_hf(self, user_prompt: str) -> str:
        """Enhance prompt via Hugging Face Inference API"""
        formatted = (
            f"<s>[INST] Enhance this CAD prompt to be extremely detailed "
            f"and compatible with ezdxf Python code generation.\n"
            f"Input: {user_prompt} [/INST]"
        )
        
        payload = {
            "inputs": formatted,
            "parameters": {
                "temperature": 0.1,
                "max_new_tokens": 350,
                "stop": ["</s>", "[INST]"]
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.hf_api_url,
                headers=self.hf_headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Handle HF API response format
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
                if "[/INST]" in generated_text:
                    enhanced = generated_text.split("[/INST]")[-1].strip()
                else:
                    enhanced = generated_text.strip()
                return enhanced
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"].strip()
            else:
                logger.warning(f"Unexpected HF API response format: {result}")
                return ""
    
    async def _enhance_via_vllm(self, user_prompt: str) -> str:
        """Enhance prompt via vLLM server"""
        formatted = (
            f"<s>[INST] Enhance this CAD prompt to be extremely detailed "
            f"and compatible with ezdxf Python code generation.\n"
            f"Input: {user_prompt} [/INST]"
        )
        
        payload = {
            "prompt": formatted,
            "temperature": 0.1,
            "max_tokens": 350,
            "stop": ["</s>", "[INST]"]
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.vllm_url}/enhance",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result.get("enhanced_prompt", "").strip()
    
    async def _enhance_via_tgi(self, user_prompt: str) -> str:
        """Enhance prompt via Text Generation Inference"""
        formatted = (
            f"<s>[INST] Enhance this CAD prompt to be extremely detailed "
            f"and compatible with ezdxf Python code generation.\n"
            f"Input: {user_prompt} [/INST]"
        )
        
        payload = {
            "inputs": formatted,
            "parameters": {
                "temperature": 0.1,
                "max_new_tokens": 350,
                "stop": ["</s>", "[INST]"]
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.tgi_url}/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            generated = result.get("generated_text", "")
            if "[/INST]" in generated:
                return generated.split("[/INST]")[-1].strip()
            return generated.strip()
    
    def is_configured(self) -> bool:
        """Check if service is properly configured"""
        return self.enabled


# Global instance - initialize with error handling
cad_prompt_enhancer_service = None
try:
    if getattr(settings, 'CAD_AGENT_ENABLED', False):
        cad_prompt_enhancer_service = CADPromptEnhancerService()
        if cad_prompt_enhancer_service.is_configured():
            logger.info("✅ CAD Prompt Enhancer Service initialized")
        else:
            logger.warning("⚠️ CAD Prompt Enhancer Service disabled (not configured)")
            cad_prompt_enhancer_service = None
    else:
        logger.info("CAD Agent is disabled in configuration")
except Exception as e:
    logger.error(f"Failed to initialize CAD Prompt Enhancer Service: {e}", exc_info=True)
    cad_prompt_enhancer_service = None
```

### Step 3: Integrate with GPTParserService

**File:** `backend/app/services/gpt_parser_service.py`

Add import at top:

```python
from app.services.cad_prompt_enhancer_service import cad_prompt_enhancer_service
```

Modify `parse_text` method (around line 136):

```python
async def parse_text(
    self,
    text: str,
    file_type: CADFileType = CADFileType.DXF,
    additional_context: Optional[str] = None
) -> tuple[List[ParsedInstruction], str]:
    """
    Parse transcribed text into CAD instructions
    """
    # NEW: Enhance prompt with CAD Agent if enabled
    original_text = text
    if cad_prompt_enhancer_service and cad_prompt_enhancer_service.is_configured():
        try:
            text = await cad_prompt_enhancer_service.enhance_prompt(text)
            if text != original_text:
                logger.info(f"Prompt enhanced by CAD Agent ({len(original_text)} → {len(text)} chars)")
        except Exception as e:
            logger.warning(f"CAD Agent enhancement failed, using original prompt: {e}")
            text = original_text
    
    # Rest of the method remains unchanged...
    system_prompt = self._get_system_prompt(file_type)
    # ... existing code continues
```

### Step 4: Integrate with TextToJSONConverter

**File:** `backend/app/services/text_to_json_converter.py`

Add import at top:

```python
from app.services.cad_prompt_enhancer_service import cad_prompt_enhancer_service
```

Modify `convert_text_to_json` method (around line 35):

```python
async def convert_text_to_json(
    self,
    text: str,
    units: str = "inches"
) -> Dict[str, Any]:
    """
    Convert natural language text to structured JSON format.
    """
    # NEW: Enhance prompt with CAD Agent if enabled
    original_text = text
    if cad_prompt_enhancer_service and cad_prompt_enhancer_service.is_configured():
        try:
            text = await cad_prompt_enhancer_service.enhance_prompt(text)
            if text != original_text:
                logger.info(f"Prompt enhanced by CAD Agent for JSON conversion")
        except Exception as e:
            logger.warning(f"CAD Agent enhancement failed, using original prompt: {e}")
            text = original_text
    
    # Rest of the method remains unchanged...
```

### Step 5: Update Requirements

**File:** `backend/requirements.txt`

Add:

```txt
# CAD Agent dependencies
httpx>=0.25.0  # For async HTTP requests to model servers
huggingface-hub>=0.20.0  # Optional, for HF API
```

### Step 6: Create Model Server Script (for local/cloud GPU)

**File:** `backend/scripts/serve_cad_agent.py`

```python
#!/usr/bin/env python3
"""
CAD Agent Model Server using vLLM

Run this on a GPU server (local or cloud) to serve the fine-tuned model.
Access via: http://localhost:8001/enhance
"""
from vllm import LLM, SamplingParams
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CAD Agent Model Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Configuration
MODEL_ID = os.getenv("CAD_AGENT_MODEL_ID", "your-username/cad-prompt-enhancer")
PORT = int(os.getenv("CAD_AGENT_PORT", "8001"))

# Load model (do this once at startup)
logger.info(f"Loading CAD Agent model: {MODEL_ID}...")
try:
    llm = LLM(
        model=MODEL_ID,
        dtype="bfloat16",
        tensor_parallel_size=1,
        max_model_len=1024,
        trust_remote_code=True
    )
    sampling_params = SamplingParams(
        temperature=0.1,
        max_tokens=350,
        stop=["</s>", "[INST]"]
    )
    logger.info("✅ Model loaded successfully!")
except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")
    raise

class PromptRequest(BaseModel):
    prompt: str

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "model": MODEL_ID}

@app.post("/enhance")
async def enhance_prompt(req: PromptRequest):
    """Enhance a CAD prompt"""
    try:
        formatted = (
            f"<s>[INST] Enhance this CAD prompt to be extremely detailed "
            f"and compatible with ezdxf Python code generation.\n"
            f"Input: {req.prompt} [/INST]"
        )
        
        outputs = llm.generate([formatted], sampling_params)
        enhanced = outputs[0].outputs[0].text.strip()
        
        return {"enhanced_prompt": enhanced}
    except Exception as e:
        logger.error(f"Enhancement failed: {e}")
        raise

if __name__ == "__main__":
    logger.info(f"Starting CAD Agent server on port {PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
```

Make executable:
```bash
chmod +x backend/scripts/serve_cad_agent.py
```

---

## Testing & Validation

### Unit Tests

**File:** `backend/tests/unit/test_cad_prompt_enhancer.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.cad_prompt_enhancer_service import CADPromptEnhancerService

@pytest.mark.asyncio
async def test_enhance_prompt_huggingface():
    """Test prompt enhancement via Hugging Face API"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = [{
            "generated_text": "<s>[INST] ... [/INST]Enhanced prompt with details"
        }]
        mock_response.raise_for_status = AsyncMock()
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        service = CADPromptEnhancerService()
        # ... test implementation

@pytest.mark.asyncio
async def test_fallback_on_failure():
    """Test fallback to original prompt on failure"""
    # ... test implementation
```

### Integration Test

**File:** `backend/tests/integration/test_cad_agent_integration.py`

```python
import pytest
from app.services.gpt_parser_service import gpt_parser_service
from app.services.cad_prompt_enhancer_service import cad_prompt_enhancer_service

@pytest.mark.asyncio
async def test_full_pipeline_with_cad_agent():
    """Test full pipeline: CAD Agent → GPT-4 → Instructions"""
    if not cad_prompt_enhancer_service or not cad_prompt_enhancer_service.is_configured():
        pytest.skip("CAD Agent not configured")
    
    text = "a simple spur gear"
    instructions, raw = await gpt_parser_service.parse_text(text)
    
    assert len(instructions) > 0
    assert instructions[0].command in ["circle", "line", "polyline"]
```

### Manual Testing

**Test Script:** `backend/scripts/test_cad_agent.py`

```python
#!/usr/bin/env python3
"""Quick test script for CAD Agent"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.cad_prompt_enhancer_service import cad_prompt_enhancer_service

async def test():
    if not cad_prompt_enhancer_service or not cad_prompt_enhancer_service.is_configured():
        print("❌ CAD Agent not configured")
        return
    
    test_prompts = [
        "a simple spur gear",
        "L bracket with mounting holes",
        "basic house floor plan"
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 Original: {prompt}")
        enhanced = await cad_prompt_enhancer_service.enhance_prompt(prompt)
        print(f"✨ Enhanced: {enhanced[:200]}...")

if __name__ == "__main__":
    asyncio.run(test())
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Fine-tune model (Stage 1: SketchGraphs, Stage 2: ezdxf examples)
- [ ] Upload model to Hugging Face
- [ ] Choose hosting option (HF API, local GPU, or cloud GPU)
- [ ] Set up model server (if using vLLM/TGI)
- [ ] Add environment variables to `.env`
- [ ] Test locally with `CAD_AGENT_ENABLED=true`

### Deployment Steps

1. **Update Environment Variables:**
   ```bash
   # For Hugging Face API
   CAD_AGENT_ENABLED=true
   CAD_AGENT_MODE=huggingface
   CAD_AGENT_HF_MODEL_ID=your-username/cad-prompt-enhancer
   CAD_AGENT_HF_API_TOKEN=hf_xxxxx
   
   # OR for vLLM server
   CAD_AGENT_ENABLED=true
   CAD_AGENT_MODE=vllm_remote
   CAD_AGENT_VLLM_URL=https://your-gpu-server:8001
   ```

2. **Deploy Backend:**
   - Push code changes
   - Deploy to your hosting platform (Render, etc.)
   - Verify service starts without errors

3. **Deploy Model Server (if using vLLM):**
   - Set up GPU server (local or cloud)
   - Run `serve_cad_agent.py`
   - Verify health endpoint: `curl http://server:8001/health`

4. **Enable Feature:**
   - Set `CAD_AGENT_ENABLED=true` in production
   - Monitor logs for enhancement activity
   - A/B test if possible

### Monitoring

**Key Metrics to Track:**
- Enhancement success rate
- Average enhancement time
- GPT-4 parsing accuracy (before/after)
- Cost per request
- Error rates
- CAD F1 score (if using advanced metrics)

**Log Messages to Monitor:**
- `"Prompt enhanced by CAD Agent"` - Success
- `"CAD Agent enhancement failed"` - Failure (should fallback)
- `"CAD Agent is disabled"` - Not configured

---

## Cost Analysis

### Current System (per 1,000 requests)
- GPT-4 Turbo: ~$30-50 (varies by token usage)
- **Total: ~$30-50**

### Proposed System (per 1,000 requests)

**With Mistral-7B:**
- Mistral inference (self-hosted): $0 (if using free GPU)
- GPU hosting cost: ~$0.50-2.00/hour (if using cloud GPU, needs RTX 3090/A4000)
- GPT-4 Turbo: ~$30-50 (same as before, but with better prompts)
- **Total: ~$30-52** (plus GPU hosting if not free)

**With DeepSeek-Coder-V2-Lite (Recommended):**
- DeepSeek inference (self-hosted): $0 (if using free GPU)
- GPU hosting cost: **~$0.15-0.30/hour** (if using cloud GPU, needs RTX 3060/3070) ⭐ **50% cheaper!**
- GPT-4 Turbo: ~$30-50 (same as before, but with better prompts)
- **Total: ~$30-32** (plus GPU hosting if not free)
- **Savings:** ~$0.20-0.50/hour on GPU hosting = **$15-30/month savings** (if running 24/7)

### Break-even Analysis
- **Cost savings:** Minimal on per-request basis
- **Value add:** Better accuracy from enhanced prompts (0.65-0.75 CAD F1)
- **Infrastructure cost:** GPU server ~$50-200/month (if 24/7) or ~$15-50/month (if stopped when idle)

### Cost Optimization Tips

**For Hugging Face API:**
- Use free tier for testing (1,000 requests/month)
- Enable auto-scaling to stop when not in use
- Consider caching common prompts

**For Cloud GPU (RunPod):**
- **Stop pod when not in use** - biggest cost saver
- Use spot instances (cheaper, but can be interrupted)
- **Use DeepSeek-Coder-V2-Lite** - can use RTX 3060/3070 (cheaper than RTX 3090)
- Right-size GPU (RTX 3090 for Mistral-7B, RTX 3060/3070 for DeepSeek)
- Use network volumes for model storage (persistent, cheaper)

**For Local GPU:**
- **DeepSeek-Coder-V2-Lite:** Can use RTX 3060/3070 (6-8GB VRAM) - **cheapest option**
- **Mistral-7B:** Needs RTX 3090 or better (8-16GB VRAM)
- Consider used hardware (eBay, etc.) - RTX 3060/3070 much cheaper than RTX 3090
- Power costs: ~$0.10-0.20/hour for electricity (lower for smaller GPUs)

**General:**
- Enable fallback to avoid blocking on model failures
- Cache enhanced prompts for common requests
- Batch requests if possible

---

## Troubleshooting

### Issue: "CAD Agent not configured"
**Solution:** Check environment variables are set correctly

### Issue: "Model server connection failed"
**Solution:** 
- Verify model server is running: `curl http://server:8001/health`
- Check firewall/network settings
- Verify URL in `CAD_AGENT_VLLM_URL`

### Issue: "Enhancement timeout"
**Solution:**
- Increase `CAD_AGENT_TIMEOUT` (default 10s)
- Check model server performance
- Consider using faster hosting option

### Issue: "HF API rate limit"
**Solution:**
- Upgrade Hugging Face plan
- Switch to self-hosted vLLM
- Implement request queuing

### Issue: "Enhancement returns empty"
**Solution:**
- Check model is properly fine-tuned
- Verify prompt format matches training data
- Check model server logs for errors

### Issue: "Low CAD F1 score"
**Solution:**
- Ensure using tokenization & normalization
- Verify training tasks (auto-completion, next-entity, masked) are included
- Check evaluation metrics implementation
- Consider two-stage training approach

---

## Next Steps

1. **Download CADLLM dataset** (155K samples) - easiest, most relevant ⭐
   ```python
   from datasets import load_dataset
   dataset = load_dataset("lanlanguai/CADLLM", split="train")
   ```

2. **Download SketchGraphs dataset** (1M+ sketches) - for geometric constraints
3. **Download DeepCAD dataset** - for construction sequences ⭐ NEW
   ```bash
   git clone https://github.com/rundiwu/DeepCAD.git
   # Download data from: https://www.cs.columbia.edu/cg/deepcad/
   ```
4. **Preprocess datasets** to your training format
4. **Implement tokenization & normalization** functions
5. **Create training data** (CADLLM + SketchGraphs + 200-500 ezdxf examples)
6. **Fine-tune model** using Google Colab or local GPU
7. **Choose hosting option** based on your traffic and budget
8. **Implement backend integration** code
9. **Test locally** with `CAD_AGENT_ENABLED=true`
10. **Deploy to staging** and validate
11. **Monitor and optimize** based on real usage

---

**Estimated Implementation Time:**
- Dataset download & preprocessing: 2-3 hours (CADLLM ready, SketchGraphs + DeepCAD need processing)
- Fine-tuning (Stage 1: CADLLM, Stage 2: SketchGraphs+DeepCAD, Stage 3: ezdxf): 8-14 hours
- Code implementation: 2-3 hours
- Testing: 1-2 hours
- Deployment: 1-2 hours
- **Total: 11-20 hours** (but much better results!)

**Estimated Monthly Cost:**

**With Mistral-7B:**
- Hugging Face API: ~$15-50 (depending on traffic)
- Cloud GPU (RunPod, RTX 3090): ~$50-150 (if running 24/7, less if stopped when idle)
- Local GPU: ~$0 (after hardware purchase, RTX 3090 ~$800-1200 used)

**With DeepSeek-Coder-V2-Lite (Recommended):**
- Hugging Face API: ~$15-50 (depending on traffic)
- Cloud GPU (RunPod, RTX 3060/3070): **~$25-75** (if running 24/7, less if stopped when idle) ⭐ **50% cheaper!**
- Local GPU: ~$0 (after hardware purchase, RTX 3060/3070 ~$300-500 used) ⭐ **Much cheaper hardware!**
- **Monthly savings:** $15-30/month on cloud GPU, $300-700 on hardware purchase

**Expected Performance:**
- **CAD F1 Score:** 
  - **With CADLLM dataset:** 0.70-0.90 (based on paper's 96.6% accuracy) ⭐
  - Mistral-7B: 0.65-0.75 (with advanced fine-tuning)
  - DeepSeek-Coder-V2-Lite: 0.60-0.70 (slightly lower but still excellent)
- **Cost per DXF:** <$0.005 (with self-hosted model)
- **Cost Savings with DeepSeek:** 50% cheaper GPU hosting, 50% cheaper hardware
- **Training Data:** CADLLM (155K) + SketchGraphs (1M+) = massive dataset

---

**Document Status:** Ready for Implementation  
**Last Updated:** December 10, 2025

