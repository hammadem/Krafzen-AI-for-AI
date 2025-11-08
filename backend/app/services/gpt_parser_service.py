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

Your task is to parse user instructions and generate structured CAD commands that can be used to create CAD files.

Rules:
1. Extract all geometric entities, dimensions, and relationships from the text
2. Convert measurements to consistent units (prefer metric: millimeters)
3. Identify drawing commands (line, circle, rectangle, arc, etc.)
4. Extract dimensions and coordinates
5. Identify relationships (parallel, perpendicular, tangent, etc.)
6. Output structured JSON format

Output format should be a JSON object with an "instructions" array, where each instruction has:
- command: The CAD command name (e.g., "line", "circle", "rectangle", "dimension")
- parameters: Object with command-specific parameters
- confidence: Confidence score (0.0 to 1.0)

Example commands:
- line: {start: {x, y}, end: {x, y}}
- circle: {center: {x, y}, radius: number}
- rectangle: {corner: {x, y}, width: number, height: number}
- dimension: {type: "linear"|"angular", points: [...], value: number}
"""
        
        if file_type == CADFileType.DXF:
            return base_prompt + "\nOutput format: DXF-compatible commands (ezdxf library)."
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
except ValueError:
    gpt_parser_service = None

