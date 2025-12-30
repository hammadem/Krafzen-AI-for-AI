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
        
        import asyncio
        import random

        max_retries = 3
        base_delay = 2  # seconds

        for attempt in range(max_retries + 1):
            try:
                model = genai.GenerativeModel(self.model_name)
                logger.info(f"Gemini Validation Request (Attempt {attempt+1}/{max_retries+1}): {prompt[:100]}...")
                response = await model.generate_content_async(prompt)
                validated = response.text.strip()
                logger.info(f"Gemini Validation Response: {validated[:100]}...")
                return validated
            
            except Exception as e:
                is_rate_limit = "429" in str(e) or "Quota exceeded" in str(e) or "Resource has been exhausted" in str(e)
                
                if is_rate_limit and attempt < max_retries:
                    import re
                    # Try to extract exact wait time from error message: "Please retry in 22.24s"
                    wait_match = re.search(r"retry in (\d+(\.\d+)?)s", str(e))
                    
                    if wait_match:
                        # Extract wait time and add a small buffer (1.5s)
                        delay = float(wait_match.group(1)) + 1.5
                        logger.warning(f"Gemini Rate Limit hit. API requested wait of {delay:.2f}s. Sleeping...")
                    else:
                        # Fallback to exponential backoff if no time provided
                        delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                        logger.warning(f"Gemini Rate Limit hit. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                    
                    await asyncio.sleep(delay)
                    continue
                
                if attempt == max_retries:
                    logger.error(f"Gemini validation failed after {max_retries} retries: {e}")
                    # User explicitly requested NO fallback. If validation fails, we fail.
                    raise Exception(f"Gemini validation failed after retries: {str(e)}")
                
                # Non-rate-limit errors might be fatal, but let's retry transient ones just in case, 
                # or strictly re-raise if it's not a rate limit? 
                # Safety: treat unknown errors as potentially transient but with shorter wait? 
                # For simplicity/robustness, we re-raise non-429s immediately or handle them?
                # Let's assume non-429s are bad (e.g. bad request) and re-raise.
                if not is_rate_limit:
                     logger.error(f"Gemini validation error (non-retryable): {e}")
                     raise e

    async def generate_image(self, prompt: str, original_prompt: str = None) -> str:
        """
        Generates an image based on the prompt using the configured Gemini Image model.
        Includes implicit validation if original_prompt is provided.
        Returns a base64 data URL.
        """
        if not settings.GEMINI_API_KEY:
             raise Exception("Gemini API Key not configured")

        try:
            # Use specific image generation model
            model = genai.GenerativeModel(settings.GEMINI_IMAGE_MODEL)
            
            # Smart Prompt Construction
            validation_instruction = ""
            if original_prompt:
                validation_instruction = f"""
            CRITICAL VALIDATION INSTRUCTIONS:
            1. **Cross-Check**: Compare the SPECIFICATION below against the USER REQUEST: "{original_prompt}".
            2. **Fix Missing Items**: If the User Request asked for specific items (e.g. balconies, pathways, furniture) that are missing from the Specification, YOU MUST INCLUDE THEM in the drawing.
            3. **View Logic**: If the user asked for "Front View" or "Elevation", generate a Top-Down Floor Plan representation instead.
            """

            # Wrapper with explicit styling instructions for consistent CAD output
            enhanced_prompt = f"""
            Generate a professional 2D CAD technical drawing (floor plan) based on the specification below.
            
            IMPORTANT: You are an image generation model. You must generate an IMAGE.
            DO NOT output text descriptions. OUTPUT ONLY THE IMAGE.
            
            {validation_instruction}

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
            
            # Configure safety settings to strict minimal blocking (CAD drawings are safe)
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = await model.generate_content_async(enhanced_prompt, safety_settings=safety_settings)
            
            # Check for refusal/empty candidates before accessing parts
            if not response.candidates:
                logger.warning("Gemini returned NO CANDIDATES.")
                try:
                    logger.warning(f"Full Response Feedback: {response.prompt_feedback}")
                except Exception as e:
                    logger.warning(f"Could not read prompt_feedback: {e}")
                
                return "https://placehold.co/600x400?text=Gemini+Refused+Generation"

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
                logger.warning(f"Gemini returned text instead of image data. Content: {response.text[:200]}")
                # Fallback: if it returns SVG code, we might want to handle it, but for now just log it.
                return "https://placehold.co/600x400?text=Generation+returned+text+not+image"

            raise Exception("No image data found in Gemini response")

        except Exception as e:
            logger.error(f"Gemini image generation error: {e}")
            # Fallback to placeholder on error to keep UI functional
            return "https://placehold.co/600x400?text=Image+Generation+Failed"

    async def vision_refinement(self, image_url: str, user_request: str) -> str:
        """
        Uses Gemini 2.0 Flash (Vision) to look at the previous image and 
        generate a consolidated description that includes the new user request.
        """
        if not settings.GEMINI_API_KEY:
             raise Exception("Gemini API Key not configured")

        import httpx
        from PIL import Image
        import io
        import base64

        try:
            # 1. Get Image Data
            image_data = None
            if image_url.startswith("data:"):
                # Handle base64
                encoded = image_url.split(",")[1]
                image_bytes = base64.b64decode(encoded)
                image_data = Image.open(io.BytesIO(image_bytes))
            else:
                # Handle URL
                async with httpx.AsyncClient() as client:
                    resp = await client.get(image_url)
                    resp.raise_for_status()
                    image_data = Image.open(io.BytesIO(resp.content))

            # 2. Call Vision Model
            # use 2.0 Flash for vision capabilities
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            
            prompt = f"""
            You are an expert architectural assistant.
            
            TASK:
            1. Analyze the attached floor plan image. Identify the EXACT layout, room dimensions, and position of all furniture/walls.
            2. The user wants to Modify this plan: "{user_request}".
            3. Generate a NEW, highly detailed specification that:
               - Keepts the ORIGINAL layout and dimensions for existing parts (unless the user asked to move/remove them).
               - Adds the NEW requested items in a logical place.
            
            OUTPUT:
            Return ONLY the full detailed specification text. Do not output markdown or conversation.
            """
            
            logger.info("Sending Image + Prompt to Gemini Vision...")
            response = await model.generate_content_async([prompt, image_data])
            logger.info(f"Gemini Vision Output: {response.text[:100]}...")
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Vision refinement failed: {e}")
            # Fallback: Just return the user request effectively bypassing vision
            return user_request

