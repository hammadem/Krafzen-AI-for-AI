import binascii
import json
import logging

import google.generativeai as genai
import httpx
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


def _default_sheet_styling() -> str:
    """Metric-oriented CAD styling (legacy default)."""
    return """
            STYLING REQUIREMENTS (STRICT TEMPLATE TO FOLLOW):
            1. View: Strictly top-down 2D orthographic view.
            2. Background: **Pure White** with a **Faint Blue/Grey Engineering Grid** (implied 1m spacing).
            3. Line Work: High-contrast **Black Lines**. Thin lines for built-ins, Thick lines for structural walls.
            4. MANDATORY TEMPLATE ELEMENTS:
               - **Scale Ruler**: A clear graphical scale bar in the bottom right. MUST be accurate to the scene (e.g. [0--1m--2m]).
               - **Dimensions**: Add major dimension lines (Length/Width) where appropriate.
               - **Grid**: Visible grid to help visual scaling.
            5. Aesthetics: Clean, minimal CAD plot style. No artistic shadows or 3D effects.
            6. **Text**: Plain filled-black sans-serif for all labels and dimensions (no hollow/outline-only lettering).

            STRICT ARCHITECTURAL STANDARDS:
            - **Orthogonality**: All walls/furniture must be 90-degree aligned (unless explicitly diagonal).
            - **Clearance**: Ensure ~1m walking paths between furniture.
            - **Sizing**: Use standard architectural sizes (Doors ~900mm, Counters ~600mm deep).
"""


def _us_residential_sheet_styling() -> str:
    """USA residential hints: imperial labels + light sheet annotations (trace-friendly for Potrace/DXF)."""
    return """
            STYLING REQUIREMENTS — US RESIDENTIAL SHEET (IMPERIAL, TRACE-FRIENDLY):
            1. View: Strictly top-down 2D orthographic floor plan (no 3D).
            2. **Keep the floor plan the hero**: largest, clearest region = room layout, walls, doors, swings. Sheet furniture (title block, scale, north arrow) must be **compact** and use **thin single-weight** strokes so they do not dominate the raster.
            3. UNIT LABELS: Use **United States customary units** on annotations (feet and inches with marks, e.g. 12'-6\" x 14'-0\"). Avoid mm/m as primary strings.
            4. Background: **Solid white** only. Optional **very faint** 1 ft implied grid — no heavy dot screens, no gray fields, no fills behind the title block.

            DIMENSION CHAINS (DO NOT LEAVE GAPS):
            - For each rectangular room **and** the overall plan, show **complete** dimension graphics: extension lines + **continuous** dimension lines (not only tick marks) with readable values.
            - Where you show length on one side (e.g. top), also show matching width/length dimensions on the **opposite** side **or** clearly chained offsets so **bottom** and **right** edges have labeled extents — avoid missing dimensions along entire edges.

            US SHEET ELEMENTS (small and legible — NOT full-bleed graphics):
            - **Title block**: One **compact** lower-right block (few text lines): project line, FLOOR PLAN, scale text like 1/4\" = 1'-0\", sheet id. Hairline rules; **align text cleanly** inside boxes with even margins (no overlapping letters).
            - **Graphic scale bar**: Segmented linear bar with numeric labels under ticks — labels aligned horizontally with ticks.
            - **North arrow**: Simple line icon with **N** in a margin (not oversized).
            - **Room labels + principal dimensions** in ft/in beside rooms.
            - **Doors**: swings + width in inches (e.g. 32\", 36\") where annotated.

            Line quality: **Black** linework on **white** — crisp, high-contrast; avoid soft airbrush, avoid **white-on-black** or “dark UI” presentation. No solid black rectangles except short wall strokes.

            STRICT ARCHITECTURAL STANDARDS:
            - Walls/cabinetry mostly orthogonal; corridors plausible; door sizes residential.
"""


def _raster_export_constraints() -> str:
    """Shared constraints so PNG→DXF (Potrace) gets black-on-white, not inverted CAD viewports."""
    return """
            OUTPUT POLARITY (REQUIRED FOR EXPORT PIPELINE):
            - Fill the entire canvas with **white** (#FFFFFF). This is a printed sheet, NOT a dark AutoCAD viewport.
            - Draw every line, arc, letter, arrow, scale tick, and title-block rule in **black** (or very dark gray #111–#222 only if needed). **Never** output a drawing that is mostly black with white lines.
            - Do not add thick black bands, letterboxed frames, or decorative side columns. Keep margins modest and white.

            TYPOGRAPHY (FIXES HOLLOW / DOUBLE-STROKE TEXT IN SCALE AND TITLE BLOCK):
            - Render **all** text — room tags, dimensions numerals, scale labels (0, 5', 10'), title-block lines, “FEET”, sheet notes — as **solid filled black** characters using a simple plain sans-serif (Helvetica/Arial-like).
            - **Forbidden**: hollow/outlined-only lettering, fake double-line CAD font, embossed/engraved effects, glowing edges, or gray halftone fills behind letters.
            - Scale bar numbers must sit **clearly above or below** the bar with consistent baseline — no overlapping outlines.

            DIMENSION GRAPHICS:
            - Dimension strings must include the **continuous dimension line** between witness ticks (do not stop at orphan ticks without the connecting horizontal or vertical dimension segment).
"""


class GeminiService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. Gemini features will fail.")
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Use model from credentials/settings
        self.model_name = settings.GEMINI_MODEL 


    async def generate_image(
        self,
        prompt: str,
        original_prompt: str | None = None,
        previous_image_url: str | None = None,
        drawing_standard: str | None = None,
    ) -> str:
        """
        Generates an image based on the prompt using the configured Gemini Image model.
        Includes implicit validation if original_prompt is provided.
        Uses previous_image_url as context if provided to preserve history.
        Returns a base64 data URL.
        """
        if not settings.GEMINI_API_KEY:
             raise RuntimeError("Gemini API key is not configured")

        try:
            # Use specific image generation model
            model = genai.GenerativeModel(settings.GEMINI_IMAGE_MODEL)
            
            # Smart Prompt Construction with Integrated Validation
            validation_instruction = ""
            if original_prompt:
                validation_instruction = f"""
            CRITICAL PRE-GENERATION VALIDATION & CORRECTION:
            You are acting as a Senior Architect and Quality Control AI.
            
            CONTEXT:
            - **Previous Design**: An image of the previous floor plan is attached (if available). Use this as the BASE. Maintain the style, layout, and existing elements unless explicitly asked to change them.
            
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

            sheet_styling = (
                _us_residential_sheet_styling()
                if drawing_standard == "US_RESIDENTIAL"
                else _default_sheet_styling()
            )

            # Wrapper with explicit styling instructions for consistent CAD output
            enhanced_prompt = f"""
            Generate a professional 2D CAD technical drawing (floor plan) based on the specification below.
            
            IMPORTANT: You are an image generation model. You must generate an IMAGE.
            DO NOT output text descriptions. OUTPUT ONLY THE IMAGE.
            
            {validation_instruction}

            {sheet_styling}

            {_raster_export_constraints()}
            
            SPECIFICATION TO VISUALIZE:
            {prompt}
            """
            
            logger.info(f"Generating image with model {settings.GEMINI_IMAGE_MODEL}...")
            
            # Configure safety settings to strict minimal blocking (CAD drawings are safe)
            from google.generativeai.types import HarmBlockThreshold, HarmCategory
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            logger.info(f"--- GEMINI IMAGE GENERATION PROMPT ---\n{enhanced_prompt}\n----------------------------------")
            
            # Prepare content parts
            content_parts = [enhanced_prompt]
            
            # If previous image functionality is desired and supported by the model (e.g. Gemini 1.5 Pro/Flash)
            # We can download and convert the previous image to include in the prompt context
            if previous_image_url:
                try:
                    import base64
                    import io

                    image_data = None
                    if previous_image_url.startswith("data:"):
                        encoded = previous_image_url.split(",")[1]
                        image_bytes = base64.b64decode(encoded)
                        image_data = Image.open(io.BytesIO(image_bytes))
                    else:
                         async with httpx.AsyncClient() as client:
                            resp = await client.get(previous_image_url)
                            if resp.status_code == 200:
                                image_data = Image.open(io.BytesIO(resp.content))
                    
                    if image_data:
                        logger.info("Including previous image in generation context.")
                        content_parts.append(image_data)
                except (binascii.Error, IndexError, OSError, ValueError, httpx.HTTPError) as e:
                    logger.warning(f"Failed to process previous image for context: {e}")

            response = await model.generate_content_async(content_parts, safety_settings=safety_settings)
            
            # Check for refusal/empty candidates before accessing parts
            if not response.candidates:
                logger.warning("Gemini returned NO CANDIDATES.")
                logger.warning("Full Response Feedback: %s", getattr(response, "prompt_feedback", None))
                
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
            
            raise ValueError("No image data found in Gemini response")

        except Exception:
            logger.exception("Gemini image generation error")
            # Fallback to placeholder on error to keep UI functional
            return "https://placehold.co/600x400?text=Image+Generation+Failed"

    async def extract_layout_metrics_json(self, user_prompt: str, cad_dsl: str) -> dict:
        """
        Use the text model to extract measurable residential layout fields for IRC baseline screening.
        Returns a dict matching LayoutExtract (rooms, doors, stairs, egress windows).
        """
        if not settings.GEMINI_API_KEY:
            logger.warning("extract_layout_metrics_json: GEMINI_API_KEY missing")
            return {}

        prompt = f"""You extract measurable RESIDENTIAL layout metrics for US IRC-style baseline screening (not legal advice).

USER REQUEST:
{user_prompt}

CAD / SPEC (DSL):
{cad_dsl}

Instructions:
- Residential spaces only. Include rooms with explicit or clearly inferable dimensions.
- Prefer US customary units in output: feet for ceiling height and areas in square feet; door widths in inches; stair rise/tread in inches.
- **Populate numeric fields whenever USER REQUEST or SPEC states dimensions** (e.g. "14 ft by 12 ft bedroom", "8 ft ceiling", "36 inch door", "6 sq ft egress"). Prefer extracting from USER REQUEST first when present.
- **Multi-room / apartments**: If the user asks for multiple bedrooms or lists rooms (kitchen, living, bath), emit **one rooms[] entry per named sleeping space** when sizes exist (e.g. "Bedroom 1", "Bedroom 2"). If only counts are given ("2 bedrooms") without sizes, set notes explaining missing dimensions — still output rooms[] rows with null areas rather than omitting bedrooms entirely.
- If a value truly cannot be inferred, use null (not 0).
- bedroom: include area_sqft when computable from dimensions (length × width).
- doors_inches: list each distinct door width if inferable (e.g. standard 32, 36).
- stairs: rise_in and tread_in only if stairs are mentioned or clearly implied.
- egress_windows_sqft: **one entry per sleeping-room egress opening** when inferable. If dimensions are given as inches (e.g. 18\" × 36\", 24\" × 44\"), compute **area_sqft = (width_in × height_in) / 144** (decimal). If net clear sq ft is stated directly, use that.

Return ONLY valid JSON with this shape (no markdown):
{{
  "rooms": [{{ "name": string, "area_sqft": number|null, "ceiling_ft": number|null }}],
  "doors_inches": [{{ "width_in": number|null }}],
  "stairs": {{ "rise_in": number|null, "tread_in": number|null }} | null,
  "egress_windows_sqft": [{{ "area_sqft": number|null }}],
  "notes": string
}}
"""

        try:
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            gen_cfg = genai.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
            )
            response = await model.generate_content_async(prompt, generation_config=gen_cfg)

            if not response.candidates:
                logger.warning("Gemini layout extraction returned no candidates")
                return {}

            text = response.text or ""
            if not text.strip():
                return {}
            data = json.loads(text)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as e:
            logger.warning(f"Layout extraction JSON parse error: {e}")
            return {}
        except Exception:
            logger.exception("extract_layout_metrics_json error")
            return {}


# Global Instance
try:
    gemini_service = GeminiService()
except Exception as e:  # noqa: BLE001 - keep optional Gemini initialization from breaking app startup.
    logger.warning(f"Failed to initialize gemini_service: {e}")
    gemini_service = None
