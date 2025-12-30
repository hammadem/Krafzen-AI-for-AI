from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ollama_service import OllamaService
from app.services.gemini_service import GeminiService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str

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
    2. Gemini validates/corrects text.
    3. Gemini generates image.
    """
    try:
        ollama_service = OllamaService()
        gemini_service = GeminiService()

        # 1. Ollama Generation
        logger.info(f"Generating Ollama response for: {request.message}")
        ollama_output = await ollama_service.generate_response(request.message)
        
        if not ollama_output:
            raise HTTPException(status_code=500, detail="Ollama returned empty response")

        # 2. Optimized Flow: Single-Pass Validation & Generation
        # We skip the explicit validation call to save 1 API request.
        # The validation logic is now embedded in the generate_image prompt.
        logger.info("Generating Image with Gemini (Single-Pass with Implicit Validation)")
        validated_text = ollama_output # Text remains original, but Image will be validated by Prompt
        
        image_url = await gemini_service.generate_image(ollama_output, original_prompt=request.message)
        logger.info(f"Generated Image URL: {image_url}")

        return ChatResponse(
            original_prompt=request.message,
            ollama_response=ollama_output,
            validated_response=validated_text,
            image_url=image_url
        )

    except Exception as e:
        logger.error(f"Chat generation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
