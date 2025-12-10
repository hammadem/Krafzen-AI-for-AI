"""
GPT-4 parsing service for converting transcribed text into CAD instructions
"""

import json
from typing import List, Optional
from openai import OpenAI
from app.core.config import settings
from app.schemas.parser import ParsedInstruction, CADFileType
import logging

logger = logging.getLogger(__name__)

class GPTParserService:
    """Service for parsing transcribed text into CAD instructions using GPT-4"""
    
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

CRITICAL: You MUST ONLY generate basic geometric primitives. Break down all complex objects (doors, cabinets, appliances, etc.) into their component rectangles, lines, and arcs.

Your task is to parse user instructions and generate structured CAD commands that can be used to create CAD files.

Rules:
1. Extract all geometric entities, dimensions, and relationships from the text
2. Convert measurements to consistent units (prefer metric: millimeters)
3. ONLY use these basic commands: "line", "circle", "rectangle", "arc", "polyline", "dimension"
4. Break down complex objects into basic primitives:
   - A door = a line (door frame) + an arc (door swing)
   - A cabinet = a rectangle
   - A sink = a rectangle (or two rectangles for sink basin)
   - An appliance = a rectangle
   - Overhead cabinets = rectangles (use dashed lines by setting linetype in parameters if needed)
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

For offset operations: Create a new rectangle with calculated coordinates instead of using an "offset" command.
For doors: Create a line for the door opening and an arc for the swing.
For cabinets: Create rectangles at calculated positions.
For appliances: Create rectangles at calculated positions.
"""
        
        if file_type == CADFileType.DXF:
            return base_prompt + """

IMPORTANT FOR DXF GENERATION:
1. Generate ONLY basic geometric primitives (rectangle, line, arc, dimension). Do NOT generate abstract commands like 'door', 'cabinet', 'sink', 'appliance', 'offset', etc.
2. Break everything down into rectangles, lines, and arcs with exact coordinates.
3. Coordinate system: Origin (0,0) is bottom-left corner. X increases right, Y increases upward.
4. Calculate exact coordinates:
   - For a 12' x 10' room: outer rectangle from (0,0) to (3657.6, 3048)
   - Inner wall offset: subtract 127mm (5 inches) from all sides
   - Base cabinets: depth 609.6mm (2 feet) inward from inner wall
   - Overhead cabinets: depth 381mm (1.25 feet) inward from inner wall, positioned above base cabinets
5. For doors: Create a line segment for the door opening, then an arc for the swing (radius = door width/2).
6. For dimensions: Place dimension lines outside the room boundary with proper offsets.
7. Ensure all measurements are converted to millimeters accurately.
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
                
                logger.info(f"Successfully parsed {len(instructions)} instructions")
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

