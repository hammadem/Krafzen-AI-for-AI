"""
CADLLM Service for prompt enhancement.

This service uses the Hugging Face Inference API to call a fine-tuned model
that enhances basic architectural descriptions into detailed prompts for image generation.
"""

import os
import logging
import tempfile
from typing import Optional, Tuple
from pathlib import Path
import io

try:
    from huggingface_hub import InferenceClient
    import requests
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    InferenceClient = None
    requests = None

from app.core.config import settings


logger = logging.getLogger(__name__)


class CADLLMService:
    """
    Service for enhancing architectural descriptions using the fine-tuned CAD-LLM model.
    
    This service acts as a "Spec Generator", taking basic user inputs and 
    converting them into a precise Domain Specific Language (DSL) format
    that describes the floor plan geometry for the image generator.
    """
    
    def __init__(self):
        """Initialize CADLLM service"""
        self.token = os.getenv("HF_TOKEN") or getattr(settings, "HF_TOKEN", None)
        self.model_name = os.getenv("HF_MODEL_NAME") or getattr(settings, "HF_MODEL_NAME", None)
        self.endpoint_url = os.getenv("HF_ENDPOINT_URL") or getattr(settings, "HF_ENDPOINT_URL", None)
        self.timeout = int(os.getenv("HF_TIMEOUT", "180"))
        
        if not HF_AVAILABLE:
            logger.warning("huggingface_hub or requests not available. CADLLM service will not work.")
            self.client = None
            return
        
        # Initialize client based on configuration
        if self.endpoint_url:
            # Use custom endpoint (e.g., Hugging Face Space)
            self.client = None  # Will use direct HTTP requests
            self._endpoint_url = self.endpoint_url
        elif self.model_name:
            # Use standard Inference API
            self.client = InferenceClient(
                token=self.token,
                model=self.model_name
            )
            self._endpoint_url = None
        else:
            logger.warning("No HF_MODEL_NAME or HF_ENDPOINT_URL configured. CADLLM service will not work.")
            self.client = None
        

    
    async def _generate_text_response(self, prompt: str) -> str:
        """
        Call the Hugging Face model to generate text response.
        
        Args:
            prompt: Formatted prompt for the model
        
        Returns:
            Raw model output (text)
        """
        if self._endpoint_url:
            # Use direct HTTP request for custom endpoint
            return await self._generate_via_endpoint(prompt)
        else:
            # Use InferenceClient
            return await self._generate_via_client(prompt)
            

    
    async def _generate_via_client(self, prompt: str) -> str:
        """Generate using InferenceClient (standard Inference API)"""
        if not self.client:
            raise ValueError("InferenceClient not initialized")
        
        try:
            # InferenceClient.text_generation is synchronous, so we run it in executor
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.text_generation(
                    prompt=prompt,
                    max_new_tokens=400,
                    temperature=0.7,
                    top_p=0.9,
                    return_full_text=False
                )
            )
            return response
        except Exception as e:
            logger.error(f"InferenceClient generation failed: {e}")
            raise
    
    async def _generate_via_endpoint(self, prompt: str) -> str:
        """Generate using direct HTTP request (for custom endpoints like Spaces)"""
        if not requests:
            raise ValueError("requests library not available")
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        # payload for custom FastAPI app on HF Space
        payload = {
            "instruction": prompt,
            "max_new_tokens": 400,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            # Run synchronous requests.post in executor for async compatibility
            import asyncio
            loop = asyncio.get_event_loop()
            
            def make_request():
                return requests.post(
                    self._endpoint_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
            
            response = await loop.run_in_executor(None, make_request)
            response.raise_for_status()
            
            result = response.json()
            
            # Custom app returns {"output": "..."}
            if isinstance(result, dict) and "output" in result:
                return result["output"]
                
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request to endpoint failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    async def enhance_prompt(self, text: str) -> str:
        """
        Enhance a user's architectural description into a detailed prompt for image generation.
        
        Args:
            text: Basic user description (e.g., "10x12 kitchen with island")
            
        Returns:
            DSL Specification String (e.g., "UNITS: mm\nROOM: ...")
        """
        if not self.is_configured():
            raise ValueError("CADLLM service is not configured")

                # The CAD-LLM model is a specialized model trained to convert text -> DSL.
        # It is based on Qwen2.5-Coder-Instruct, which REQUIRES ChatML formatting to work correctly.
        # Without this, it treats the input as a completion task and hallucinates.
        
        formatted_prompt = f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n"
        
        prompt = formatted_prompt
        
        try:
             # reuse the existing client mechanisms
             return await self._generate_text_response(prompt)
        except Exception as e:
             logger.error(f"CADLLM prompt enhancement failed: {e}")
             # Fallback to original text if enhancement fails
             return text

    def is_configured(self) -> bool:
        """Check if service is properly configured"""
        if not HF_AVAILABLE:
            return False
        return bool(self.token and (self.model_name or self.endpoint_url))


# Global instance - only create if configured
try:
    cadllm_service = CADLLMService() if (HF_AVAILABLE and (os.getenv("HF_TOKEN") or getattr(settings, "HF_TOKEN", None))) else None
except Exception as e:
    logger.warning(f"Failed to initialize CADLLM service: {e}")
    cadllm_service = None

