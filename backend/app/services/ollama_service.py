import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL_NAME

    async def generate_response(self, prompt: str) -> str:
        """
        Generates a response from the local Ollama model.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"Sending request to Ollama: {self.model}")
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                result = data.get("response", "")
                logger.info(f"Ollama generated: {result}")
                return result
        except httpx.RequestError as e:
            logger.error(f"Ollama connection error: {e}")
            raise Exception(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
