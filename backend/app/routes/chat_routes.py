from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ollama_service import OllamaService
from app.services.gemini_service import GeminiService
from app.services.stable_diffusion_service import StableDiffusionService
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    image_provider: str = "default" # "gemini", "stable-diffusion", or "default" config

class ChatResponse(BaseModel):
    original_prompt: str
    ollama_response: str
    validated_response: str
    image_url: str

@router.post("/chat/generate", response_model=ChatResponse)
async def generate_chat_response(request: ChatRequest):
    """
    Process chat message:
    1. Ollama generates text.
    2. Gemini validates/corrects text (Optional/Implicit).
    3. Image Generation (Gemini or Stable Diffusion based on Config/Request).
    """
    try:
        ollama_service = OllamaService()
        gemini_service = GeminiService()
        
        # 1. Ollama Generation
        logger.info(f"Generating Ollama response for: {request.message}")
        ollama_output = await ollama_service.generate_response(request.message)
        
        if not ollama_output:
            raise HTTPException(status_code=500, detail="Ollama returned empty response")

        # Determine Provider
        # Logic: Request override > Env Config > Default (Gemini)
        use_sd = False
        if request.image_provider == "stable-diffusion":
            use_sd = True
        elif request.image_provider == "gemini":
            use_sd = False
        else:
            # Fallback to env config
            use_sd = settings.USE_STABLE_DIFFUSION

        image_url = ""
        validated_text = ollama_output

        if use_sd:
            # 2. explicit Gemini Validation (Required for SD to get good results)
            logger.info("Validating Ollama output with Gemini (for SD path)...")
            validated_text = await gemini_service.validate_and_correct(ollama_output, request.message)
            
            # 3. SD Image Generation
            logger.info("Generating Image with Stable Diffusion (HF Space) using Validated Prompt")
            try:
                sd_service = StableDiffusionService()
                image_url = await sd_service.generate_image(validated_text)
            except Exception as e:
                logger.error(f"Stable Diffusion Failed (likely Quota/API error): {e}")
                logger.info("⚠️ Falling back to Gemini (Nano Banana) for Image Generation...")
                # Fallback to Gemini with the same validated text
                image_url = await gemini_service.generate_image(validated_text)
        else:
             # Single Pass Gemini (Optimization)
             logger.info("Generating Image with Gemini (Single Pass with Implicit Validation)")
             # We pass the raw output + original prompt, so Gemini validates & draws in one go
             image_url = await gemini_service.generate_image(ollama_output, original_prompt=request.message)
            
        logger.info(f"Generated Image URL: {image_url[:50]}...")

        return ChatResponse(
            original_prompt=request.message,
            ollama_response=ollama_output,
            validated_response=validated_text,
            image_url=image_url
        )

    except Exception as e:
        logger.error(f"Chat generation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
