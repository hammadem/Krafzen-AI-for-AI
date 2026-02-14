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
import time

try:
    from huggingface_hub import InferenceClient
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    InferenceClient = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

HF_AVAILABLE = HF_HUB_AVAILABLE or REQUESTS_AVAILABLE

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
        
        # Determine SDK type (docker or gradio) - default to docker for backward compat
        self.sdk_type = (os.getenv("HF_SPACE_SDK") or getattr(settings, "HF_SPACE_SDK", "docker")).lower()

        # Ollama Configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL") or getattr(settings, "OLLAMA_BASE_URL", None)
        self.ollama_model = os.getenv("OLLAMA_MODEL") or getattr(settings, "OLLAMA_MODEL", "cadllm:latest")
        
        if not HF_AVAILABLE:
            logger.warning("huggingface_hub or requests not available. CADLLM service will not work.")
            self.client = None
            return
        
        # Initialize client based on configuration
        if self.endpoint_url and REQUESTS_AVAILABLE:
            # Use custom endpoint (e.g., Hugging Face Space) - HIGHEST PRIORITY
            self.client = None
            
            # Normalize URL based on SDK type
            base_url = self.endpoint_url.rstrip("/")
            if self.sdk_type == "gradio":
                if not base_url.endswith("/api/predict"):
                     # Remove /generate if user accidentally left it from docker config
                     if base_url.endswith("/generate"):
                         base_url = base_url[:-9]
                     self._endpoint_url = f"{base_url}/api/predict"
                else:
                    self._endpoint_url = base_url
            else: # docker
                if not base_url.endswith("/generate"):
                    self._endpoint_url = f"{base_url}/generate"
                else:
                    self._endpoint_url = base_url
                    
            logger.info(f"CADLLM Service using Custom Endpoint ({self.sdk_type}): {self._endpoint_url}")

        elif self.ollama_base_url and REQUESTS_AVAILABLE:
            self.client = None
            self._endpoint_url = None
            logger.info(f"CADLLM Service using Ollama at {self.ollama_base_url} with model {self.ollama_model}")
        elif self.model_name and HF_HUB_AVAILABLE:
            # Use standard Inference API
            self.client = InferenceClient(
                token=self.token,
                model=self.model_name
            )
            self._endpoint_url = None
        else:
            logger.warning("No valid CADLLM configuration found (Ollama, HF Endpoint, or HF Model).")
            self.client = None
            self._endpoint_url = None

    async def _generate_text_response(self, prompt: str) -> str:
        """
        Call the Hugging Face model to generate text response.
        
        Args:
            prompt: Formatted prompt for the model
        
        Returns:
            Raw model output (text)
        """
        if self._endpoint_url:
            # Check for Custom Endpoint FIRST (Highest Priority)
            logger.info(f"Generating via Custom Endpoint ({self.sdk_type}): {self._endpoint_url}")
            return await self._generate_via_endpoint(prompt)
        elif self.ollama_base_url:
             # Fallback to Ollama
             logger.info(f"Generating via Ollama: {self.ollama_base_url}")
             return await self._generate_via_ollama(prompt)
        else:
            # Use InferenceClient
            logger.info(f"Generating via HF Inference API: {self.model_name}")
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
    
    async def _generate_via_ollama(self, prompt: str) -> str:
        """Generate using local Ollama instance"""
        if not requests:
            raise ValueError("requests library not available")

        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.5 # As requested/tested
        }

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            def make_request():
                return requests.post(url, json=payload, timeout=self.timeout)

            response = await loop.run_in_executor(None, make_request)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def _generate_via_endpoint(self, prompt: str) -> str:
        """Generate using direct HTTP request (for custom endpoints like Spaces)"""
        if not requests:
            raise ValueError("requests library not available")
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        # Construct payload based on SDK type
        if self.sdk_type == "gradio":
            # Gradio API expects {"data": [input_args...]}
            # Your app.py likely calls generate(instruction, max_new_tokens, temperature, top_p)
            # We map "instruction" -> data[0]
            # Order MUST match the input order in the Gradio Interface
            payload = {
                "data": [
                    prompt, # instruction
                    400,    # max_new_tokens
                    0.7,    # temperature
                    0.9     # top_p
                ]
            }
        else:
             # Docker / FastAPI native payload
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
            
            start_time = time.time()
            response = await loop.run_in_executor(None, make_request)
            duration = time.time() - start_time
            logger.info(f"CADLLM Request Duration: {duration:.4f}s")
            response.raise_for_status()
            
            result = response.json()
            
            if self.sdk_type == "gradio":
                # Gradio returns {"data": ["output_string"], "duration": ...}
                if "data" in result and len(result["data"]) > 0:
                    output = result["data"][0]
                    # Sometimes Gradio returns a dictionary/JSON object as the first element if the function returns one
                    if isinstance(output, dict) and "output" in output:
                         output = output["output"]
                else:
                    logger.error(f"Unexpected Gradio response format: {result}")
                    return "" # or raise
            else:
                 # Custom Docker app returns {"output": "..."}
                if isinstance(result, dict) and "output" in result:
                    output = result["output"]
                else:
                     output = "" # Fallback

            # Common cleanup logic
            if output:
                # Check for standard ChatML specific markers in output
                if "<|im_start|>assistant" in output:
                    output = output.split("<|im_start|>assistant")[-1]
                
                # Check for plain text "assistant" marker (common in the screenshot seen)
                elif "assistant\n" in output:
                    output = output.split("assistant\n")[-1]
                    
                # Clean leading whitespace/newlines
                return output.strip()
            return ""
                 
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
        if not HF_AVAILABLE: # This variable name is slightly misleading now, but covers both deps
            return False
        
        has_ollama = bool(self.ollama_base_url)
        has_hf = bool(self.token and (self.model_name or self.endpoint_url))
        
        return has_ollama or has_hf


# Global instance - only create if configured
try:

    # Initialize if either HF is configured OR Ollama is configured
    _hf_configured = (os.getenv("HF_TOKEN") or getattr(settings, "HF_TOKEN", None))
    _ollama_configured = (os.getenv("OLLAMA_BASE_URL") or getattr(settings, "OLLAMA_BASE_URL", None))
    
    cadllm_service = CADLLMService() if (HF_AVAILABLE and (_hf_configured or _ollama_configured)) else None
except Exception as e:
    logger.warning(f"Failed to initialize CADLLM service: {e}")
    cadllm_service = None

