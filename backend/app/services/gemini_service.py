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
            
            # Smart Prompt Construction with Integrated Validation
            validation_instruction = ""
            if original_prompt:
                validation_instruction = f"""
            CRITICAL PRE-GENERATION VALIDATION & CORRECTION:
            You are acting as a Senior Architect and Quality Control AI.
            
            INPUTS:
            - **User Request**: "{original_prompt}"
            - **Draft Spec**: The specification provided below.
            
            YOUR TASKS BEFORE DRAWING:
            1. **Completeness Check**: Compare the User Request vs The Draft Spec. If the user asked for specific items (e.g. "Kitchen Island", "Double Vanity") and they are missing, YOU MUST DRAW THEM.
            2. **Measurement & Logic Check**: 
               - Validate all dimensions. Ensure no object is overlapping or physically impossible (e.g. a 2m wide cabinet in a 1m wide hallway).
               - Ensure all objects fit within the room boundaries.
            3. **Dynamic Scale Calibration**: 
               - Analyze the maximum dimensions of the described space.
               - Set your internal viewport scale to fit the ENTIRE layout comfortably with margins.
               - The graphical Scale Ruler (required below) must match this chosen scale.
            4. **View Correction**: If request implies "Front View" or "Elevation", IGNORE it and generate a **Top-Down Floor Plan** representation instead.
            """

            # Wrapper with explicit styling instructions for consistent CAD output
            enhanced_prompt = f"""
            Generate a professional 2D CAD technical drawing (floor plan) based on the specification below.
            
            IMPORTANT: You are an image generation model. You must generate an IMAGE.
            DO NOT output text descriptions. OUTPUT ONLY THE IMAGE.
            
            {validation_instruction}

            STYLING REQUIREMENTS (STRICT TEMPLATE TO FOLLOW):
            1. View: Strictly top-down 2D orthographic view.
            2. Background: **Pure White** with a **Faint Blue/Grey Engineering Grid** (implied 1m spacing).
            3. Line Work: High-contrast **Black Lines**. Thin lines for built-ins, Thick lines for structural walls.
            4. MANDATORY TEMPLATE ELEMENTS:
               - **Scale Ruler**: A clear graphical scale bar in the bottom right. MUST be accurate to the scene (e.g. [0--1m--2m]).
               - **Dimensions**: Add major dimension lines (Length/Width) where appropriate.
               - **Grid**: Visible grid to help visual scaling.
            5. Aesthetics: Clean, minimal CAD plot style. No artistic shadows or 3D effects.

            STRICT ARCHITECTURAL STANDARDS:
            - **Orthogonality**: All walls/furniture must be 90-degree aligned (unless explicitly diagonal).
            - **Clearance**: Ensure ~1m walking paths between furniture.
            - **Sizing**: Use standard architectural sizes (Doors ~900mm, Counters ~600mm deep).
            
            SPECIFICATION TO VISUALIZE:
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

            logger.info(f"--- GEMINI IMAGE GENERATION PROMPT ---\n{enhanced_prompt}\n----------------------------------")
            
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


# Global Instance
try:
    gemini_service = GeminiService()
except Exception as e:
    logger.warning(f"Failed to initialize gemini_service: {e}")
    gemini_service = None
