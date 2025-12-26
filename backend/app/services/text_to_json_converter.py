"""
Text to JSON Converter Service

Converts natural language instructions to structured JSON format
that can be used by the JSON instruction parser for precise DXF generation.
"""

import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class TextToJSONConverter:
    """
    Converts natural language text to structured JSON format for CAD generation.
    
    This provides a middle step: Text → Structured JSON → DXF
    which is more reliable than Text → DXF directly.
    """
    
    def __init__(self):
        """Initialize text to JSON converter"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GPT_MODEL
        self.max_tokens = settings.GPT_MAX_TOKENS
        self.temperature = 0.2  # Lower temperature for more structured output
    
    async def convert_text_to_json(
        self,
        text: str,
        units: str = "inches"
    ) -> Dict[str, Any]:
        """
        Convert natural language text to structured JSON format.
        
        Args:
            text: Natural language instructions
            units: Unit system to use (inches, feet, mm)
        
        Returns:
            Structured JSON dictionary ready for JSON parser
        """
        system_prompt = """You are an expert CAD engineer. Convert natural language instructions into structured JSON format for CAD generation.

Output a JSON object with this structure:
{
  "units": "inches" | "feet" | "mm",
  "format": "DXF",
  "entities": {
    "entity_name": {
      "type": "lwpolyline" | "line" | "arc" | "circle" | "dimension" | "rectangle",
      "points": [[x, y], ...] for polylines,
      "start": [x, y], "end": [x, y] for lines,
      "center": [x, y], "radius": number, "start_angle": number, "end_angle": number for arcs,
      "center": [x, y], "radius": number for circles,
      "corner": [x, y], "width": number, "height": number for rectangles,
      "points": [[x, y], [x, y]], "value": number, "dim_type": "linear" for dimensions
    }
  }
}

CRITICAL RULES:
1. Calculate EXACT coordinates based on measurements in the text
2. Break down ALL elements into separate entities - CRITICAL for L-shaped layouts
3. Use consistent coordinate system (origin at bottom-left, X increases right, Y increases up)
4. Convert all measurements to the specified units
5. Generate ALL mentioned elements - do not skip any, including dimensions
6. For nested structures (like door with opening and swing), use nested objects
7. For arrays of similar items (like multiple cabinets), use arrays
8. For L-shaped or continuous countertop runs:
   - Break into separate rectangles for each wall section (top, left, bottom, right)
   - If a section has a gap (like sink or cooktop), create separate rectangles:
     * Rectangle for section BEFORE the gap
     * Rectangle for the gap element (sink, cooktop, etc.)
     * Rectangle for section AFTER the gap
   - Example: "cabinets along top wall except for sink" = 3 rectangles:
     * left_cabinet_section (from start to before sink)
     * sink_base (the sink area)
     * right_cabinet_section (from after sink to end)
9. When dimensions are mentioned, generate dimension entities with:
   - type: "dimension"
   - dim_type: "linear"
   - points: [[x1, y1], [x2, y2]] - the two points being dimensioned
   - value: the dimension value in the specified units
   - Place dimension lines outside the drawing boundary (offset by 50-100 units)
10. For countertops: Create rectangles that represent the countertop surface, positioned at the top of base cabinets (typically 36\" from floor for standard counter height)

Example: "12' x 10' room with 5 inch wall offset"
- Outer room: points from [0,0] to [144,0] to [144,120] to [0,120] to [0,0] (in inches)
- Inner room: offset by 5 inches = points from [5,5] to [139,5] to [139,115] to [5,115] to [5,5]
- Room width dimension: type "dimension", points [[0, 130], [144, 130]], value 144, dim_type "linear"
- Room height dimension: type "dimension", points [[150, 0], [150, 120]], value 120, dim_type "linear"

Example: "L-shaped counter: cabinets along top wall except sink, cabinets along left wall except cooktop, cabinets along bottom wall"
- top_left_cabinet: rectangle from [7, 115] to [54, 115] to [54, 91] to [7, 91] (24\" deep, before sink)
- sink_base: rectangle from [54, 115] to [90, 115] to [90, 91] to [54, 91] (36\" wide sink area)
- top_right_cabinet: rectangle from [90, 115] to [139, 115] to [139, 91] to [90, 91] (after sink)
- left_top_cabinet: rectangle from [5, 91] to [29, 91] to [29, 67] to [5, 67] (above cooktop)
- cooktop: rectangle from [5, 67] to [35, 67] to [35, 43] to [5, 43] (30\" wide cooktop)
- left_bottom_cabinet: rectangle from [5, 43] to [29, 43] to [29, 5] to [5, 5] (below cooktop)
- bottom_cabinet: rectangle from [5, 5] to [139, 5] to [139, 29] to [5, 29] (full bottom wall)
"""

        user_prompt = f"""Convert the following instructions to structured JSON format:

{text}

Use units: {units}
Calculate all coordinates precisely. Generate ALL elements mentioned."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            logger.info(f"GPT-4 JSON response received: {len(raw_response)} characters")
            
            # Parse JSON response
            try:
                json_data = json.loads(raw_response)
                
                # Ensure required fields
                if "entities" not in json_data:
                    json_data["entities"] = {}
                if "units" not in json_data:
                    json_data["units"] = units
                if "format" not in json_data:
                    json_data["format"] = "DXF"
                
                logger.info(f"Successfully converted text to JSON with {len(json_data.get('entities', {}))} entities")
                return json_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {raw_response}")
                raise ValueError(f"Invalid JSON response from GPT-4: {e}")
                
        except Exception as e:
            logger.error(f"Text to JSON conversion failed: {e}")
            raise


# Global instance
try:
    text_to_json_converter = TextToJSONConverter() if settings.OPENAI_API_KEY else None
except (ValueError, AttributeError) as e:
    logger.warning(f"Failed to initialize text to JSON converter: {e}")
    text_to_json_converter = None

