"""
FastAPI server for CAD-LLM model on Hugging Face Spaces.
"""

import os
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login

# Initialize FastAPI app
app = FastAPI(title="CAD-LLM API", version="1.0.0")

# Enable CORS for Spaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MODEL_NAME = os.getenv("HF_MODEL_NAME", "mkmad7/cad-llm-krafzen")
HF_TOKEN = os.getenv("HF_TOKEN")

# Login if token is provided
if HF_TOKEN:
    login(token=HF_TOKEN)

# Global model and tokenizer
model = None
tokenizer = None
device = "cuda" if torch.cuda.is_available() else "cpu"

# Request/Response models
class GenerateRequest(BaseModel):
    instruction: str
    max_new_tokens: int = 400
    temperature: float = 0.7
    top_p: float = 0.9

class GenerateResponse(BaseModel):
    output: str
    model: str
    device: str

def load_model():
    """Load the model and tokenizer."""
    global model, tokenizer
    
    if model is not None:
        return  # Already loaded
    
    print(f"Loading model: {MODEL_NAME}")
    print(f"Device: {device}")
    
    # Load tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        token=HF_TOKEN,
        trust_remote_code=True
    )
    
    # Ensure pad token exists
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Load model
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        token=HF_TOKEN,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True
    )
    
    if device == "cpu":
        model = model.to(device)
    
    model.eval()
    print("✅ Model loaded successfully!")

@app.on_event("startup")
async def startup():
    """Load model on startup."""
    try:
        load_model()
    except Exception as e:
        print(f"⚠️  Warning: Failed to load model on startup: {e}")
        print("   Model will be loaded on first request")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "device": device,
        "model_loaded": model is not None
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate CAD code from instruction."""
    # Load model if not already loaded
    if model is None or tokenizer is None:
        try:
            load_model()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Model not loaded: {str(e)}")
    
    try:
        # Format prompt for enhanced text output (natural language CAD descriptions)
        system_prompt = "You are a CAD code assistant. Given a vague CAD description, produce ezdxf-ready CAD operations and code-oriented text.\n\n"
        prompt = f"{system_prompt}{request.instruction}"
        
        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        
        # Generate
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id
            )
        
        # Decode
        generated_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        
        # Remove the prompt from the output
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
        
        return GenerateResponse(
            output=generated_text,
            model=MODEL_NAME,
            device=device
        )
    
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback_str = traceback.format_exc()
        print(f"❌ Generation error: {error_detail}")
        print(f"Traceback: {traceback_str}")
        raise HTTPException(
            status_code=500, 
            detail=f"Generation failed: {error_detail}"
        )

@app.get("/health")
async def health():
    """Health check with model status."""
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "device": device,
        "model_loaded": model is not None,
        "cuda_available": torch.cuda.is_available()
    }

# Note: When running in Hugging Face Spaces, uvicorn is called directly from Dockerfile
# This __main__ block is for local testing only
if __name__ == "__main__":
    import uvicorn
    # For local testing
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)

