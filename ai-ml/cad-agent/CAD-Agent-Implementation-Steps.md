# CAD Agent - Complete Implementation Guide

**Step-by-step instructions to build and deploy your CAD Agent**

---

## Prerequisites

### Hardware Requirements

**Option 1: DeepSeek-Coder-V2-Lite (Recommended - Cheapest)**
- GPU: RTX 3060 (12GB) or RTX 3070 (8GB)
- VRAM: 6-8GB minimum
- System RAM: 16GB+
- Disk: 50GB+ free space

**Option 2: Mistral-7B (Better Performance)**
- GPU: RTX 3090 (24GB) or A4000 (16GB)
- VRAM: 8-16GB minimum
- System RAM: 16GB+
- Disk: 50GB+ free space

### Software Requirements
- Python 3.8+
- CUDA 11.8+ (for GPU training)
- Git
- Conda (optional, for pythonocc)

---

## Step 1: Download Training Datasets

**Where to Run:** Your local machine OR cloud instance (Google Colab, AWS, etc.)

**Requirements:**
- **Disk Space:** 50-100GB free (datasets are large!)
- **Internet:** Fast connection (downloading 15-43GB)
- **Time:** 1-3 hours depending on connection speed

**Recommended:** Do this on your local machine if you have the disk space, otherwise use a cloud instance.

### 1.1 CADLLM Dataset (155K samples) ⭐ START HERE

```bash
# Install datasets library
pip install datasets

# Download dataset (this will take time, ~15GB)
python -c "from datasets import load_dataset; dataset = load_dataset('lanlanguai/CADLLM', split='train'); print(f'Loaded {len(dataset)} samples')"
```

**Or download manually:**
- Visit: https://huggingface.co/datasets/lanlanguai/CADLLM
- Download the dataset files

### 1.2 SketchGraphs Dataset (15M sketches)

```bash
# Clone repository
git clone https://github.com/PrincetonLIPS/SketchGraphs.git
cd SketchGraphs
pip install -e .

# Download data (choose one format):
# Option A: Construction sequences (15GB, recommended)
# Visit: https://princetonlips.github.io/SketchGraphs
# Download: construction sequences binary file

# Option B: Filtered sequences (smaller, pre-split)
# Download: train/validation/test splits
```

### 1.3 DeepCAD Dataset (Optional but Recommended)

```bash
# Clone repository
git clone https://github.com/rundiwu/DeepCAD.git
cd DeepCAD
pip install -r requirements.txt
conda install -c conda-forge pythonocc-core=7.5.1

# Download data
# Visit: https://www.cs.columbia.edu/cg/deepcad/
# Download and extract to data/ folder:
# - cad_json/: Original JSON files
# - cad_vec/: Vectorized representation
```

---

## Step 2: Preprocess Datasets

**Where to Run:** Your local machine OR same machine where you'll train

**Requirements:**
- **Disk Space:** Same as Step 1 (processed data will be smaller)
- **CPU:** Decent CPU (preprocessing is CPU-intensive, not GPU)
- **RAM:** 8-16GB recommended
- **Time:** 2-6 hours depending on dataset size and CPU

**Recommended:** 
- **Local machine** if you have good CPU and RAM
- **Cloud instance** (AWS/GCP) if local machine is slow
- **Google Colab** for smaller datasets (free but limited storage)

**Note:** You can also do preprocessing on the same GPU machine you'll use for training (Step 3), which saves transferring large files.

### 2.1 Create Preprocessing Scripts Directory

```bash
mkdir -p scripts
mkdir -p training_data
```

### 2.2 Preprocess CADLLM Dataset

**File:** `scripts/preprocess_cadllm.py`

```python
#!/usr/bin/env python3
"""
Preprocess CADLLM dataset for training.
Extract 2D sketch commands and convert to training format.
"""
from datasets import load_dataset
import json
import os

def extract_2d_commands(ccs):
    """Extract 2D sketch commands (Line, Arc, Circle) from CAD Command Sequence."""
    commands = []
    for cmd in ccs:
        if isinstance(cmd, str):
            if any(x in cmd for x in ["<Line>", "<Arc>", "<Circle>"]):
                commands.append(cmd)
        elif isinstance(cmd, dict):
            cmd_type = cmd.get('type', '')
            if cmd_type in ['Line', 'Arc', 'Circle']:
                commands.append(cmd)
    return commands

def preprocess_cadllm_to_jsonl(output_path):
    """Convert CADLLM dataset to our jsonl training format."""
    print("Loading CADLLM dataset...")
    dataset = load_dataset("lanlanguai/CADLLM", split="train")
    
    training_examples = []
    
    for idx, sample in enumerate(dataset):
        # Get text description
        appearance = sample.get("appearance_description", "")
        parameters = sample.get("parameter_description", "")
        text_description = f"{appearance} {parameters}".strip()
        
        # Get CAD Command Sequence
        ccs = sample.get("ccs", [])
        
        # Extract 2D commands for DXF
        sketch_commands = extract_2d_commands(ccs)
        
        if not sketch_commands or not text_description:
            continue
        
        # Create training example
        enhanced_prompt = (
            f"Write complete Python code using the ezdxf library to create: {text_description}. "
            f"Use the following CAD operations: {', '.join(str(cmd) for cmd in sketch_commands[:5])}. "
            f"Generate accurate 2D geometry with proper coordinates and save as DXF file."
        )
        
        training_examples.append({
            "instruction": "Enhance this CAD prompt to be extremely detailed and compatible with ezdxf Python code generation.",
            "input": text_description,
            "output": enhanced_prompt
        })
        
        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1} samples, {len(training_examples)} examples")
    
    # Save as jsonl
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        for example in training_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"✅ Created {len(training_examples)} training examples from CADLLM")

if __name__ == "__main__":
    preprocess_cadllm_to_jsonl("training_data/cadllm_processed.jsonl")
```

**Run:**
```bash
python scripts/preprocess_cadllm.py
```

### 2.3 Preprocess SketchGraphs Dataset

**File:** `scripts/preprocess_sketchgraphs.py`

```python
#!/usr/bin/env python3
"""
Preprocess SketchGraphs dataset for CAD-LLM style training.
"""
import json
import os
from sketchgraphs.data import SequenceDataset

def sketch_to_tokenized_sequence(sketch):
    """Convert SketchGraphs sketch to tokenized sequence."""
    sequence = []
    for entity in sketch.entities:
        if entity.type == 'Line':
            sequence.append(f"LINE {entity.start[0]:.6f} {entity.start[1]:.6f} {entity.end[0]:.6f} {entity.end[1]:.6f}")
        elif entity.type == 'Circle':
            sequence.append(f"CIRCLE {entity.center[0]:.6f} {entity.center[1]:.6f} {entity.radius:.6f}")
        elif entity.type == 'Arc':
            sequence.append(f"ARC {entity.center[0]:.6f} {entity.center[1]:.6f} {entity.radius:.6f} {entity.start_angle:.6f} {entity.end_angle:.6f}")
    return sequence

def create_autocompletion_examples(sequence):
    """Create auto-completion training examples."""
    examples = []
    for mask_ratio in [0.2, 0.4, 0.6, 0.8]:
        if len(sequence) < 2:
            continue
        split_point = max(1, int(len(sequence) * mask_ratio))
        prefix = sequence[:split_point]
        completion = sequence[split_point:]
        examples.append({
            "instruction": "Complete the CAD sketch sequence:",
            "input": " ".join(prefix),
            "output": " ".join(completion)
        })
    return examples

def preprocess_sketchgraphs_to_jsonl(sketchgraphs_path, output_path, max_sketches=100000):
    """Convert SketchGraphs binary format to our jsonl training format."""
    dataset = SequenceDataset(sketchgraphs_path)
    
    training_examples = []
    
    for sketch_idx, sketch in enumerate(dataset):
        if sketch_idx >= max_sketches:
            break
            
        # Convert to tokenized sequence
        sequence = sketch_to_tokenized_sequence(sketch)
        
        if len(sequence) < 2:
            continue
        
        # Create auto-completion examples
        autocomp_examples = create_autocompletion_examples(sequence)
        training_examples.extend(autocomp_examples)
        
        if (sketch_idx + 1) % 1000 == 0:
            print(f"Processed {sketch_idx + 1} sketches, {len(training_examples)} examples")
    
    # Save as jsonl
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        for example in training_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"✅ Created {len(training_examples)} training examples from SketchGraphs")

if __name__ == "__main__":
    # Update path to your SketchGraphs data file
    sketchgraphs_path = "path/to/your/sketchgraphs/sequences.bin"
    preprocess_sketchgraphs_to_jsonl(sketchgraphs_path, "training_data/sketchgraphs_processed.jsonl")
```

**Run:**
```bash
python scripts/preprocess_sketchgraphs.py
```

### 2.4 Create ezdxf-Specific Examples (200-500 samples)

**File:** `scripts/generate_ezdxf_examples.py`

```python
#!/usr/bin/env python3
"""
Generate ezdxf-specific training examples using GPT-4o-mini.
"""
import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Example prompts for common CAD shapes
prompts = [
    "a simple spur gear",
    "L bracket with mounting holes",
    "basic house floor plan",
    "circular flange with bolt holes",
    "rectangular frame",
    "hexagonal nut",
    "keyway slot",
    "T-slot profile",
    # Add more prompts...
]

def generate_ezdxf_example(prompt):
    """Generate enhanced prompt using GPT-4o-mini."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert CAD engineer. Generate detailed Python code using ezdxf library."
            },
            {
                "role": "user",
                "content": f"Write complete Python code using the ezdxf library to create: {prompt}. Include all necessary imports, create accurate 2D geometry with proper coordinates, and save as DXF file."
            }
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    enhanced = response.choices[0].message.content
    
    return {
        "instruction": "Enhance this CAD prompt to be extremely detailed and compatible with ezdxf Python code generation.",
        "input": prompt,
        "output": enhanced
    }

def generate_all_examples():
    """Generate all ezdxf examples."""
    examples = []
    
    for prompt in prompts:
        try:
            example = generate_ezdxf_example(prompt)
            examples.append(example)
            print(f"Generated example for: {prompt}")
        except Exception as e:
            print(f"Error generating example for {prompt}: {e}")
    
    # Save
    os.makedirs("training_data", exist_ok=True)
    with open("training_data/ezdxf_examples.jsonl", 'w') as f:
        for example in examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"✅ Created {len(examples)} ezdxf-specific examples")

if __name__ == "__main__":
    generate_all_examples()
```

**Run:**
```bash
export OPENAI_API_KEY="your-api-key"
python scripts/generate_ezdxf_examples.py
```

### 2.5 Combine All Training Data

**File:** `scripts/combine_training_data.py`

```python
#!/usr/bin/env python3
"""Combine all preprocessed training data into single file."""
import json
import os

def combine_training_data():
    """Combine all training data sources."""
    all_examples = []
    
    # Load CADLLM
    if os.path.exists("training_data/cadllm_processed.jsonl"):
        with open("training_data/cadllm_processed.jsonl", 'r') as f:
            for line in f:
                all_examples.append(json.loads(line))
        print(f"Loaded {len([x for x in all_examples if 'cadllm' in str(x)])} CADLLM examples")
    
    # Load SketchGraphs
    if os.path.exists("training_data/sketchgraphs_processed.jsonl"):
        with open("training_data/sketchgraphs_processed.jsonl", 'r') as f:
            for line in f:
                all_examples.append(json.loads(line))
        print(f"Loaded SketchGraphs examples")
    
    # Load ezdxf examples
    if os.path.exists("training_data/ezdxf_examples.jsonl"):
        with open("training_data/ezdxf_examples.jsonl", 'r') as f:
            for line in f:
                all_examples.append(json.loads(line))
        print(f"Loaded ezdxf examples")
    
    # Shuffle
    import random
    random.shuffle(all_examples)
    
    # Save combined
    with open("training_data/combined_training_data.jsonl", 'w') as f:
        for example in all_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"✅ Combined {len(all_examples)} total training examples")

if __name__ == "__main__":
    combine_training_data()
```

**Run:**
```bash
python scripts/combine_training_data.py
```

---

## Step 3: Fine-Tune the Model

**Where to Run:** Google Colab (free GPU) OR local GPU OR cloud GPU (RunPod, Vast.ai)

**Requirements:**
- **GPU:** Required (RTX 3060/3070 for DeepSeek, RTX 3090 for Mistral)
- **VRAM:** 6-16GB depending on model
- **Disk:** 20-30GB for model files
- **Time:** 4-8 hours for training

**Recommended:** Google Colab (free) for first training, then move to local/cloud GPU for production.

### 3.1 Choose Your Model

**Option 1: DeepSeek-Coder-V2-Lite (Recommended - Cheapest)**
- Model: `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct`
- VRAM: 6-8GB
- Cost: 50% cheaper GPU hosting

**Option 2: Mistral-7B (Better Performance)**
- Model: `mistralai/Mistral-7B-Instruct-v0.3`
- VRAM: 8-16GB
- Performance: Slightly better CAD F1

### 3.2 Fine-Tuning Notebook (Google Colab)

**Create:** `cad_agent_finetuning.ipynb`

```python
# CELL 1 – Install & Login
!pip install -q torch transformers datasets peft trl accelerate bitsandbytes sentencepiece huggingface_hub
from huggingface_hub import login
login()  # Paste your free HF token

# CELL 2 – Imports & Model Loading
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments
from datasets import load_dataset
from peft import LoraConfig, prepare_model_for_kbit_training, get_peft_model
from trl import SFTTrainer

# Choose your model
model_name = "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"  # OR "mistralai/Mistral-7B-Instruct-v0.3"

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
dataset = load_dataset("json", data_files="training_data/combined_training_data.jsonl", split="train")

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
    num_train_epochs=20,
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

base_model = AutoModelForCausalLM.from_pretrained(model_name)
model = PeftModel.from_pretrained(base_model, "./cad-agent-mistral")
model.push_to_hub("your-username/cad-prompt-enhancer")
tokenizer.push_to_hub("your-username/cad-prompt-enhancer")
```

**Steps:**
1. **If preprocessing on local machine:**
   - Upload `training_data/combined_training_data.jsonl` to Google Colab
   - Or upload to Google Drive and mount in Colab
   
2. **If preprocessing on Colab:**
   - Just use the file directly from Colab's file system
   
3. Run all cells in the notebook
4. Model will be saved to your Hugging Face account

**File Transfer Options:**
- **Small files (<100MB):** Direct upload to Colab
- **Large files:** Upload to Google Drive, then mount in Colab:
  ```python
  from google.colab import drive
  drive.mount('/content/drive')
  # Then copy file: !cp /content/drive/MyDrive/training_data.jsonl ./
  ```

---

## Step 4: Backend Integration

### 4.1 Update Configuration

**File:** `backend/app/core/config.py`

Add to `Settings` class:

```python
# CAD Agent Configuration
CAD_AGENT_ENABLED: bool = False
CAD_AGENT_MODE: str = "huggingface"  # Options: "huggingface", "vllm_local", "vllm_remote", "tgi"
CAD_AGENT_HF_MODEL_ID: Optional[str] = None  # e.g., "your-username/cad-prompt-enhancer"
CAD_AGENT_HF_API_TOKEN: Optional[str] = None  # For Hugging Face API
CAD_AGENT_VLLM_URL: Optional[str] = None  # e.g., "http://localhost:8001"
CAD_AGENT_FALLBACK_ENABLED: bool = True
CAD_AGENT_TIMEOUT: int = 10
```

**File:** `backend/.env`

```env
# CAD Agent Configuration
CAD_AGENT_ENABLED=true
CAD_AGENT_MODE=huggingface
CAD_AGENT_HF_MODEL_ID=your-username/cad-prompt-enhancer
CAD_AGENT_HF_API_TOKEN=your-hf-token-here
CAD_AGENT_FALLBACK_ENABLED=true
CAD_AGENT_TIMEOUT=10
```

### 4.2 Create CAD Prompt Enhancer Service

**File:** `backend/app/services/cad_prompt_enhancer_service.py`

(Copy the full service code from the main guide - it's too long to include here)

### 4.3 Integrate with Existing Services

**File:** `backend/app/services/gpt_parser_service.py`

Add at top:
```python
from app.services.cad_prompt_enhancer_service import cad_prompt_enhancer_service
```

Modify `parse_text` method:
```python
async def parse_text(self, text: str, ...):
    # NEW: Enhance prompt with CAD Agent if enabled
    original_text = text
    if cad_prompt_enhancer_service and cad_prompt_enhancer_service.is_configured():
        try:
            text = await cad_prompt_enhancer_service.enhance_prompt(text)
            if text != original_text:
                logger.info(f"Prompt enhanced by CAD Agent")
        except Exception as e:
            logger.warning(f"CAD Agent enhancement failed: {e}")
            text = original_text
    
    # Rest of method unchanged...
```

**File:** `backend/app/services/text_to_json_converter.py`

Same integration pattern as above.

### 4.4 Update Requirements

**File:** `backend/requirements.txt`

Add:
```txt
httpx>=0.25.0
huggingface-hub>=0.20.0
```

---

## Step 5: Choose Hosting Option

### Option A: Hugging Face Inference API (Easiest)

**Pros:**
- ✅ No setup required
- ✅ Automatic scaling
- ✅ Free tier available

**Setup:**
1. Upload model to Hugging Face (already done in Step 3)
2. Enable Inference API on your model page
3. Get API token from https://huggingface.co/settings/tokens
4. Set in `.env`:
   ```env
   CAD_AGENT_MODE=huggingface
   CAD_AGENT_HF_MODEL_ID=your-username/cad-prompt-enhancer
   CAD_AGENT_HF_API_TOKEN=your-token
   ```

### Option B: Local GPU Server

**File:** `backend/scripts/serve_cad_agent.py`

```python
#!/usr/bin/env python3
"""CAD Agent Model Server using vLLM"""
from vllm import LLM, SamplingParams
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(title="CAD Agent Model Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

MODEL_ID = os.getenv("CAD_AGENT_MODEL_ID", "your-username/cad-prompt-enhancer")
PORT = int(os.getenv("CAD_AGENT_PORT", "8001"))

# Load model
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

class PromptRequest(BaseModel):
    prompt: str

@app.post("/enhance")
async def enhance_prompt(req: PromptRequest):
    formatted = (
        f"<s>[INST] Enhance this CAD prompt to be extremely detailed "
        f"and compatible with ezdxf Python code generation.\n"
        f"Input: {req.prompt} [/INST]"
    )
    outputs = llm.generate([formatted], sampling_params)
    enhanced = outputs[0].outputs[0].text.strip()
    return {"enhanced_prompt": enhanced}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
```

**Run:**
```bash
pip install vllm fastapi uvicorn
python backend/scripts/serve_cad_agent.py
```

**Set in `.env`:**
```env
CAD_AGENT_MODE=vllm_local
CAD_AGENT_VLLM_URL=http://localhost:8001
```

### Option C: Cloud GPU (RunPod)

1. Create RunPod account
2. Deploy GPU pod (RTX 3060/3070 for DeepSeek, RTX 3090 for Mistral)
3. Install dependencies:
   ```bash
   pip install vllm fastapi uvicorn
   ```
4. Upload and run `serve_cad_agent.py`
5. Get public URL from RunPod
6. Set in `.env`:
   ```env
   CAD_AGENT_MODE=vllm_remote
   CAD_AGENT_VLLM_URL=https://your-pod-id-8001.proxy.runpod.net
   ```

---

## Step 6: Test the Integration

### 6.1 Test Script

**File:** `backend/scripts/test_cad_agent.py`

```python
#!/usr/bin/env python3
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

**Run:**
```bash
python backend/scripts/test_cad_agent.py
```

### 6.2 Test Full Pipeline

```bash
# Start your backend
cd backend
uvicorn app.main:app --reload

# Test API endpoint
curl -X POST http://localhost:8000/api/dxf/generate-from-text-via-json \
  -H "Content-Type: application/json" \
  -d '{"text": "a simple spur gear", "units": "inches"}'
```

---

## Step 7: Deploy to Production

### 7.1 Environment Variables

Ensure all required variables are set:
```env
CAD_AGENT_ENABLED=true
CAD_AGENT_MODE=huggingface  # or vllm_local/vllm_remote
CAD_AGENT_HF_MODEL_ID=your-username/cad-prompt-enhancer
CAD_AGENT_HF_API_TOKEN=your-token
CAD_AGENT_FALLBACK_ENABLED=true
CAD_AGENT_TIMEOUT=10
```

### 7.2 Monitoring

- Check logs for enhancement success/failure
- Monitor response times
- Track enhancement quality

---

## Quick Start Summary

### Workflow Options:

**Option A: All Local (Recommended if you have resources)**
1. **Local Machine:** Download datasets (Step 1)
2. **Local Machine:** Preprocess datasets (Step 2)
3. **Google Colab:** Fine-tune model (Step 3) - upload preprocessed data
4. **Local Machine:** Backend integration (Steps 4-7)

**Option B: Cloud-Based (Recommended if limited local resources)**
1. **Cloud Instance (AWS/GCP):** Download & preprocess (Steps 1-2)
2. **Google Colab:** Fine-tune model (Step 3) - download from cloud
3. **Local Machine:** Backend integration (Steps 4-7)

**Option C: Hybrid (Best for large datasets)**
1. **Local Machine:** Download CADLLM (smallest, easiest)
2. **Cloud Instance:** Download & preprocess SketchGraphs/DeepCAD (large files)
3. **Google Colab:** Fine-tune model (Step 3)
4. **Local Machine:** Backend integration (Steps 4-7)

### Steps:
1. **Download datasets** (CADLLM, SketchGraphs, DeepCAD) - **Local or Cloud**
2. **Preprocess** all datasets to jsonl format - **Local or Cloud**
3. **Combine** training data - **Same as Step 2**
4. **Fine-tune** model on Google Colab - **Upload preprocessed data**
5. **Upload** model to Hugging Face - **Automatic from Colab**
6. **Integrate** backend service - **Local machine**
7. **Choose hosting** (HF API, local GPU, or cloud GPU) - **Local or Cloud**
8. **Test** and deploy - **Local machine**

**Estimated Time:** 8-15 hours total
**Estimated Cost:** <$0.005 per DXF generation

**Disk Space Needed:**
- **Step 1:** 50-100GB (raw datasets)
- **Step 2:** 10-20GB (processed jsonl files)
- **Step 3:** 5-10GB (model files)
- **Total:** ~70-130GB peak, can delete raw data after preprocessing

---

## Troubleshooting

### Issue: "CAD Agent not configured"
- Check environment variables are set
- Verify model ID is correct
- Ensure API token is valid

### Issue: "Model server connection failed"
- Verify server is running: `curl http://server:8001/health`
- Check firewall/network settings
- Verify URL in `CAD_AGENT_VLLM_URL`

### Issue: "Enhancement timeout"
- Increase `CAD_AGENT_TIMEOUT` (default 10s)
- Check model server performance
- Consider faster hosting option

---

**For detailed information, see:** `CAD-Agent-Complete-Guide.md`

