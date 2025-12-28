# Hugging Face Inference API Guide

This guide walks you through using your fine-tuned CAD-LLM model with Hugging Face Inference API for both **local testing and production use**.

## Overview

Hugging Face Inference API is the **easiest and most cost-effective** solution:
- ✅ Works for both local testing and production
- ✅ Zero infrastructure management
- ✅ Automatic scaling
- ✅ Simple API integration
- ✅ Pay-per-use pricing
- ✅ Fast deployment (minutes)
- ✅ Works on any machine (Mac, Linux, Windows) - no GPU needed
- ✅ Fast response times (1-3 seconds)

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
cd ai-ml/cadllm/NVIDIA-H200-NVL/workspace
pip install -r requirements.txt
```

This installs:
- `huggingface-hub` - For model upload and API access
- `python-dotenv` - For loading environment variables from `.env`

### Step 2: Set Up Your Token

Your Hugging Face token is already configured in `.env` file (gitignored for security).

If you need to update it:
```bash
# Edit .env file
HF_TOKEN=your_token_here
HF_USERNAME=your-username
HF_MODEL_NAME=your-username/cad-llm-krafzen
```

Or login via CLI (token will be saved):
```bash
huggingface-cli login
# Enter your token from: https://huggingface.co/settings/tokens
```

### Step 3: Merge and Upload Model

⚠️ **Important**: The Inference API requires a merged model, not just a LoRA adapter.

```bash
cd ai-ml/cadllm/NVIDIA-H200-NVL/workspace
python upload_model.py
```

**This script will:**
- Merge your LoRA adapter with the base model
- Upload the merged model to Hugging Face Hub
- Create a new repository: `your-username/cad-llm-krafzen`

**After merging, update your `.env` file:**
```bash
HF_MODEL_NAME=your-username/cad-llm-krafzen
```

**Why merge?** LoRA adapters cannot be used directly with the Inference API. The merged model combines your fine-tuned adapter with the base model into a single model.

### Step 4: Test It
```bash
# Test with default prompt
python test_hf_api.py

# Or test with a custom prompt
python test_hf_api.py "Create a circle with radius 10mm centered at origin"
```

The test script automatically:
- Loads your token and model name from `.env`
- Validates configuration
- Tests the API and shows results

**See detailed steps below for complete instructions.**

## Cost Information

### Pricing Structure

**Free Tier:**
- $0.10/month in credits (for testing)
- 30 requests/minute rate limit
- **100GB private storage included** (your model is ~1.3GB)
- Suitable for development/testing

**PRO Users ($9/month):**
- $2.00/month in credits included
- 60 requests/minute rate limit
- **1TB private storage included**
- Pay-as-you-go after credits: ~$0.00012/second for GPU inference

**Enterprise:**
- Custom pricing
- Higher rate limits
- Dedicated support

**Important Notes:**
- **Inference API costs are the same** for public and private models
- **Storage is free** up to your account limits (100GB free, 1TB PRO)
- Your model (~1.3GB) fits easily within free tier storage limits
- Additional storage (if needed): $25 per TB/month (only if you exceed limits)

## Privacy & Storage

### Privacy Settings

**By Default:**
- **Free accounts**: Models are **PUBLIC** (visible to everyone)
- **Free accounts**: Can create **PRIVATE** repositories (100GB included)
- **PRO accounts ($9/month)**: Can create private repositories (1TB included)

**To Make Your Model Private:**
- Add `--private` flag when uploading via CLI
- Or set `private=True` when creating repo via API
- Free accounts have 100GB of private storage included

**Storage Costs:**
- **Free tier**: 100GB private storage included (your model is ~1.3GB)
- **PRO tier**: 1TB private storage included
- Additional storage: $25 per TB/month (only if exceeded)
- Your model fits easily within free tier limits (~75 models of this size)

**Inference API Costs:**
- **Same pricing** for public and private models
- Costs are based on compute time, not repository privacy
- See cost breakdown below

### Cost Examples

**Per Request:**
- Average inference time: 2-3 seconds
- Cost per request: ~$0.00024 - $0.00036
- **100 requests = ~$0.024 - $0.036**

**Monthly Estimates:**
- **Light usage** (1,000 requests): ~$0.50 - $1.00/month
- **Medium usage** (10,000 requests): ~$3.60 - $5.00/month
- **Heavy usage** (100,000 requests): ~$36 - $50/month
- **Very heavy** (1,000,000 requests): ~$360 - $500/month

**Note:** Costs are based on actual compute time, so faster inference = lower costs.

## Prerequisites

1. **Hugging Face Account**
   - Sign up at https://huggingface.co/join
   - Free account works for testing

2. **Python Environment**
   ```bash
   cd ai-ml/cadllm/NVIDIA-H200-NVL/workspace
   pip install -r requirements.txt
   ```
   
   This installs all required dependencies including:
   - `huggingface-hub` - For model upload and API access
   - `python-dotenv` - For loading environment variables
   - Other dependencies for model inference

3. **Your Fine-Tuned Model**
   - Located at: `NVIDIA-H200-NVL/workspace/cad-llm-krafzen/`

## Step 1: Merge and Upload Your Model to Hugging Face Hub

⚠️ **Important**: The Hugging Face Inference API requires a **merged model**, not just a LoRA adapter. Your fine-tuned model is a LoRA adapter, so we need to merge it with the base model first.

### Option 1: Merge and Upload (Recommended - Automated)

A ready-to-use script merges your LoRA adapter with the base model and uploads it:

```bash
cd ai-ml/cadllm/NVIDIA-H200-NVL/workspace
python upload_model.py
```

**This script will:**
- Load your token and username from `.env` file automatically
- Merge the LoRA adapter with the base model (`Qwen/Qwen2.5-Coder-3B-Instruct`)
- Create a new repository for the merged model
- Upload the merged model to Hugging Face Hub
- Show you the model URL and update instructions

**Before running, make sure your `.env` file has:**
```bash
HF_TOKEN=your_token_here
HF_USERNAME=mkmad7  # or your Hugging Face username
```

**After merging, update your `.env` file:**
```bash
# Change from adapter model to merged model
HF_MODEL_NAME=mkmad7/cad-llm-krafzen
```

**Why merge?** The Inference API requires a full merged model, not just a LoRA adapter. The merged model combines your fine-tuned adapter with the base model into a single model that the API can use.

**To customize the script:**
- Set `HF_USERNAME` in your `.env` file (default: `mkmad7` if not set)
- Change `PRIVATE = True` to `False` in `upload_model.py` for a public model
- The merged model will be named `cad-llm-krafzen`

### Option 2: Upload Adapter Only (For Reference - Not for Inference API)

**Note:** This uploads just the adapter, which won't work with Inference API. Use Option 1 (merge and upload) instead.

If you want to upload just the adapter for reference:

If you prefer using the CLI:

```bash
# Install dependencies (if not already installed)
cd ai-ml/cadllm/NVIDIA-H200-NVL/workspace
pip install -r requirements.txt

# Login to Hugging Face (REQUIRED before uploading)
# Option 1: Use token from .env file
huggingface-cli login --token $(grep HF_TOKEN .env | cut -d'=' -f2)

# Option 2: Interactive login (will prompt for token)
huggingface-cli login
# Enter your token from: https://huggingface.co/settings/tokens

# Upload the model (PUBLIC by default on free accounts)
# Replace 'your-username' with your HF username
# Note: Use 'hf upload' instead of 'huggingface-cli upload' (newer command)
hf upload your-username/cad-llm-krafzen \
    ./cad-llm-krafzen \
    --repo-type model \
    --commit-message "Initial upload of fine-tuned CAD-LLM model"

# To make it PRIVATE, add --private flag
hf upload your-username/cad-llm-krafzen \
    ./cad-llm-krafzen \
    --repo-type model \
    --private \
    --commit-message "Initial upload of fine-tuned CAD-LLM model"
```

**Important:** Make sure you're logged in before uploading. If you get a 401 Unauthorized error, run `huggingface-cli login` first.

**⚠️ Important: Privacy Settings**
- **Free accounts**: Models are **PUBLIC by default**
- **Free accounts**: Can create **private repositories** (100GB included)
- **PRO accounts ($9/month)**: Can create private repositories (1TB included)
- **Inference API costs**: Same for public and private models
- **Storage**: Free tier includes 100GB private storage (your model is ~1.3GB)

## Step 2: Verify Model Upload

1. Visit your model page: `https://huggingface.co/your-username/cad-llm-krafzen`
2. Check that all files are present:
   - `adapter_model.safetensors`
   - `adapter_config.json`
   - `tokenizer.json`
   - `tokenizer_config.json`
   - Other tokenizer files

## Step 3: Set Up Inference API Access

### Get Your API Token

1. Go to https://huggingface.co/settings/tokens
2. Create a new token with **"Write"** permissions (required for uploading models)
   - **Important**: You need "Write" permissions, not just "Read"
   - "Read" tokens can only access models, not create/upload them
3. Copy the token

**Store Token Securely:**
- A `.env` file template (`.env.example`) is provided in the workspace directory
- Copy `.env.example` to `.env` and add your configuration:
  ```bash
  cd ai-ml/cadllm/NVIDIA-H200-NVL/workspace
  cp .env.example .env
  # Edit .env and add:
  # HF_TOKEN=your_token_here
  # HF_USERNAME=your-username
  # HF_MODEL_NAME=your-username/cad-llm-krafzen
  # HF_ENDPOINT_URL=  (optional - only if using dedicated endpoint)
  ```
- The `.env` file is gitignored and won't be committed
- The `cadllm_client.py` automatically loads from `.env` (requires `python-dotenv` from requirements.txt)

**Required .env variables:**
- `HF_TOKEN`: Your Hugging Face API token (required)
- `HF_USERNAME`: Your Hugging Face username, e.g., `mkmad7` (required for upload_model.py)
- `HF_MODEL_NAME`: Your model identifier, e.g., `mkmad7/cad-llm-krafzen` (required)

**Optional .env variables:**
- `HF_ENDPOINT_URL`: Only needed if you create a dedicated Inference Endpoint (see Step 6 below)
  - **Leave this unset/empty** to use the standard Inference API (recommended for most users)
  - If you create a dedicated endpoint, you'll get a URL like: `https://xxx.us-east-1.aws.endpoints.huggingface.cloud`
  - When set, the client automatically uses the endpoint instead of the standard API
  - **Note:** Most users don't need this - the standard Inference API works great!

### Test the API

A ready-to-use test script is provided that automatically loads configuration from `.env`:

```bash
cd ai-ml/cadllm/NVIDIA-H200-NVL/workspace
python test_hf_api.py
```

This will:
- Load your token and model name from `.env` file
- Test the API with a default prompt
- Show the generated output

**With a custom prompt:**
```bash
python test_hf_api.py "Create a rectangle 50x30mm centered at origin"
```

**The script (`test_hf_api.py`) includes:**
- Automatic `.env` file loading
- Configuration validation
- Error handling with helpful messages
- Progress indicators
- Formatted output

**Make sure your `.env` file has:**
- `HF_TOKEN=your_token_here` (required)
- `HF_MODEL_NAME=your-username/cad-llm-krafzen` (required)
- `HF_ENDPOINT_URL=...` (optional - only if using dedicated endpoint)

## Step 4: Use the Production Client

The `cadllm_client.py` file provides a ready-to-use client. You can use it directly:

```python
from cadllm_client import CADLLMClient

# Standard usage (automatically loads from .env)
client = CADLLMClient("your-username/cad-llm-krafzen")
result = client.generate("Create a circle with radius 10mm centered at origin")
print(result)
```

**The client automatically:**
- Loads your token from `.env` file (if `HF_TOKEN` is set)
- Formats prompts correctly
- Handles both standard Inference API and Inference Endpoints
- Provides error handling

**For custom configuration:**
```python
from cadllm_client import CADLLMClient

# With explicit token (optional - will use .env if not provided)
client = CADLLMClient(
    model_name="your-username/cad-llm-krafzen",
    token="your_token_here"
)

# With Inference Endpoint (optional - only if you created one)
# See Step 6 for details on creating endpoints
client = CADLLMClient(
    model_name="your-username/cad-llm-krafzen",
    endpoint_url="https://your-endpoint-id.us-east-1.aws.endpoints.huggingface.cloud"
)

# Batch generation
instructions = [
    "Create a rectangle 50x30mm",
    "Draw a hexagon with side length 20mm"
]
results = client.generate_batch(instructions)
for inst, result in zip(instructions, results):
    print(f"{inst}: {result[:100]}...")
```

**Note:** The client is already implemented in `cadllm_client.py` - you don't need to create it yourself. Just import and use it!

## Step 5: Integrate into Your Application

### FastAPI Integration Example

```python
# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cadllm_client import CADLLMClient
import os

app = FastAPI()

# Initialize client at startup
client = None

@app.on_event("startup")
async def startup():
    global client
    client = CADLLMClient(
        model_name=os.getenv("HF_MODEL_NAME", "your-username/cad-llm-krafzen"),
        token=os.getenv("HF_TOKEN")
    )

class GenerateRequest(BaseModel):
    instruction: str
    max_tokens: int = 400
    temperature: float = 0.7

@app.post("/generate")
async def generate(request: GenerateRequest):
    try:
        result = client.generate(
            request.instruction,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature
        )
        return {"output": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Simple Python Script

```python
# use_cadllm.py
from cadllm_client import CADLLMClient

# Token is automatically loaded from .env file
# Make sure .env exists with: HF_TOKEN=your_token_here

# Initialize (token loaded from .env automatically)
client = CADLLMClient("your-username/cad-llm-krafzen")

# Use it
result = client.generate("Create a circle with radius 10mm centered at origin")
print(result)
```

## Step 6: (Optional) Create Dedicated Inference Endpoint

For better performance and custom rate limits:

1. Go to https://huggingface.co/inference-endpoints
2. Click "New Endpoint"
3. Select your model: `your-username/cad-llm-krafzen`
4. Choose instance type:
   - **GPU Small**: Good for testing (~$0.60/hour)
   - **GPU Medium**: Production use (~$1.20/hour)
   - **GPU Large**: High traffic (~$2.40/hour)
5. Deploy (takes 2-5 minutes)

**Use the endpoint:**

After creating the endpoint, you'll get a URL like: `https://xxx.us-east-1.aws.endpoints.huggingface.cloud`

**Option 1: Set in .env file**
```bash
# Add to .env
HF_ENDPOINT_URL=https://your-endpoint-id.us-east-1.aws.endpoints.huggingface.cloud
```

Then use normally - the client will automatically use the endpoint:
```python
from cadllm_client import CADLLMClient
client = CADLLMClient("your-username/cad-llm-krafzen")
# Client automatically uses endpoint from HF_ENDPOINT_URL if set
```

**Option 2: Pass directly to client**
```python
from cadllm_client import CADLLMClient

client = CADLLMClient(
    model_name="your-username/cad-llm-krafzen",
    endpoint_url="https://your-endpoint-id.us-east-1.aws.endpoints.huggingface.cloud"
)
```

**Note:** When using an Inference Endpoint, the client uses direct HTTP requests instead of the standard Inference API. The `requests` library is required (usually already installed with `huggingface-hub`).

## Monitoring Usage and Costs

### Check Usage

1. Go to https://huggingface.co/settings/billing
2. View your usage and costs
3. Set up billing alerts

### Rate Limits

- **Free tier**: 30 requests/minute
- **PRO**: 60 requests/minute
- **Dedicated endpoints**: Custom limits

If you hit rate limits, implement retry logic:

```python
import time
from functools import wraps

def retry_on_rate_limit(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                        continue
                    raise
            return None
        return wrapper
    return decorator

# Usage
@retry_on_rate_limit()
def generate_with_retry(client, instruction):
    return client.generate(instruction)
```

## Best Practices

1. **Cache Common Queries**: Cache frequently used prompts to reduce API calls
2. **Batch Requests**: Process multiple requests together when possible
3. **Monitor Costs**: Set up billing alerts
4. **Error Handling**: Implement proper error handling and retries
5. **Token Management**: Store tokens securely (use environment variables)

## Troubleshooting

### Issue: "Model not found"
- **Solution**: Verify model name is correct and model is public (or you have access)

### Issue: "Rate limit exceeded"
- **Solution**: Upgrade to PRO or implement rate limiting in your code

### Issue: "Authentication failed" or "403 Forbidden: You don't have the rights"
- **Solution**: Your token needs **"Write"** permissions, not just "Read"
  - Go to https://huggingface.co/settings/tokens
  - Create a new token with **"Write"** permissions
  - Update your `.env` file with the new token
  - Run the upload script again

### Issue: "404 Repository Not Found" after creation fails
- **Solution**: This happens when repository creation fails due to permissions
  - Make sure your token has "Write" permissions
  - The script will show a clear error message if permissions are wrong

### Issue: Slow responses
- **Solution**: Consider creating a dedicated inference endpoint for better performance

### Issue: "StopIteration" or "Generation failed" with empty error
- **Solution**: This usually means you're trying to use a LoRA adapter directly with the Inference API
  - **The Inference API requires a merged model, not just a LoRA adapter**
  - Run `python upload_model.py` to merge your adapter with the base model
  - Update your `.env` file to use the merged model: `HF_MODEL_NAME=your-username/cad-llm-krafzen-merged`
  - Then test again with `python test_hf_api.py`

### Issue: "unexpected keyword argument 'endpoint_url'"
- **Solution**: This error means you're using an outdated version of the client
  - The `cadllm_client.py` has been updated to handle endpoints correctly
  - Make sure you're using the latest version from the workspace
  - The client now handles endpoints automatically when `HF_ENDPOINT_URL` is set in `.env`

## Next Steps

1. ✅ Upload your model to Hugging Face Hub (use `upload_model.py`)
2. ✅ Test the API using `test_hf_api.py`
3. ✅ Integrate into your application using `cadllm_client.py`
4. ✅ Monitor usage and costs
5. ✅ (Optional) Create dedicated endpoint for production

## Support

- **Hugging Face Docs**: https://huggingface.co/docs/api-inference
- **Community Forum**: https://discuss.huggingface.co
- **Pricing**: https://huggingface.co/pricing

