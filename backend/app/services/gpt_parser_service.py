"""
GPT-4 parsing service for converting natural language text into structured CAD instructions.

This service uses GPT-4 to parse user instructions and convert them into a structured
format that can be used by CAD generators to create DXF, DWG, or other CAD file formats.
"""

import json
from typing import List, Optional
from openai import OpenAI
from app.core.config import settings
from app.schemas.parser import ParsedInstruction, CADFileType
import logging

logger = logging.getLogger(__name__)

class GPTParserService:
    """
    Service for parsing natural language text into structured CAD instructions using GPT-4.
    
    Converts user descriptions into geometric primitives (rectangles, lines, arcs, etc.)
    with calculated coordinates and parameters suitable for CAD file generation.
    """
    
    def __init__(self):
        """Initialize GPT-4 parser service"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GPT_MODEL
        self.max_tokens = settings.GPT_MAX_TOKENS
        self.temperature = settings.GPT_TEMPERATURE
    
    def _get_system_prompt(self, file_type: CADFileType) -> str:
        """Get system prompt based on file type"""
        base_prompt = """You are an expert CAD/BIM engineer specialized in converting natural language instructions into precise CAD commands.

CRITICAL: You MUST ONLY generate basic geometric primitives. Break down all complex objects into their component rectangles, lines, and arcs.

Your task is to parse user instructions and generate structured CAD commands that can be used to create CAD files.

Rules:
1. Extract all geometric entities, dimensions, and relationships from the text
2. Convert measurements to consistent units (prefer metric: millimeters)
3. ONLY use these basic commands: "line", "circle", "rectangle", "arc", "polyline", "dimension"
4. Break down complex objects into basic primitives:
   - Doors/Openings = a line (frame) + an arc (swing path if applicable)
   - Furniture/Fixtures = rectangles
   - Equipment/Machinery = rectangles
   - Structural elements = rectangles or polylines
5. Extract dimensions and coordinates
6. Calculate exact coordinates based on room dimensions and positions
7. Output structured JSON format

Output format should be a JSON object with an "instructions" array, where each instruction has:
- command: ONE OF: "line", "circle", "rectangle", "arc", "polyline", "dimension" (NO other commands)
- parameters: Object with command-specific parameters
- confidence: Confidence score (0.0 to 1.0)

Example commands:
- rectangle: {corner: {x, y}, width: number, height: number}
- line: {start: {x, y}, end: {x, y}}
- arc: {center: {x, y}, radius: number, startAngle: number, endAngle: number}
- dimension: {type: "linear", points: [{x, y}, {x, y}], value: number}

EXAMPLE BREAKDOWN:
If instructions say "cabinets along top wall except for sink area, sink centered":
- Generate rectangle for left cabinet section
- Generate rectangle for right cabinet section  
- Generate rectangle for sink (centered)
- All three as SEPARATE rectangle commands

If instructions say "base cabinets full length except for cooktop area":
- Generate rectangle for bottom cabinet section
- Generate rectangle for top cabinet section
- Generate rectangle for cooktop
- All three as SEPARATE rectangle commands

For offset operations: Create a new rectangle with calculated coordinates instead of using an "offset" command.
For openings: Create a line for the opening frame and an arc for swing paths if applicable.
For fixtures and equipment: Create rectangles at calculated positions.
"""
        
        if file_type == CADFileType.DXF:
            return base_prompt + """

CRITICAL INSTRUCTIONS FOR DXF GENERATION:
1. Generate ONLY basic geometric primitives: rectangle, line, arc, dimension. NO abstract commands.
2. Coordinate system: Origin (0,0) is bottom-left. X increases rightward, Y increases upward.
3. BREAK DOWN ALL ELEMENTS into separate entities - CRITICAL:
   - Each cabinet section = separate rectangle (e.g., "left cabinet" and "right cabinet" = 2 rectangles)
   - Each appliance = separate rectangle (sink, cooktop, refrigerator = 3 separate rectangles)
   - Each fixture = separate rectangle
   - Wall sections = separate rectangles (outer wall, inner wall = 2 rectangles)
   - Do NOT combine multiple elements into one rectangle
   - If instructions say "cabinets along wall except for X area", generate:
     * Rectangle for left section
     * Rectangle for right section  
     * Rectangle for the excluded element (X)
     * All as separate entities
4. Calculate exact coordinates based on the provided measurements:
   - Convert all measurements to millimeters (1 foot = 304.8mm, 1 inch = 25.4mm)
   - Calculate positions based on room dimensions, offsets, and specified placements
   - For walls with thickness: create outer and inner rectangles with proper offsets
   - For openings: calculate frame positions and swing arcs based on specified dimensions
   - For fixtures/equipment: position based on specified locations and dimensions
5. For dimensions: Place dimension lines outside the drawing boundary with appropriate offsets.
6. Calculate ALL coordinates precisely. Do not approximate or use placeholder values.
7. If layer is specified in instructions, include it in the parameters: {"layer": "LayerName"}
8. IMPORTANT: Generate ALL entities mentioned in the instructions. Do not skip any elements.
9. COUNT CHECK: If instructions mention multiple sections (e.g., "left cabinet" and "right cabinet"), 
   generate separate rectangles for EACH section. Do not combine them.
10. COMPLETENESS CHECKLIST - Before finalizing, verify you have generated:
    - All wall rectangles (outer + inner if offset mentioned)
    - All door elements (line + arc if swing mentioned)
    - ALL cabinet sections separately (left, right, top, bottom sections as separate rectangles)
    - ALL appliances separately (sink, cooktop, refrigerator as separate rectangles)
    - All overhead/elevated elements (as separate rectangles)
    - All dimensions mentioned
11. If instructions say "cabinets along wall except for X area", you MUST generate:
    - Rectangle for left section (before X)
    - Rectangle for right section (after X)  
    - Rectangle for X itself
    - All three as SEPARATE rectangle commands with calculated coordinates
12. Generate a MINIMUM number of entities: For a typical room layout, expect 15-25+ entities.
    If you generate fewer than 10 entities, you are likely missing elements.
"""
        elif file_type == CADFileType.DWG:
            return base_prompt + "\nOutput format: DWG-compatible commands."
        elif file_type == CADFileType.REVIT:
            return base_prompt + "\nOutput format: Revit-compatible BIM elements."
        else:
            return base_prompt
    
    async def parse_text(
        self,
        text: str,
        file_type: CADFileType = CADFileType.DXF,
        additional_context: Optional[str] = None
    ) -> tuple[List[ParsedInstruction], str]:
        """
        Parse transcribed text into CAD instructions
        
        Args:
            text: Transcribed text to parse
            file_type: Target CAD file type
            additional_context: Optional additional context
        
        Returns:
            Tuple of (parsed_instructions, raw_gpt_response)
        
        Raises:
            Exception: If parsing fails
        """
        system_prompt = self._get_system_prompt(file_type)
        
        user_prompt = f"""Parse the following instructions into CAD commands:

{text}
"""
        
        if additional_context:
            user_prompt += f"\nAdditional context: {additional_context}"
        
        user_prompt += "\n\nRespond with a valid JSON object containing an 'instructions' array. Each instruction must have 'command', 'parameters', and 'confidence' fields."
        
        try:
            # Call GPT-4 API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}  # Request JSON response
            )
            
            raw_response = response.choices[0].message.content
            logger.info(f"GPT-4 response received: {len(raw_response)} characters")
            
            # Parse JSON response
            try:
                response_json = json.loads(raw_response)
                
                # Handle different response formats
                if isinstance(response_json, dict) and "instructions" in response_json:
                    instructions_data = response_json["instructions"]
                elif isinstance(response_json, list):
                    instructions_data = response_json
                else:
                    instructions_data = [response_json]
                
                # Convert to ParsedInstruction objects
                instructions = []
                for instr_data in instructions_data:
                    try:
                        instruction = ParsedInstruction(
                            command=instr_data.get("command", ""),
                            parameters=instr_data.get("parameters", {}),
                            confidence=instr_data.get("confidence", 0.8)
                        )
                        instructions.append(instruction)
                    except Exception as e:
                        logger.warning(f"Failed to parse instruction: {e}, data: {instr_data}")
                        continue
                
                if not instructions:
                    raise ValueError("No valid instructions parsed from GPT-4 response")
                
                original_count = len(instructions)
                logger.info(f"Successfully parsed {original_count} instructions")
                
                # Validate and enrich instructions
                try:
                    from app.services.instruction_validator import instruction_validator
                    instructions = instruction_validator.validate_and_enrich(
                        instructions=instructions,
                        original_text=text
                    )
                    if len(instructions) > original_count:
                        logger.info(f"Enriched instructions: {len(instructions)} total (added {len(instructions) - original_count} elements)")
                except Exception as e:
                    logger.warning(f"Instruction validation failed: {e}. Continuing with original instructions.")
                
                return instructions, raw_response
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {raw_response}")
                raise ValueError(f"Invalid JSON response from GPT-4: {e}")
                
        except Exception as e:
            logger.error(f"GPT-4 API call failed: {e}")
            raise
    
    def is_configured(self) -> bool:
        """Check if service is properly configured"""
        return bool(settings.OPENAI_API_KEY)

# Global instance - only create if API key is configured
try:
    gpt_parser_service = GPTParserService() if settings.OPENAI_API_KEY else None
except (ValueError, AttributeError) as e:
    logger.warning(f"Failed to initialize GPT parser service: {e}")
    gpt_parser_service = None
except Exception as e:
    logger.error(f"Unexpected error initializing GPT parser service: {e}", exc_info=True)
    gpt_parser_service = None

