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

        # 2. Gemini Validation
        logger.info("Validating with Gemini")
        validated_text = await gemini_service.validate_and_correct(ollama_output)

        # 3. Gemini Image Generation
        # Note: If validation failed (empty), we might fall back to ollama output or error
        prompt_for_image = validated_text if validated_text else ollama_output
        logger.info("Generating Image with Gemini")
        image_url = await gemini_service.generate_image(prompt_for_image)
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
