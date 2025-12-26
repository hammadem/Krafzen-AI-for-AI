"""
CADLLM Service for generating DXF files using the fine-tuned CAD-LLM model.

This service uses the Hugging Face Inference API to call the fine-tuned model
that outputs coordinates in a specific format, which are then converted to DXF files.
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
from app.services.coordinate_parser import parse_coordinates_to_dxf

logger = logging.getLogger(__name__)


class CADLLMService:
    """
    Service for generating DXF files using the fine-tuned CAD-LLM model.
    
    The model outputs coordinates in format:
    - <SOL> - Start of object
    - <Circle>: x=0.0, y=0.0, r=48.0 - Circle with center and radius
    - <Line>: x=47.5, y=-32.0 - Line coordinates (multiple lines form a polyline)
    - <Arc>: x=-8.5, y=-58.0, α=64.0, f=1.0 - Arc with center, angle, and flag
    - <EOS> - End of sequence
    
    These coordinates are then converted to DXF files.
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
        
        self.system_prompt = """You are a CAD code assistant. Given a CAD description, 
generate precise 2D CAD coordinates. Always center shapes at origin (0, 0). 
Use exact dimensions specified in the request. Generate single, closed shapes unless multiple objects are explicitly requested."""
    
    def format_prompt(self, instruction: str, input_text: str = "(none)") -> str:
        """
        Format user instruction into model prompt.
        
        Args:
            instruction: User's CAD description
            input_text: Additional input (default: "(none)")
        
        Returns:
            Formatted prompt string
        """
        text = (
            self.system_prompt
            + "\n\n### Instruction\n"
            + instruction
            + "\n\n### Input\n"
            + input_text
            + "\n\n### CAD Coordinates Output\n"
        )
        return text
    
    async def generate_dxf_from_text(
        self,
        text: str,
        filename: Optional[str] = None
    ) -> Tuple[bytes, Optional[str]]:
        """
        Generate DXF file from text description using CAD-LLM model.
        
        Args:
            text: Natural language CAD description
            filename: Optional filename for logging
        
        Returns:
            Tuple of (dxf_bytes, error_message)
        
        Raises:
            ValueError: If service is not configured
            Exception: If generation fails
        """
        if not self.is_configured():
            raise ValueError("CADLLM service is not configured. Set HF_TOKEN and HF_MODEL_NAME or HF_ENDPOINT_URL.")
        
        try:
            # Format prompt
            prompt = self.format_prompt(text)
            
            # Generate coordinates from model
            logger.info(f"Calling CAD-LLM model for text: {text[:100]}...")
            coordinates_output = await self._generate_coordinates(prompt)
            
            if not coordinates_output:
                return None, "Model returned empty output"
            
            logger.info(f"Model output received: {len(coordinates_output)} characters")
            
            # Parse coordinates to DXF
            logger.info("Converting coordinates to DXF file...")
            dxf_path = parse_coordinates_to_dxf(
                text=coordinates_output,
                output_path=None,  # Use temp file
                center_at_origin=True
            )
            
            # Read DXF file as bytes
            with open(dxf_path, 'rb') as f:
                dxf_bytes = f.read()
            
            # Clean up temp file
            try:
                os.unlink(dxf_path)
            except:
                pass
            
            logger.info(f"DXF file generated: {len(dxf_bytes)} bytes")
            return dxf_bytes, None
            
        except Exception as e:
            logger.error(f"CADLLM generation error: {e}", exc_info=True)
            return None, str(e)
    
    async def _generate_coordinates(self, prompt: str) -> str:
        """
        Call the Hugging Face model to generate coordinates.
        
        Args:
            prompt: Formatted prompt for the model
        
        Returns:
            Raw model output (coordinate format)
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
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 400,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_full_text": False
            }
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
            
            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                if "generated_text" in result[0]:
                    return result[0]["generated_text"]
                elif "text" in result[0]:
                    return result[0]["text"]
                else:
                    return str(result[0])
            elif isinstance(result, dict):
                if "generated_text" in result:
                    return result["generated_text"]
                elif "text" in result:
                    return result["text"]
                else:
                    return str(result)
            else:
                return str(result)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request to endpoint failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
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

