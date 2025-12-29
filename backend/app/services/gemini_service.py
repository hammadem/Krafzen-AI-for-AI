import google.generativeai as genai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. Gemini features will fail.")
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Use model from credentials/settings
        self.model_name = settings.GEMINI_MODEL 

    async def validate_and_correct(self, text: str, original_prompt: str) -> str:
        """
        Validates the input text against the original prompt and corrects inaccuracies.
        Returns the corrected text.
        """
        if not settings.GEMINI_API_KEY:
             raise Exception("Gemini API Key not configured")

        prompt = f"""
        You are an expert AI CAD validator.
        
        Original User Request:
        "{original_prompt}"

        Generated Spec (to be validated):
        "{text}"
        
        Validator Instructions:
        1. **Compare** the Generated Spec against the User Request.
        2. **Missing Components**: If the User Request asked for specific items (e.g. balconies, pathways, furniture) and they are missing, ADD them.
        3. **Extra Components**: If there are weird random items not appropriate for the context, remove them.
        4. **Logic Check**: Ensure measurements and layout are physically possible.
        5. **View Correction**: The image generator is STRICTLY for Top-Down Floor Plans. If the user asked for "Front View" or "Elevation", DO NOT try to generate a vertical view. Instead, generate a floor plan that represents the layout described, but maybe add a note or Label saying "Floor Plan Representation".
        6. **Output**: Return ONLY the corrected, final Specification string. Do NOT add conversation.
        """
        
        try:
            model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini Validation Request: {prompt}")
            response = await model.generate_content_async(prompt)
            validated = response.text.strip()
            logger.info(f"Gemini Validation Response: {validated}")
            return validated
        except Exception as e:
            logger.error(f"Gemini validation error: {e}")
            # If Gemini fails, we might want to fallback to original text or raise. 
            # For now, let's log and re-raise or return original if strictly required.
            # But the requirement says "Validation & Correction (Gemini 3 API)", so failure here is critical.
            raise Exception(f"Gemini validation failed: {str(e)}")

    async def generate_image(self, prompt: str) -> str:
        """
        Generates an image based on the prompt using the configured Gemini Image model.
        Returns a base64 data URL.
        """
        if not settings.GEMINI_API_KEY:
             raise Exception("Gemini API Key not configured")

        try:
            # Use specific image generation model
            model = genai.GenerativeModel(settings.GEMINI_IMAGE_MODEL)
            
            # Wrap the DSL in a clear instruction if needed, though the model might handle raw DSL.
            # Based on testing, a clear prompt helps.
            # Wrapper with explicit styling instructions for consistent CAD output
            enhanced_prompt = f"""
            Generate a professional 2D CAD technical drawing (floor plan) based on the specification below.

            STYLING REQUIREMENTS:
            1. View: Strictly top-down 2D orthographic view.
            2. Background: Use a uniform **dark blueprint style background** strictly matching **RGB(0, 51, 102)** (Classic Engineering Blue) with a **visible fine engineering grid overlay**.
            3. Line Work: Use clear, high-contrast **white or light-colored lines** for walls and objects.
            4. Details:
               - Include a **graphical scale ruler** in the bottom corner (e.g., 0-5m).
               - Include a small **legend** or clear text labels for major furniture items.
            5. Aesthetics: Minimalist, clean, engineering precision. No 3D perspective or artistic shading.

            SPECIFICATION:
            {prompt}
            """
            
            logger.info(f"Generating image with model {settings.GEMINI_IMAGE_MODEL}...")
            response = await model.generate_content_async(enhanced_prompt)
            
            # Extract image from response
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    mime_type = part.inline_data.mime_type
                    image_data = part.inline_data.data
                    
                    # Convert to base64
                    import base64
                    base64_str = base64.b64encode(image_data).decode('utf-8')
                    return f"data:{mime_type};base64,{base64_str}"
            
            # If no inline data found, check for text (maybe SVG code?)
            if response.text:
                logger.warning("Gemini returned text instead of image data. Returning text as failure/debug.")
                # Fallback: if it returns SVG code, we might want to handle it, but for now just log it.
                return "https://placehold.co/600x400?text=Generation+returned+text+not+image"

            raise Exception("No image data found in Gemini response")

        except Exception as e:
            logger.error(f"Gemini image generation error: {e}")
            # Fallback to placeholder on error to keep UI functional
            return "https://placehold.co/600x400?text=Image+Generation+Failed"

