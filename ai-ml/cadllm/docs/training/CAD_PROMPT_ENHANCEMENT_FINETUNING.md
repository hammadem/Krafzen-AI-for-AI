# CAD Prompt-Enhancement Fine-Tuning: Technical Documentation

## Table of Contents

1. [Project Goal and Scope](#project-goal-and-scope)
2. [Base Model and Selection Rationale](#base-model-and-selection-rationale)
3. [Adapter Approach: LoRA](#adapter-approach-lora)
4. [Dataset Format and Constraints](#dataset-format-and-constraints)
5. [Training Code Walkthrough](#training-code-walkthrough)
6. [Inner Workings of Training](#inner-workings-of-training)
7. [Libraries and Their Roles](#libraries-and-their-roles)
8. [Hardware and Precision](#hardware-and-precision)
9. [Concrete Examples](#concrete-examples)
10. [Operational Guidance](#operational-guidance)

---

## Project Goal and Scope

### Goal

The project fine-tunes an instruction-following language model to convert short, natural language CAD requests into a strict, DXF-ready Domain-Specific Language (DSL) output. The model must produce structured output with:

- **Explicit units** (millimeters)
- **Room boundaries** (width, height, center coordinates)
- **Geometric entities** (rectangles and circles with precise dimensions)
- **Spatial coordinates** (center points for all objects)
- **Metadata** (layers, anchor walls, subfeature relationships)

### Pipeline Architecture

```
User Prompt (Natural Language)
    ↓
Fine-Tuned Model (Qwen2.5-Coder-3B-Instruct + LoRA)
    ↓
Structured DSL Output
    ↓
Downstream Parser
    ↓
DXF Geometry File
```

**Example Flow:**

1. **Input**: "Draw a kitchen with sink, stove, and refrigerator."
2. **Model Output** (DSL):
   ```
   UNITS: mm
   ORIGIN_POLICY: room_center_at_(0,0)
   ROOM: rect w=4000 h=3000 center=(0,0)
   WALLS: rect_perimeter closed=true layer=WALLS
   SINK: rect w=600 h=500 center=(0,1400) layer=OBJECTS closed=true anchor_wall=north
   STOVE: rect w=800 h=800 center=(-1600,0) layer=OBJECTS closed=true anchor_wall=west
   REFRIGERATOR: rect w=700 h=1800 center=(1600,0) layer=OBJECTS closed=true anchor_wall=east
   ```
3. **Parser**: Converts DSL lines into DXF entities (rectangles, circles, polylines)
4. **DXF File**: Ready for CAD software import

### Why Fine-Tuning Instead of Training from Scratch

- **Cost**: Training a 3B parameter model from scratch requires months of GPU time and millions of dollars. Fine-tuning takes hours and costs hundreds of dollars.
- **Data Efficiency**: Pre-trained models have learned general language patterns, code structure, and reasoning. We only need to teach the specific DSL format.
- **Quality**: Base models (especially code-specialized ones) already understand structured output, coordinate systems, and geometric concepts. Fine-tuning adapts this knowledge to our domain.
- **Maintenance**: We can update the model by fine-tuning on new data without retraining the entire architecture.

---

## Base Model and Selection Rationale

### Qwen2.5-Coder-3B-Instruct

**Model Type**: Decoder-only transformer architecture (similar to GPT, LLaMA)

**Architecture Details**:
- **Parameters**: 3 billion
- **Architecture**: Transformer decoder with:
  - Multi-head self-attention layers
  - Feed-forward networks (MLP) with SwiGLU activation
  - Rotary Position Embeddings (RoPE)
  - Grouped Query Attention (GQA) for efficiency
- **Context Length**: 32,768 tokens
- **Vocabulary**: ~152,000 tokens (includes code-specific tokens)

**What "Instruct" Means**:

The "Instruct" variant has been trained using instruction-following techniques (RLHF, supervised fine-tuning) to:
- Follow user instructions precisely
- Generate structured outputs
- Use chat templates (system/user/assistant message format)
- Produce deterministic, format-consistent responses

This makes it ideal for our task: we need the model to follow a strict DSL format rather than generate free-form text.

**Why Qwen2.5-Coder-3B-Instruct is Suitable**:

1. **Code Specialization**: Pre-trained on code, so it understands structured syntax, coordinate systems, and geometric primitives.
2. **Size Efficiency**: 3B parameters fit on a single GPU (H200/H100) with LoRA, enabling fast iteration.
3. **Instruction Following**: The "Instruct" variant excels at format-constrained generation.
4. **Multilingual**: Handles diverse natural language inputs while producing consistent DSL output.
5. **Proven Performance**: Strong results on code generation benchmarks, indicating good structured output capabilities.

**Alternative Models Considered**:

- **DeepSeek-Coder-V2-Lite**: Smaller (1.3B), but less capable for complex layouts
- **Mistral-7B-Instruct**: Larger (7B), requires more VRAM, slower training
- **CodeLlama-7B**: Good but larger than needed for this structured task

---

## Adapter Approach: LoRA

### What is LoRA?

**LoRA (Low-Rank Adaptation)** is a parameter-efficient fine-tuning technique that adds trainable low-rank matrices to specific transformer layers instead of updating all model weights.

**Key Concept**: Instead of modifying the full weight matrix `W` (which has `d × d` parameters), LoRA decomposes the update as:

```
W' = W + ΔW
ΔW = BA
```

Where:
- `B` is a `d × r` matrix (rank `r`)
- `A` is an `r × d` matrix
- `r << d` (typically `r = 8, 16, or 32`)

This reduces trainable parameters from `d²` to `2rd`. For `d = 4096` and `r = 16`, that's `131,072` parameters instead of `16,777,216` (99.2% reduction).

### Why Use LoRA?

1. **Memory Efficiency**: Only the LoRA matrices are stored in optimizer states (AdamW momentum/variance), reducing memory by ~90%.
2. **Speed**: Fewer gradients to compute and update, faster training iterations.
3. **Modularity**: LoRA adapters can be swapped without reloading the base model.
4. **Stability**: Lower learning rates on adapter weights reduce risk of catastrophic forgetting.

### LoRA Configuration in Our Project

```python
lora_config = LoraConfig(
    r=16,                    # Rank: controls adapter capacity (higher = more parameters)
    lora_alpha=32,           # Scaling factor: α/r scales LoRA outputs (typically 2×r)
    lora_dropout=0.05,       # Dropout for LoRA layers (regularization)
    bias="none",             # Don't train bias terms (further parameter reduction)
    task_type="CAUSAL_LM",   # Causal language modeling objective
    target_modules=[          # Which transformer layers receive LoRA
        "q_proj",              # Query projection (attention)
        "k_proj",              # Key projection (attention)
        "v_proj",              # Value projection (attention)
        "o_proj",              # Output projection (attention)
        "gate_proj",           # Gate projection (MLP)
        "up_proj",             # Up projection (MLP)
        "down_proj",           # Down projection (MLP)
    ],
)
```

**Target Modules Explained**:

- **Attention Projections** (`q_proj`, `k_proj`, `v_proj`, `o_proj`): Control what the model attends to. LoRA here adapts the model's focus to CAD-specific patterns (e.g., recognizing "kitchen" → generate room dimensions).
- **MLP Projections** (`gate_proj`, `up_proj`, `down_proj`): Control feature transformations. LoRA here adapts how the model processes geometric information.

**Why Not Embeddings or Layer Norms?**:
- Embeddings: Large vocabularies make embedding LoRA less efficient; we resize embeddings if needed.
- Layer Norms: Small parameters, minimal impact; training them can destabilize training.

### Artifacts Produced

After training, we save:

1. **LoRA Adapter Weights**: Small files (`adapter_model.safetensors`, `adapter_config.json`) containing only the `A` and `B` matrices for each target module.
2. **Tokenizer**: Copy of the tokenizer (needed for inference).
3. **Embedding Resize Info** (if applicable): If vocabulary was extended.

**Total Size**: ~50-100 MB (vs. ~6 GB for full model weights)

### Loading for Inference

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-Coder-3B-Instruct",
    torch_dtype=torch.bfloat16
)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct")

# Load LoRA adapter on top
model = PeftModel.from_pretrained(base_model, "./cadllm/adapter")
model = model.merge_and_unload()  # Optional: merge for faster inference
```

---

## Dataset Format and Constraints

### JSONL Structure

Each line in the dataset is a JSON object:

```json
{
    "instruction": "Draw a kitchen with sink, stove, and refrigerator.",
    "input": "(none)",
    "output": "UNITS: mm\nORIGIN_POLICY: room_center_at_(0,0)\nROOM: rect w=4000 h=3000 center=(0,0)\nWALLS: rect_perimeter closed=true layer=WALLS\nSINK: rect w=600 h=500 center=(0,1400) layer=OBJECTS closed=true anchor_wall=north\nSTOVE: rect w=800 h=800 center=(-1600,0) layer=OBJECTS closed=true anchor_wall=west\nREFRIGERATOR: rect w=700 h=1800 center=(1600,0) layer=OBJECTS closed=true anchor_wall=east"
}
```

**Fields**:
- `instruction`: Natural language user request
- `input`: Additional context (usually "(none)" for our use case)
- `output`: Strict DSL format (newline-separated)

### DSL Schema and Constraints

#### Required Header Lines (Must Appear in Order)

1. **UNITS**: `UNITS: mm` (always millimeters)
2. **ORIGIN_POLICY**: `ORIGIN_POLICY: room_center_at_(0,0)` (room center is origin)
3. **ROOM**: `ROOM: rect w=WIDTH h=HEIGHT center=(0,0)` (room dimensions)
4. **WALLS**: `WALLS: rect_perimeter closed=true layer=WALLS` (wall perimeter)

#### Entity Lines

**Rectangle Format**:
```
ENTITY_NAME: rect w=WIDTH h=HEIGHT center=(X,Y) layer=LAYER closed=true anchor_wall=WALL [subfeature_of=PARENT]
```

**Circle Format**:
```
ENTITY_NAME: circle r=RADIUS center=(X,Y) layer=LAYER closed=true anchor_wall=WALL [subfeature_of=PARENT]
```

**Parameters**:
- `w`, `h`: Width and height in mm (rectangles only)
- `r`: Radius in mm (circles only)
- `center=(x,y)`: Center coordinates in mm (room-centered coordinate system)
- `layer`: Layer name (`WALLS`, `OBJECTS`, `CABINETS`, etc.)
- `closed=true`: Shape is closed (always true in our DSL)
- `anchor_wall`: One of `north`, `south`, `east`, `west`, `none`
- `subfeature_of`: Optional parent entity (e.g., `BURNER_1 subfeature_of=COOKTOP`)

#### Coordinate System

- **Origin**: Room center at `(0, 0)`
- **Axes**: 
  - X: Positive = east, Negative = west
  - Y: Positive = north, Negative = south
- **Room Bounds**: For room `w=4000 h=3000`, bounds are:
  - X: `[-2000, 2000]`
  - Y: `[-1500, 1500]`

#### Entity Naming Conventions

- Use **UPPERCASE** with **UNDERSCORES**: `COFFEE_TABLE`, `BED_QUEEN`, `SINK_DOUBLE`
- No spaces: `COFFEE TABLE` ❌, `COFFEE_TABLE` ✅
- Descriptive: `CABINET_LEFT`, `CABINET_RIGHT` (not `CABINET_1`, `CABINET_2`)

### Dataset Quality Constraints

#### 1. Out-of-Bounds (OOB) Validation

All objects must be fully contained within room boundaries:

```python
def is_out_of_bounds(entity, room_w, room_h):
    """Check if entity extends beyond room bounds."""
    x, y = entity.center
    if entity.shape == "rect":
        half_w, half_h = entity.w / 2, entity.h / 2
        bounds_x = [-room_w/2, room_w/2]
        bounds_y = [-room_h/2, room_h/2]
        return (x - half_w < bounds_x[0] or x + half_w > bounds_x[1] or
                y - half_h < bounds_y[0] or y + half_h > bounds_y[1])
    elif entity.shape == "circle":
        r = entity.r
        bounds_x = [-room_w/2, room_w/2]
        bounds_y = [-room_h/2, room_h/2]
        return (x - r < bounds_x[0] or x + r > bounds_x[1] or
                y - r < bounds_y[0] or y + r > bounds_y[1])
```

**Validation**: Dataset generation scripts filter out any records with OOB entities.

#### 2. Overlap Validation

Objects must not overlap **except** for subfeatures:

```python
def rectangles_overlap(rect1, rect2):
    """Check if two rectangles overlap."""
    x1, y1, w1, h1 = rect1.center[0], rect1.center[1], rect1.w, rect1.h
    x2, y2, w2, h2 = rect2.center[0], rect2.center[1], rect2.w, rect2.h
    
    return not (x1 + w1/2 < x2 - w2/2 or x1 - w1/2 > x2 + w2/2 or
                y1 + h1/2 < y2 - h2/2 or y1 - h1/2 > y2 + h2/2)

def validate_no_overlaps(entities):
    """Check all entities for overlaps, excluding subfeatures."""
    main_entities = [e for e in entities if not e.get("subfeature_of")]
    
    for i, e1 in enumerate(main_entities):
        for e2 in main_entities[i+1:]:
            if rectangles_overlap(e1, e2):
                return False  # Overlap detected
    return True
```

**Subfeature Exception**: Burners can overlap with cooktops because they're subfeatures:

```
COOKTOP: rect w=800 h=800 center=(-1600,0) layer=OBJECTS closed=true anchor_wall=west
BURNER_1: circle r=150 center=(-1400,200) layer=OBJECTS closed=true anchor_wall=west subfeature_of=COOKTOP
BURNER_2: circle r=150 center=(-1400,-200) layer=OBJECTS closed=true anchor_wall=west subfeature_of=COOKTOP
BURNER_3: circle r=150 center=(-1800,200) layer=OBJECTS closed=true anchor_wall=west subfeature_of=COOKTOP
BURNER_4: circle r=150 center=(-1800,-200) layer=OBJECTS closed=true anchor_wall=west subfeature_of=COOKTOP
```

Here, all four burners overlap the cooktop rectangle, which is allowed.

#### 3. Dataset Statistics

Our final validated dataset (`cadllm_final.jsonl`) contains:
- **200,191 records**
- **Room Types**: Kitchen, bathroom, bedroom, living room
- **Validation**: All records pass OOB and overlap checks (excluding subfeatures)

---

## Training Code Walkthrough

### Architecture Overview

The training script (`train_qwen.py`) follows this flow:

```
1. Parse command-line arguments
2. Load and shuffle dataset
3. Split into train/eval (first 2k for eval, rest for train)
4. Format examples into chat messages
5. Load base model + apply LoRA
6. Create data collator (handles prompt masking)
7. Configure training arguments
8. Initialize Trainer
9. Train
10. Save adapter weights
```

### Step-by-Step Breakdown

#### 1. Dataset Loading and Shuffling

```python
raw_dset = load_dataset("json", data_files=args.data_path)
full_train = raw_dset["train"]

# Shuffle before splitting to ensure representative eval set
full_train = full_train.shuffle(seed=args.seed)

# First 2k for eval, rest for train
eval_size = min(2000, len(full_train))
eval_raw = full_train.select(range(eval_size))
train_raw = full_train.select(range(eval_size, len(full_train)))
```

**Why Shuffle First?** Ensures the eval set is representative of the full distribution (not just the first 2k examples, which might be sorted by room type).

#### 2. Conversion to Chat Format

```python
def format_example(example: Dict[str, Any]) -> Dict[str, Any]:
    """Format example as Qwen chat messages."""
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
```

**Chat Template Structure**:
- **System**: Contains DSL format specification and rules
- **User**: Natural language instruction (and optional input)
- **Assistant**: Expected DSL output

#### 3. Qwen Chat Templating

The tokenizer's `apply_chat_template` converts messages into the format Qwen expects:

```python
full = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=False,
    return_tensors=None
)
```

This produces a token sequence like:
```
<|im_start|>system
You are a CAD code assistant...
<|im_end|>
<|im_start|>user
Draw a kitchen with sink, stove, and refrigerator.
<|im_end|>
<|im_start|>assistant
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
...
<|im_end|>
```

#### 4. Label Construction and Prompt Masking

**Key Concept**: We only want to compute loss on the assistant's response, not on the prompt (system + user messages).

```python
class CADDataCollator:
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
            
            # Prefix up to assistant (system + user)
            prefix = self.tokenizer.apply_chat_template(
                messages[:-1],  # Exclude assistant message
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
```

**Label Masking Explained**:

- `-100` is a special value in PyTorch's `CrossEntropyLoss` that means "ignore this token in loss calculation"
- **Prompt masking**: `labels[:prefix_len] = [-100] * prefix_len` ensures we don't compute loss on system/user tokens
- **Padding masking**: `labels[attention_mask == 0] = -100` ensures we don't compute loss on padding tokens

**Visual Example**:

```
Input IDs:  [151644, 8948, 198, 2610, 525, 29958, 151645, 198, 2610, ...]
Labels:     [-100,  -100, -100, -100, -100, -100,  -100,  -100, -100, ...]
            ↑ System/User tokens (masked)          ↑ Assistant tokens (unmasked)
```

#### 5. Training vs. Eval Loss

**Training Loss**: Average cross-entropy over all non-masked tokens in the training set.

**Eval Loss**: Average cross-entropy over all non-masked tokens in the eval set.

**Why They Can Be Close for Structured DSL**:

1. **Deterministic Format**: The DSL has strict syntax, so once the model learns the format, errors are rare.
2. **Limited Vocabulary**: DSL uses a small subset of tokens (keywords like `UNITS`, `ROOM`, `rect`, `center=`, etc.), making it easier to learn.
3. **Pattern Recognition**: The model quickly learns patterns like "kitchen" → "ROOM: rect w=4000 h=3000", reducing variance.

**Typical Values**:
- Training loss: 0.05 - 0.15 (after 1 epoch)
- Eval loss: 0.06 - 0.18 (slightly higher due to unseen examples)

If eval loss is much higher (>2× training loss), the model is overfitting. Solutions: reduce learning rate, add dropout, or increase dataset size.

---

## Inner Workings of Training

### Tokenization → Input IDs → Next-Token Prediction

#### 1. Tokenization

The tokenizer converts text into subword tokens:

```
"UNITS: mm" → [151644, 8948, 198, 2610, 525, 29958]
              ["UN", "ITS", ":", " mm", ...]
```

**Why Subword Tokenization?** Handles out-of-vocabulary words by breaking them into known subwords. For example, "COOKTOP" might tokenize as `["COOK", "TOP"]` if it's not in the vocabulary.

#### 2. Input IDs

Each token is mapped to an integer ID from the vocabulary:

```python
tokenizer.encode("UNITS: mm")
# Returns: [151644, 8948, 198, 2610, 525, 29958]
```

These IDs are what the model actually processes.

#### 3. Next-Token Prediction Objective

The model is trained to predict the next token given all previous tokens:

**Forward Pass**:
```
Input:  [151644, 8948, 198, ...]  (tokens 0 to t-1)
Output: [P(token_t | tokens_0..t-1) for each token in vocabulary]
```

**Example**:
- Given: `"UNITS: "`
- Predict: `"mm"` (token ID 29958) with high probability

The model outputs a probability distribution over all ~152,000 tokens in the vocabulary.

### Causal Language Modeling Loss: Cross-Entropy

#### Softmax Logits

The model's final layer outputs **logits** (raw scores) for each token:

```python
logits = model(input_ids)  # Shape: [batch_size, seq_len, vocab_size]
# Example: [4, 512, 152064]
```

These logits are converted to probabilities using the **softmax function**:

\[
P(y_i | x) = \frac{e^{z_i}}{\sum_{j=1}^{V} e^{z_j}}
\]

Where:
- \(z_i\) = logit for token \(i\)
- \(V\) = vocabulary size (~152,000)
- \(P(y_i | x)\) = probability of token \(i\) given context \(x\)

**Numerical Stability**: In practice, we use `log_softmax` to avoid numerical overflow:

\[
\log P(y_i | x) = z_i - \log\left(\sum_{j=1}^{V} e^{z_j}\right)
\]

#### Cross-Entropy Loss

For each position in the sequence, we compute the cross-entropy between the predicted distribution and the true token:

\[
L = -\frac{1}{N} \sum_{i=1}^{N} \log P(y_i^* | x_i)
\]

Where:
- \(N\) = number of non-masked tokens
- \(y_i^*\) = true token at position \(i\)
- \(x_i\) = context (all tokens before position \(i\))

**In Code**:
```python
loss = F.cross_entropy(
    logits.view(-1, vocab_size),  # Flatten: [batch*seq, vocab]
    labels.view(-1),               # Flatten: [batch*seq]
    ignore_index=-100              # Ignore masked tokens
)
```

**Why Negative Log-Likelihood?** It penalizes low probabilities for the correct token. If the model assigns probability 0.9 to the correct token, loss is `-log(0.9) ≈ 0.105`. If it assigns 0.1, loss is `-log(0.1) ≈ 2.3` (much worse).

### Gradient Descent and AdamW

#### What Are Gradients?

The **gradient** of the loss with respect to a parameter is the partial derivative:

\[
\nabla_\theta L = \frac{\partial L}{\partial \theta}
\]

It tells us the direction and magnitude of steepest increase in loss. To minimize loss, we move in the opposite direction:

\[
\theta_{t+1} = \theta_t - \eta \nabla_\theta L
\]

Where \(\eta\) is the learning rate.

#### Gradient Norm

The **gradient norm** is the L2 norm of all gradients:

\[
||\nabla_\theta L||_2 = \sqrt{\sum_{i} \left(\frac{\partial L}{\partial \theta_i}\right)^2}
\]

**Interpretation**:
- **Large gradient norm** (>10.0): Model is learning rapidly, but may be unstable. Consider gradient clipping.
- **Small gradient norm** (<0.1): Model is learning slowly. May need higher learning rate or more training.
- **Normal range**: 0.5 - 5.0 (typical for transformer fine-tuning)

**Gradient Clipping**: We clip gradients to prevent explosive updates:

```python
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

This ensures `||\nabla_\theta L||_2 \leq 1.0`.

#### AdamW Optimizer

**AdamW** (Adam with Weight Decay) is an adaptive learning rate optimizer:

\[
m_t = \beta_1 m_{t-1} + (1 - \beta_1) \nabla_\theta L \quad \text{(momentum)}
\]
\[
v_t = \beta_2 v_{t-1} + (1 - \beta_2) (\nabla_\theta L)^2 \quad \text{(variance)}
\]
\[
\hat{m}_t = \frac{m_t}{1 - \beta_1^t}, \quad \hat{v}_t = \frac{v_t}{1 - \beta_2^t} \quad \text{(bias correction)}
\]
\[
\theta_{t+1} = \theta_t - \eta \left(\frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon} + \lambda \theta_t\right)
\]

Where:
- \(\beta_1 = 0.9\) (momentum decay)
- \(\beta_2 = 0.999\) (variance decay)
- \(\epsilon = 10^{-8}\) (numerical stability)
- \(\lambda\) = weight decay coefficient (typically 0.01)

**Why AdamW?**:
- **Adaptive**: Automatically adjusts learning rate per parameter (small gradients → larger updates, large gradients → smaller updates)
- **Momentum**: Smooths gradient updates, reducing noise
- **Weight Decay**: Regularizes parameters, preventing overfitting

**Fused AdamW**: On NVIDIA GPUs, `adamw_torch_fused` uses optimized CUDA kernels for faster computation (2-3× speedup).

### Learning Rate Schedule: Warmup + Cosine Decay

#### Warmup Phase

During the first few steps, gradients can be very large (model is far from optimal). **Warmup** gradually increases the learning rate:

\[
\eta_t = \eta_{\text{max}} \times \frac{t}{T_{\text{warmup}}}
\]

Where:
- \(t\) = current step
- \(T_{\text{warmup}}\) = total warmup steps
- \(\eta_{\text{max}}\) = maximum learning rate

**Example**: With `warmup_ratio=0.03` and `num_train_epochs=1`, if we have 10,000 steps:
- Warmup steps: \(0.03 \times 10,000 = 300\)
- At step 150: \(\eta = 2 \times 10^{-4} \times \frac{150}{300} = 1 \times 10^{-4}\)

**Why Warmup?** Prevents the model from taking large, destabilizing steps early in training.

#### Cosine Decay

After warmup, the learning rate decays following a cosine curve:

\[
\eta_t = \eta_{\text{min}} + (\eta_{\text{max}} - \eta_{\text{min}}) \times \frac{1 + \cos(\pi \times \frac{t - T_{\text{warmup}}}{T_{\text{total}} - T_{\text{warmup}}})}{2}
\]

Where:
- \(\eta_{\text{min}}\) = minimum learning rate (typically 10% of max, or 0)
- \(T_{\text{total}}\) = total training steps

**Visualization**:
```
LR
│
│     ╱─────╲
│    ╱       ╲
│   ╱         ╲
│  ╱           ╲
│ ╱             ╲────
└────────────────────── Steps
  ↑      ↑
Warmup  Cosine Decay
```

**Why Cosine?** Provides smooth decay that allows the model to fine-tune in later epochs without sudden drops.

### Gradient Checkpointing

**What It Does**: Instead of storing all intermediate activations during the forward pass, gradient checkpointing recomputes them during the backward pass.

**Memory Savings**: Reduces activation memory by ~50-70% at the cost of ~30% slower training (due to recomputation).

**How It Works**:

**Without Checkpointing**:
```
Forward:  Store all activations → High memory
Backward: Use stored activations → Fast
```

**With Checkpointing**:
```
Forward:  Store only checkpoints (every N layers) → Low memory
Backward: Recompute activations between checkpoints → Slower but memory-efficient
```

**When to Use**: Essential for training large models on limited VRAM. Our 3B model with LoRA can fit without it, but it's enabled as a safety measure:

```python
model.gradient_checkpointing_enable()
```

---

## Libraries and Their Roles

### `transformers` (Hugging Face)

**Purpose**: Provides pre-trained models, tokenizers, and training infrastructure.

**Key Components**:

1. **`AutoModelForCausalLM`**: Loads the base model architecture (Qwen2.5-Coder-3B-Instruct)
   ```python
   model = AutoModelForCausalLM.from_pretrained(
       "Qwen/Qwen2.5-Coder-3B-Instruct",
       dtype=torch.bfloat16
   )
   ```

2. **`AutoTokenizer`**: Handles tokenization and chat templating
   ```python
   tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct")
   tokenizer.apply_chat_template(messages, tokenize=True)
   ```

3. **`Trainer`**: High-level training loop that handles:
   - Batching and data loading
   - Forward/backward passes
   - Optimizer steps
   - Logging and checkpointing
   - Evaluation

4. **`TrainingArguments`**: Configuration for training hyperparameters
   ```python
   training_args = TrainingArguments(
       output_dir="./cadllm",
       learning_rate=2e-4,
       num_train_epochs=1,
       per_device_train_batch_size=4,
       # ... more args
   )
   ```

### `datasets` (Hugging Face)

**Purpose**: Efficient dataset loading and preprocessing.

**Key Features**:

1. **JSONL Loading**:
   ```python
   dataset = load_dataset("json", data_files="cadllm.jsonl")
   ```

2. **Shuffling and Splitting**:
   ```python
   dataset = dataset.shuffle(seed=42)
   train = dataset.select(range(2000, len(dataset)))
   eval = dataset.select(range(2000))
   ```

3. **Mapping Functions** (apply transformations):
   ```python
   dataset = dataset.map(format_example, remove_columns=dataset.column_names)
   ```

**Why `datasets`?** Provides memory-mapped, lazy loading that doesn't load the entire dataset into RAM at once.

### `peft` (Parameter-Efficient Fine-Tuning)

**Purpose**: Implements LoRA and other parameter-efficient methods.

**Key Components**:

1. **`LoraConfig`**: Configuration for LoRA adapters
   ```python
   lora_config = LoraConfig(r=16, lora_alpha=32, target_modules=[...])
   ```

2. **`get_peft_model`**: Wraps the base model with LoRA adapters
   ```python
   model = get_peft_model(model, lora_config)
   ```

3. **`PeftModel`**: For loading adapters during inference
   ```python
   model = PeftModel.from_pretrained(base_model, "./adapter")
   ```

### `torch` (PyTorch)

**Purpose**: Deep learning backend (tensors, autograd, CUDA operations).

**Key Features**:

1. **Tensors**: Multi-dimensional arrays on CPU/GPU
   ```python
   input_ids = torch.tensor([151644, 8948, ...], dtype=torch.long)
   ```

2. **Autograd**: Automatic differentiation for gradient computation
   ```python
   loss.backward()  # Computes gradients automatically
   ```

3. **CUDA**: GPU acceleration
   ```python
   model = model.cuda()  # Move to GPU
   ```

4. **Mixed Precision**: bf16/fp16 for memory efficiency
   ```python
   model = model.to(torch.bfloat16)
   ```

5. **Gradient Checkpointing**: Memory optimization
   ```python
   model.gradient_checkpointing_enable()
   ```

---

## Hardware and Precision

### bf16 (Brain Float 16) Usage

**What is bf16?** A 16-bit floating-point format with the same exponent range as fp32 (8 bits) but reduced mantissa precision (7 bits vs. 23 bits).

**Why Use bf16 on H200?**:
- **Memory Savings**: 50% reduction vs. fp32 (6 GB → 3 GB for model weights)
- **Speed**: H200 has Tensor Cores optimized for bf16, providing 2-3× speedup
- **Stability**: Same exponent range as fp32 means no risk of overflow/underflow (unlike fp16)

**Code**:
```python
bf16_supported = (
    torch.cuda.is_available()
    and hasattr(torch.cuda, "is_bf16_supported")
    and torch.cuda.is_bf16_supported()
)
dtype = torch.bfloat16 if bf16_supported else torch.float16
model = AutoModelForCausalLM.from_pretrained(model_name, dtype=dtype)
```

### tf32 (TensorFloat-32) Tradeoffs

**What is tf32?** A 19-bit format used internally by NVIDIA Ampere+ GPUs (A100, H100, H200) for matrix multiplications. It uses fp32 inputs/outputs but tf32 for computation.

**Tradeoffs**:
- **Speed**: 2-3× faster matrix multiplications on Ampere+ GPUs
- **Precision**: Slightly lower than full fp32, but sufficient for training (typically <0.1% accuracy difference)
- **Compatibility**: Only works on Ampere+ GPUs (A100, H100, H200, RTX 30/40 series)

**Code**:
```python
training_args = TrainingArguments(
    tf32=True,  # Enable TensorFloat-32
    # ...
)
```

**When to Disable**: If you need exact fp32 precision (rare for fine-tuning).

### `use_cache=False` During Training

**What is KV Cache?** During inference, the model caches key-value pairs from previous tokens to avoid recomputation:

```
Token 1: Compute K₁, V₁, cache them
Token 2: Use cached K₁, V₁, compute K₂, V₂, cache them
Token 3: Use cached K₁, V₁, K₂, V₂, compute K₃, V₃
```

**Why Disable During Training?**:
- **Memory**: KV cache requires storing `[batch_size, seq_len, num_heads, head_dim]` for each layer (significant memory overhead)
- **Not Needed**: During training, we process the entire sequence at once (no incremental generation)
- **Correctness**: KV cache assumes previous tokens are fixed, but during training we're updating the model

**Code**:
```python
if hasattr(model.config, "use_cache"):
    model.config.use_cache = False
```

**During Inference**: Re-enable for faster generation:
```python
model.config.use_cache = True
```

### Throughput Factors

**Throughput** = examples processed per second (or tokens per second)

**Factors Affecting Throughput**:

1. **Batch Size** (`per_device_train_batch_size`):
   - Larger batches → better GPU utilization → higher throughput
   - Tradeoff: More memory required
   - Typical: 4-8 for 3B model on H200

2. **Gradient Accumulation** (`gradient_accumulation_steps`):
   - Simulates larger batch size without increasing memory
   - Effective batch size = `per_device_batch_size × gradient_accumulation_steps × num_gpus`
   - Example: `batch_size=4, grad_accum=2` → effective batch size of 8

3. **Sequence Length** (`max_seq_length`):
   - Longer sequences → more computation per example → lower throughput
   - Tradeoff: Need sufficient length for DSL output (typically 512-768 tokens)
   - Memory scales quadratically with sequence length (due to attention)

4. **`group_by_length`**:
   - Groups examples by similar sequence lengths to minimize padding
   - Reduces wasted computation on padding tokens
   - Typical speedup: 10-20%

**Example Configuration**:
```python
training_args = TrainingArguments(
    per_device_train_batch_size=4,
    gradient_accumulation_steps=2,  # Effective batch size = 8
    max_seq_length=512,
    group_by_length=True,  # Optimize padding
)
```

**Expected Throughput**: ~50-100 examples/second on H200 (depending on sequence length and batch size).

---

## Concrete Examples

### Example 1: Kitchen with Cooktop and 4 Burners

**User Input**:
```
Draw a kitchen with a cooktop and 4 burners.
```

**Model Output (DSL)**:
```
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=4000 h=3000 center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
COOKTOP: rect w=800 h=800 center=(-1600,0) layer=OBJECTS closed=true anchor_wall=west
BURNER_1: circle r=150 center=(-1400,200) layer=OBJECTS closed=true anchor_wall=west subfeature_of=COOKTOP
BURNER_2: circle r=150 center=(-1400,-200) layer=OBJECTS closed=true anchor_wall=west subfeature_of=COOKTOP
BURNER_3: circle r=150 center=(-1800,200) layer=OBJECTS closed=true anchor_wall=west subfeature_of=COOKTOP
BURNER_4: circle r=150 center=(-1800,-200) layer=OBJECTS closed=true anchor_wall=west subfeature_of=COOKTOP
```

**Explanation**:
- **Room**: 4000mm × 3000mm kitchen, centered at origin
- **Cooktop**: 800mm × 800mm rectangle on west wall (center at x=-1600, room half-width is 2000mm, so -1600 is 400mm from west wall)
- **Burners**: 4 circles (radius 150mm) arranged in 2×2 grid within cooktop bounds
- **Subfeature Relationship**: All burners have `subfeature_of=COOKTOP`, allowing them to overlap the cooktop rectangle
- **Constraints Satisfied**:
  - ✅ All entities within room bounds (cooktop: x ∈ [-2000, -1200], y ∈ [-400, 400])
  - ✅ No overlaps between main entities (only cooktop, no other objects)
  - ✅ Burners overlap cooktop (allowed due to `subfeature_of`)

### Example 2: Bedroom Layout with Furniture Placement

**User Input**:
```
Create a bedroom with a queen bed, nightstand, and dresser.
```

**Model Output (DSL)**:
```
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=3000 h=3000 center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
BED_QUEEN: rect w=2000 h=1600 center=(0,-200) layer=OBJECTS closed=true anchor_wall=none
NIGHTSTAND: rect w=500 h=400 center=(-1250,0) layer=OBJECTS closed=true anchor_wall=none
DRESSER: rect w=1200 h=600 center=(0,1200) layer=OBJECTS closed=true anchor_wall=north
```

**Explanation**:
- **Room**: 3000mm × 3000mm bedroom (square)
- **Bed**: 2000mm × 1600mm queen bed, positioned slightly south of center (y=-200) to leave space for dresser
- **Nightstand**: 500mm × 400mm, positioned west of bed (x=-1250, bed half-width is 1000mm, so nightstand is 250mm from bed edge)
- **Dresser**: 1200mm × 600mm, positioned on north wall (y=1200, room half-height is 1500mm, so dresser is 300mm from north wall)
- **Constraints Satisfied**:
  - ✅ All entities within room bounds
  - ✅ No overlaps (bed, nightstand, and dresser are spatially separated)
  - ✅ Anchor walls: Dresser uses `anchor_wall=north` (wall-anchored), bed and nightstand use `anchor_wall=none` (free placement)

### Example 3: Bathroom with Fixtures Anchored to Walls

**User Input**:
```
Draw a bathroom with a sink, toilet, and bathtub.
```

**Model Output (DSL)**:
```
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=2000 h=2000 center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
SINK: rect w=600 h=500 center=(0,700) layer=OBJECTS closed=true anchor_wall=north
TOILET: rect w=400 h=700 center=(-600,-700) layer=OBJECTS closed=true anchor_wall=south
BATHTUB: rect w=1700 h=700 center=(0,-700) layer=OBJECTS closed=true anchor_wall=south
```

**Explanation**:
- **Room**: 2000mm × 2000mm bathroom (compact)
- **Sink**: 600mm × 500mm, anchored to north wall (y=700, room half-height is 1000mm, so sink is 200mm from north wall)
- **Toilet**: 400mm × 700mm, anchored to south wall, positioned west (x=-600, y=-700)
- **Bathtub**: 1700mm × 700mm, anchored to south wall, centered horizontally (x=0, y=-700)
- **Constraints Satisfied**:
  - ✅ All entities within room bounds
  - ✅ No overlaps (toilet and bathtub are on same wall but separated: toilet x=-600, bathtub spans x ∈ [-850, 850])
  - ✅ Wall anchoring: All fixtures use appropriate `anchor_wall` values (north for sink, south for toilet/bathtub)

---

## Operational Guidance

### How to Train

#### Command Line Example

```bash
python -u train_qwen.py \
    --data_path /workspace/cadllm_final.jsonl \
    --output_dir /workspace/cadllm-adapter \
    --num_train_epochs 1 \
    --max_seq_length 512 \
    --per_device_train_batch_size 4 \
    --gradient_accumulation_steps 2 \
    --learning_rate 2e-4 \
    --warmup_ratio 0.03 \
    --save_steps 500 \
    --logging_steps 50 \
    --seed 42
```

#### Using the Training Script

```bash
# From the workspace directory
cd /workspace
bash train.sh --data_path /workspace/dataset/jsonl/cadllm_final.jsonl \
              --output_dir /workspace/cadllm-adapter
```

#### Expected Output

```
======== LoRA CADLLM Fine-tuning (Qwen 3B) ========
Model:        Qwen/Qwen2.5-Coder-3B-Instruct
Dataset file: /workspace/cadllm_final.jsonl
Output dir:   /workspace/cadllm-adapter
Max seq len:  512
Epochs:       1
LR:           0.0002
Per-GPU BS:   4
Grad accum.:  2
===================================================
__ Loading CADLLM dataset...
   Total examples: 200191
   Train examples: 198191
   Eval examples:  2000
__ Loading tokenizer for length computation...
__ Formatting examples and computing lengths...
__ Loading model...
📥 Loading base model: Qwen/Qwen2.5-Coder-3B-Instruct
✅ Model + LoRA loaded
   Trainable parameters: 8,388,608 / 3,000,000,000
🚀 Starting training...
```

#### Training Time

- **Dataset Size**: 200k examples
- **Hardware**: NVIDIA H200 (single GPU)
- **Configuration**: `batch_size=4, grad_accum=2, seq_len=512`
- **Expected Time**: 4-6 hours for 1 epoch

### How to Evaluate

#### Metrics That Matter

1. **Eval Loss**: Primary metric. Should decrease during training.
   - **Good**: 0.05 - 0.15 (model is learning the DSL format)
   - **Concerning**: >0.5 (model is struggling)
   - **Overfitting**: Eval loss increases while train loss decreases

2. **DSL Validity Checks** (Post-Training):
   - **Format Compliance**: Does output start with `UNITS:`, `ORIGIN_POLICY:`, `ROOM:`, `WALLS:`?
   - **Coordinate Validity**: Are all coordinates within room bounds?
   - **Entity Completeness**: Are all entities from the instruction present in the output?
   - **Syntax Correctness**: Are attribute names correct (`anchor_wall`, not `anchorWall`)?

#### Evaluation Script Example

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-Coder-3B-Instruct",
    torch_dtype=torch.bfloat16
)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct")

# Load adapter
model = PeftModel.from_pretrained(base_model, "./cadllm-adapter")
model.eval()

# Test example
instruction = "Draw a kitchen with sink, stove, and refrigerator."
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": instruction},
]

# Generate
input_ids = tokenizer.apply_chat_template(
    messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
).to(model.device)

with torch.no_grad():
    outputs = model.generate(
        input_ids,
        max_new_tokens=512,
        temperature=0.1,  # Low temperature for deterministic output
        do_sample=False,  # Greedy decoding
    )

# Decode
response = tokenizer.decode(outputs[0][input_ids.shape[1]:], skip_special_tokens=True)
print(response)
```

#### Validation Checklist

After generating outputs, validate:

1. **Header Presence**: Check for `UNITS:`, `ORIGIN_POLICY:`, `ROOM:`, `WALLS:`
2. **Coordinate Bounds**: Parse coordinates and verify they're within room bounds
3. **Entity Count**: Count entities in output vs. instruction (e.g., "4 burners" → 4 `BURNER_*` entities)
4. **Syntax**: Check for typos in attribute names, missing colons, etc.

### How to Run Inference

#### Loading Base + Adapter

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# Load base model (can be cached)
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-Coder-3B-Instruct",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct")

# Load LoRA adapter
model = PeftModel.from_pretrained(base_model, "./cadllm-adapter")
model.eval()

# Optional: Merge adapter for faster inference (one-time cost)
# model = model.merge_and_unload()
```

#### Generation Parameters

```python
with torch.no_grad():
    outputs = model.generate(
        input_ids,
        max_new_tokens=512,        # Maximum DSL length
        temperature=0.1,          # Low for deterministic output
        do_sample=False,          # Greedy decoding (deterministic)
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
```

**Parameter Tuning**:
- **`temperature=0.1`**: Low temperature → more deterministic, format-consistent output
- **`do_sample=False`**: Greedy decoding → always picks highest-probability token
- **`max_new_tokens=512`**: Sufficient for most DSL outputs (typical length: 200-400 tokens)

### Common Failure Modes and Mitigations

#### 1. Format Drift

**Symptom**: Model outputs natural language instead of DSL:
```
"I'll create a kitchen with a sink, stove, and refrigerator..."
```

**Causes**:
- Insufficient training data
- System prompt not emphasized enough
- Model overfitting to natural language patterns

**Mitigations**:
- Increase training data (especially examples with strict DSL format)
- Strengthen system prompt (add "STRICT - must match exactly")
- Lower learning rate (prevent overfitting)
- Add format validation during training (filter out non-DSL outputs)

#### 2. Invalid Coordinates

**Symptom**: Coordinates outside room bounds:
```
ROOM: rect w=4000 h=3000 center=(0,0)
SINK: rect w=600 h=500 center=(3000,2000)  # Out of bounds!
```

**Causes**:
- Model hasn't learned coordinate system constraints
- Insufficient examples with boundary cases

**Mitigations**:
- Add validation during dataset generation (filter OOB examples)
- Include examples with objects at room edges
- Post-process outputs: clamp coordinates to room bounds (temporary fix)

#### 3. Missing Entities

**Symptom**: Instruction says "4 burners" but output only has 2:
```
COOKTOP: rect w=800 h=800 center=(-1600,0) ...
BURNER_1: circle r=150 center=(-1400,200) ...
BURNER_2: circle r=150 center=(-1400,-200) ...
# Missing BURNER_3 and BURNER_4
```

**Causes**:
- Model stops generation early (hit `max_new_tokens` or EOS token)
- Model doesn't understand "4" means 4 separate entities

**Mitigations**:
- Increase `max_new_tokens` (if hitting limit)
- Add examples with explicit entity counts ("4 burners" → 4 `BURNER_*` entities)
- Use repetition penalty to encourage generating all entities:
  ```python
  outputs = model.generate(
      ...,
      repetition_penalty=1.1,  # Slightly penalize repetition
  )
  ```

#### 4. Incorrect Attribute Names

**Symptom**: Typos in DSL attributes:
```
SINK: rect w=600 h=500 center=(0,1400) anchorWall=north  # Should be anchor_wall
```

**Causes**:
- Tokenizer splitting `anchor_wall` into multiple tokens
- Insufficient examples with all attribute variations

**Mitigations**:
- Ensure consistent attribute names in training data
- Add attribute names to tokenizer vocabulary (if custom)
- Post-process outputs: replace common typos (`anchorWall` → `anchor_wall`)

#### 5. Overfitting

**Symptom**: Training loss decreases but eval loss increases:
```
Epoch 1: train_loss=0.10, eval_loss=0.12
Epoch 2: train_loss=0.05, eval_loss=0.15  # Eval loss increased!
```

**Causes**:
- Too many epochs for dataset size
- Learning rate too high
- Insufficient regularization

**Mitigations**:
- Early stopping (stop when eval loss stops decreasing)
- Reduce learning rate (e.g., `2e-4` → `1e-4`)
- Increase LoRA dropout (`lora_dropout=0.05` → `0.1`)
- Add weight decay (already in AdamW, but can increase)

#### 6. Out of Memory (OOM)

**Symptom**: `RuntimeError: CUDA out of memory`

**Causes**:
- Batch size too large
- Sequence length too long
- Gradient accumulation not used

**Mitigations**:
- Reduce `per_device_train_batch_size` (e.g., 4 → 2)
- Reduce `max_seq_length` (e.g., 768 → 512)
- Increase `gradient_accumulation_steps` (maintain effective batch size)
- Enable gradient checkpointing (already enabled, but verify)
- Use `bf16` instead of `fp32` (already using, but verify)

---

## Conclusion

This document has covered the end-to-end technical details of the CAD prompt-enhancement fine-tuning project. Key takeaways:

1. **Goal**: Convert natural language CAD requests into strict DSL output for DXF generation
2. **Model**: Qwen2.5-Coder-3B-Instruct fine-tuned with LoRA for parameter efficiency
3. **Dataset**: 200k+ validated examples with strict quality constraints (no OOB, no overlaps)
4. **Training**: Causal language modeling with prompt masking, warmup + cosine LR schedule
5. **Hardware**: Optimized for H200 with bf16, tf32, and gradient checkpointing

For questions or issues, refer to the training logs, validation scripts, and dataset documentation in the repository.

