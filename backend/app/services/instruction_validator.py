"""
Instruction Validator Service for validating and enriching parsed CAD instructions
"""

import logging
from typing import Any

from app.schemas.parser import ParsedInstruction

logger = logging.getLogger(__name__)


class InstructionValidator:
    """
    Validates and enriches parsed CAD instructions to ensure completeness.
    
    Analyzes instructions and adds missing elements based on the original text
    and common CAD patterns.
    """
    
    def __init__(self):
        """Initialize the instruction validator"""
    
    def validate_and_enrich(
        self,
        instructions: list[ParsedInstruction],
        original_text: str
    ) -> list[ParsedInstruction]:
        """
        Validate instructions and add missing elements if needed.
        
        Args:
            instructions: List of parsed instructions
            original_text: Original instruction text for context
        
        Returns:
            Enriched list of instructions with missing elements added
        """
        enriched = list(instructions)  # Start with existing instructions
        
        # Analyze what we have
        entity_counts = self._analyze_instructions(instructions)
        
        # Check for common missing patterns
        missing = self._identify_missing_elements(instructions, original_text, entity_counts)
        
        # Add missing elements
        if missing:
            logger.info(f"Adding {len(missing)} missing elements")
            enriched.extend(missing)
        
        return enriched
    
    def _analyze_instructions(self, instructions: list[ParsedInstruction]) -> dict[str, int]:
        """Analyze instructions to count entity types"""
        counts = {
            'rectangles': 0,
            'lines': 0,
            'arcs': 0,
            'dimensions': 0,
            'circles': 0
        }
        
        for instr in instructions:
            cmd = instr.command.lower()
            if cmd == 'rectangle':
                counts['rectangles'] += 1
            elif cmd == 'line':
                counts['lines'] += 1
            elif cmd == 'arc':
                counts['arcs'] += 1
            elif cmd == 'dimension':
                counts['dimensions'] += 1
            elif cmd == 'circle':
                counts['circles'] += 1
        
        return counts
    
    def _identify_missing_elements(
        self,
        instructions: list[ParsedInstruction],
        original_text: str,
        entity_counts: dict[str, int]
    ) -> list[ParsedInstruction]:
        """
        Identify missing elements based on original text and entity patterns.
        
        This is a heuristic-based approach that looks for common patterns
        and attempts to infer missing elements from the original instructions.
        """
        missing = []
        text_lower = original_text.lower()
        
        # Extract room dimensions if mentioned
        self._extract_dimension(text_lower, r"width[:\s]+(\d+)['\"]")
        self._extract_dimension(text_lower, r"depth[:\s]+(\d+)['\"]")
        
        # Check for wall elements
        if 'wall' in text_lower or 'room' in text_lower:
            wall_rects = sum(1 for instr in instructions 
                           if instr.command.lower() == 'rectangle' and 
                           self._is_large_rectangle(instr.parameters))
            
            if wall_rects < 2 and ('offset' in text_lower or 'inner' in text_lower):
                logger.debug("Potential missing inner wall rectangle")
        
        # Check for door elements
        if 'door' in text_lower:
            door_lines = sum(1 for instr in instructions 
                           if instr.command.lower() == 'line' and
                           self._is_short_line(instr.parameters))
            door_arcs = sum(1 for instr in instructions 
                          if instr.command.lower() == 'arc')
            
            if 'door' in text_lower and door_lines == 0:
                logger.debug("Potential missing door line")
            if 'swing' in text_lower and door_arcs == 0:
                logger.debug("Potential missing door swing arc")
        
        # Check for cabinet sections - count mentions of "except" or "section"
        if 'cabinet' in text_lower:
            cabinet_rects = sum(1 for instr in instructions 
                              if instr.command.lower() == 'rectangle' and
                              self._is_medium_rectangle(instr.parameters))
            
            # Count how many "except" clauses suggest multiple sections
            except_count = text_lower.count('except')
            section_count = text_lower.count('section') + text_lower.count('left') + text_lower.count('right')
            
            # If instructions mention multiple sections but we have few rectangles
            if except_count > 0 or section_count > 2:
                expected_cabinets = except_count * 2 + section_count  # Each "except" implies 2 sections
                if cabinet_rects < expected_cabinets:
                    logger.warning(f"Potential missing cabinet sections: have {cabinet_rects}, expected ~{expected_cabinets}")
        
        # Check for appliances - count specific mentions
        appliance_keywords = {
            'sink': 'sink',
            'cooktop': 'cooktop',
            'oven': 'oven',
            'refrigerator': 'refrigerator'
        }
        
        mentioned_appliances = []
        for keyword, name in appliance_keywords.items():
            if keyword in text_lower:
                mentioned_appliances.append(name)
        
        appliance_rects = sum(1 for instr in instructions 
                            if instr.command.lower() == 'rectangle' and
                            self._is_appliance_size(instr.parameters))
        
        if len(mentioned_appliances) > appliance_rects:
            logger.warning(f"Potential missing appliances: mentioned {len(mentioned_appliances)} ({', '.join(mentioned_appliances)}), have {appliance_rects}")
        
        # Try to generate missing elements based on patterns
        missing = self._generate_missing_elements(instructions, original_text, text_lower)
        
        # Log summary
        if missing:
            logger.info(f"Identified {len(missing)} potentially missing elements")
        else:
            logger.debug("No obvious missing elements detected")
        
        return missing
    
    def _generate_missing_elements(
        self,
        instructions: list[ParsedInstruction],
        original_text: str,
        text_lower: str
    ) -> list[ParsedInstruction]:
        """
        Generate missing elements based on detected patterns in the original text.
        
        This attempts to infer missing entities from the instructions and existing entities.
        """
        missing = []
        
        # Extract room dimensions
        room_width_mm = None
        room_depth_mm = None
        
        # Try to find room dimensions from existing wall rectangles
        for instr in instructions:
            if instr.command.lower() == 'rectangle':
                width = abs(float(instr.parameters.get('width', 0)))
                height = abs(float(instr.parameters.get('height', 0)))
                if width > 3000 and height > 3000:
                    room_width_mm = width
                    room_depth_mm = height
                    break
        
        # If we found room dimensions, we can calculate missing elements
        if room_width_mm and room_depth_mm:
            # Check for missing inner wall (if outer wall exists but inner doesn't)
            wall_rects = [instr for instr in instructions 
                         if instr.command.lower() == 'rectangle' and 
                         self._is_large_rectangle(instr.parameters)]
            
            if len(wall_rects) == 1 and 'offset' in text_lower:
                # Missing inner wall - calculate from outer
                outer = wall_rects[0]
                offset_mm = 127  # Default 5 inches
                if '5 inch' in text_lower or '5"' in text_lower:
                    offset_mm = 127
                
                corner = self._extract_point(outer.parameters, 'corner', (0, 0))
                inner_corner = (corner[0] + offset_mm, corner[1] + offset_mm)
                inner_width = abs(float(outer.parameters.get('width', 0))) - (2 * offset_mm)
                inner_height = abs(float(outer.parameters.get('height', 0))) - (2 * offset_mm)
                
                missing.append(ParsedInstruction(
                    command="rectangle",
                    parameters={
                        "corner": {"x": inner_corner[0], "y": inner_corner[1]},
                        "width": inner_width,
                        "height": inner_height
                    },
                    confidence=0.7
                ))
                logger.info("Generated missing inner wall rectangle")
        
        # Note: More sophisticated element generation would require parsing the original text
        # more deeply, which is complex. For now, we focus on validation and logging.
        # The improved parser prompt should handle most cases.
        
        return missing
    
    def _extract_point(self, params: dict, key: str, default: tuple) -> tuple:
        """Extract point coordinates from parameters"""
        if key in params:
            point = params[key]
            if isinstance(point, dict):
                x = float(point.get('x', default[0]))
                y = float(point.get('y', default[1]))
                return (x, y)
            elif isinstance(point, (list, tuple)) and len(point) >= 2:
                return (float(point[0]), float(point[1]))
        return default
    
    def _extract_dimension(self, text: str, pattern: str) -> float | None:
        """Extract dimension value from text using regex pattern"""
        import re
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                pass
        return None
    
    def _is_large_rectangle(self, params: dict[str, Any]) -> bool:
        """Check if rectangle is large (likely a wall/room boundary)"""
        width = abs(float(params.get('width', 0)))
        height = abs(float(params.get('height', 0)))
        return width > 3000 or height > 3000
    
    def _is_medium_rectangle(self, params: dict[str, Any]) -> bool:
        """Check if rectangle is medium-sized (likely a cabinet/fixture)"""
        width = abs(float(params.get('width', 0)))
        height = abs(float(params.get('height', 0)))
        return 200 <= width <= 2000 or 200 <= height <= 2000
    
    def _is_appliance_size(self, params: dict[str, Any]) -> bool:
        """Check if rectangle is appliance-sized"""
        width = abs(float(params.get('width', 0)))
        height = abs(float(params.get('height', 0)))
        return 600 <= width <= 1200 and 600 <= height <= 1200
    
    def _is_short_line(self, params: dict[str, Any]) -> bool:
        """Check if line is short (likely a door/window frame)"""
        start = params.get('start', {})
        end = params.get('end', {})
        if isinstance(start, dict) and isinstance(end, dict):
            dx = abs(float(end.get('x', 0)) - float(start.get('x', 0)))
            dy = abs(float(end.get('y', 0)) - float(start.get('y', 0)))
            length = (dx**2 + dy**2)**0.5
            return length < 1500
        return False


# Global instance
instruction_validator = InstructionValidator()

