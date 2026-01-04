from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from app.services.cadllm_service import cadllm_service
from app.services.gemini_service import gemini_service
from app.core.config import settings
import logging
import os

from app.middlewares.auth import require_auth
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, Any]] = []

class ChatResponse(BaseModel):
    original_prompt: str
    ollama_response: str
    validated_response: str
    image_url: str

class DxfRequest(BaseModel):
    image_url: str
    prompt: Optional[str] = None

@router.post("/chat/dxf", dependencies=[Depends(require_auth)])
async def generate_dxf(request: DxfRequest):
    """
    Generates a DXF file from an image URL.
    Uses External Service (Api2Convert) for high-fidelity Raster-to-Vector conversion.
    """
    try:
        from app.services.external_dxf_service import ExternalDxfService
        dxf_service = ExternalDxfService() # External provider

        logger.info(f"Requesting External DXF Conversion for image...")
        
        # Call external API
        file_path = await dxf_service.convert_to_dxf(request.image_url)
        
        # Check and Return
        if not os.path.exists(file_path):
             raise HTTPException(status_code=500, detail="Failed to retrieve DXF file from external provider")

        return FileResponse(
            path=file_path, 
            filename=os.path.basename(file_path),
            media_type='application/dxf'
        )

    except Exception as e:
        logger.error(f"DXF Generation Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/chat/generate", response_model=ChatResponse, dependencies=[Depends(require_auth)])
async def generate_chat_response(request: ChatRequest):
    """
    Process chat message:
    1. Ollama generates text.
    2. Gemini validates/corrects text (Optional/Implicit).
    3. Image Generation (Gemini or Stable Diffusion based on Config/Request).
    """
    try:
        if not cadllm_service:
             raise HTTPException(status_code=503, detail="CADLLM Service Unavailable")


        
        # Unified Flow: Always Text -> CADLLM Enhance
        # We treat the history as context for the unified prompt enhancement
        full_prompt = request.message
        
        if request.history:
            # Construct a context-aware prompt
            context_str = "\n".join([f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}" for msg in request.history])
            
            full_prompt = f"""
            PREVIOUS CONVERSATION HISTORY:
            {context_str}
            
            CURRENT USER REQUEST:
            "{request.message}"
            
            TASK:
            Based on the previous conversation and the new request, generate a UPDATED, FULL, and COMPREHENSIVE scene description. 
            Do not just describe the changes. Describe the entire scene as it should look now.
            """
            logger.info(f"Using Context-Aware Prompt. History length: {len(request.history)}")
        
        # Use CADLLM Enhance instead of generate_text (which was removed)
        logger.info(f"Generating CADLLM response for: {request.message}")
        ollama_output = await cadllm_service.enhance_prompt(full_prompt)
        
        if not ollama_output:
            raise HTTPException(status_code=500, detail="Ollama returned empty response")

        # 2. Image Generation (Gemini Only)
        logger.info("Generating Image with Gemini (Single Pass with Implicit Validation)")
        
        # Retrieve previous image URL to maintain history context
        previous_image_url = None
        if request.history:
            for msg in reversed(request.history):
                if msg.get("role") == "assistant" and msg.get("imageUrl"):
                    previous_image_url = msg.get("imageUrl")
                    break
        
        if previous_image_url:
            logger.info("Found previous image in history. Passing to Gemini for context preservation.")
        
        image_url = await gemini_service.generate_image(
            ollama_output, 
            original_prompt=request.message,
            previous_image_url=previous_image_url
        )
            
        logger.info(f"Generated Image URL: {image_url[:50]}...")

        return ChatResponse(
            original_prompt=request.message,
            ollama_response=ollama_output,
            validated_response=ollama_output,
            image_url=image_url
        )

    except Exception as e:
        logger.error(f"Chat generation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
