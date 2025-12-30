from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ollama_service import OllamaService
from app.services.gemini_service import GeminiService
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

        # 2. Image Generation (Gemini Only)
        logger.info("Generating Image with Gemini (Single Pass with Implicit Validation)")
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
