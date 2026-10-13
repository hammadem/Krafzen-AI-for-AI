import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL_NAME

    async def generate_response(self, prompt: str) -> str:
        """
        Generates a response from the local Ollama model.
        """
        # The original 'url' and 'payload' variables are no longer needed
        # as the request details are now inline in the client.post call.
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"--- OLLAMA REQUEST ---\nPrompt: {prompt}\n----------------------")
                
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                output_text = result.get("response", "")
                
                logger.info(f"--- OLLAMA RESPONSE ---\n{output_text}\n-----------------------")
                return output_text
        except httpx.RequestError as e:
            logger.error(f"Ollama connection error: {e}")
            raise Exception(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
