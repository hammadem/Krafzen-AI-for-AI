"""
JSON Instruction Parser Service for converting structured JSON to CAD instructions
"""

import json
import logging
from typing import List, Dict, Any
from app.schemas.parser import ParsedInstruction

logger = logging.getLogger(__name__)


class JSONInstructionParser:
    """
    Parses machine-readable JSON format into CAD instructions.
    
    Supports structured JSON with exact coordinates and entity definitions.
    """
    
    def __init__(self):
        """Initialize JSON instruction parser"""
        pass
    
    def parse_json(self, json_data: Dict[str, Any]) -> List[ParsedInstruction]:
        """
        Parse JSON structure into CAD instructions.
        
        Args:
            json_data: Dictionary containing entities and configuration
        
        Returns:
            List of ParsedInstruction objects
        """
        instructions = []
        units = json_data.get('units', 'inches').lower()
        entities = json_data.get('entities', {})
        
        # Conversion factor based on units
        if units == 'inches':
            unit_factor = 25.4  # Convert inches to mm
        elif units == 'feet' or units == 'ft':
            unit_factor = 304.8  # Convert feet to mm
        else:
            unit_factor = 1.0  # Assume already in mm
        
        # Process each entity
        for entity_name, entity_data in entities.items():
            if isinstance(entity_data, dict):
                # Check if it's a nested structure (like door with opening_line and swing_arc)
                if 'type' in entity_data:
                    # Single entity with type
                    instr = self._parse_entity(entity_data, entity_name, unit_factor)
                    if instr:
                        instructions.append(instr)
                else:
                    # Nested structure - process each sub-entity
                    for sub_name, sub_data in entity_data.items():
                        if isinstance(sub_data, dict) and 'type' in sub_data:
                            instr = self._parse_entity(sub_data, f"{entity_name}_{sub_name}", unit_factor)
                            if instr:
                                instructions.append(instr)
            elif isinstance(entity_data, list):
                # Multiple entities (array)
                for idx, item in enumerate(entity_data):
                    if isinstance(item, dict):
                        instr = self._parse_entity(item, f"{entity_name}_{idx}", unit_factor)
                        if instr:
                            instructions.append(instr)
        
        logger.info(f"Parsed {len(instructions)} instructions from JSON")
        return instructions
    
    def _parse_entity(self, entity_data: Dict[str, Any], entity_name: str, unit_factor: float) -> ParsedInstruction:
        """Parse a single entity from JSON data"""
        entity_type = entity_data.get('type', '').lower()
        layer = self._infer_layer_from_name(entity_name)
        
        if entity_type == 'lwpolyline' or entity_type == 'polyline':
            points = entity_data.get('points', [])
            if len(points) >= 2:
                # Convert to polyline or rectangle if 4 points
                if len(points) == 5 and points[0] == points[-1]:  # Closed rectangle
                    # Convert to rectangle format
                    x_coords = [p[0] * unit_factor for p in points[:4]]
                    y_coords = [p[1] * unit_factor for p in points[:4]]
                    min_x = min(x_coords)
                    min_y = min(y_coords)
                    max_x = max(x_coords)
                    max_y = max(y_coords)
                    
                    return ParsedInstruction(
                        command="rectangle",
                        parameters={
                            "corner": {"x": min_x, "y": min_y},
                            "width": max_x - min_x,
                            "height": max_y - min_y,
                            "layer": layer
                        },
                        confidence=1.0
                    )
                else:
                    # Convert points to mm and create polyline
                    points_mm = [[p[0] * unit_factor, p[1] * unit_factor] for p in points]
                    return ParsedInstruction(
                        command="polyline",
                        parameters={
                            "points": [{"x": p[0], "y": p[1]} for p in points_mm],
                            "close": points[0] == points[-1] if len(points) > 0 else False,
                            "layer": layer
                        },
                        confidence=1.0
                    )
        
        elif entity_type == 'line':
            start = entity_data.get('start', [0, 0])
            end = entity_data.get('end', [0, 0])
            return ParsedInstruction(
                command="line",
                parameters={
                    "start": {"x": start[0] * unit_factor, "y": start[1] * unit_factor},
                    "end": {"x": end[0] * unit_factor, "y": end[1] * unit_factor},
                    "layer": layer
                },
                confidence=1.0
            )
        
        elif entity_type == 'arc':
            center = entity_data.get('center', [0, 0])
            radius = entity_data.get('radius', 0)
            start_angle = entity_data.get('start_angle', 0)
            end_angle = entity_data.get('end_angle', 90)
            return ParsedInstruction(
                command="arc",
                parameters={
                    "center": {"x": center[0] * unit_factor, "y": center[1] * unit_factor},
                    "radius": radius * unit_factor,
                    "startAngle": start_angle,
                    "endAngle": end_angle,
                    "layer": layer
                },
                confidence=1.0
            )
        
        elif entity_type == 'circle':
            center = entity_data.get('center', [0, 0])
            radius = entity_data.get('radius', 0)
            return ParsedInstruction(
                command="circle",
                parameters={
                    "center": {"x": center[0] * unit_factor, "y": center[1] * unit_factor},
                    "radius": radius * unit_factor,
                    "layer": layer
                },
                confidence=1.0
            )
        
        elif entity_type == 'ellipse':
            # Convert ellipse to circle (use average of major/minor axes as radius)
            # If ellipse has center and radius, use as circle
            center = entity_data.get('center', [0, 0])
            radius = entity_data.get('radius', 0)
            # If ellipse has major/minor axes, use average
            if radius == 0:
                major_axis = entity_data.get('major_axis', 0)
                minor_axis = entity_data.get('minor_axis', 0)
                if major_axis > 0 and minor_axis > 0:
                    radius = (major_axis + minor_axis) / 2
                else:
                    # Default to a reasonable size
                    radius = 15  # 15mm default
            return ParsedInstruction(
                command="circle",
                parameters={
                    "center": {"x": center[0] * unit_factor, "y": center[1] * unit_factor},
                    "radius": radius * unit_factor,
                    "layer": layer
                },
                confidence=1.0
            )
        
        elif entity_type == 'rectangle':
            # Handle rectangle type explicitly
            corner = entity_data.get('corner', [0, 0])
            width = entity_data.get('width', 0)
            height = entity_data.get('height', 0)
            return ParsedInstruction(
                command="rectangle",
                parameters={
                    "corner": {"x": corner[0] * unit_factor, "y": corner[1] * unit_factor},
                    "width": width * unit_factor,
                    "height": height * unit_factor,
                    "layer": layer
                },
                confidence=1.0
            )
        
        elif entity_type == 'dimension':
            # Handle dimension type - always use Dimensions layer
            dim_type = entity_data.get('dim_type', 'linear').lower()
            if dim_type == 'linear':
                points = entity_data.get('points', [])
                value = entity_data.get('value', 0)
                if len(points) >= 2:
                    return ParsedInstruction(
                        command="dimension",
                        parameters={
                            "type": "linear",
                            "points": [{"x": p[0] * unit_factor, "y": p[1] * unit_factor} for p in points[:2]],
                            "value": value * unit_factor if value else 0,
                            "layer": "Dimensions"  # Always use Dimensions layer for dimension entities
                        },
                        confidence=1.0
                    )
            # For other dimension types, log warning but don't fail
            logger.warning(f"Unsupported dimension type: {dim_type} for {entity_name}")
            return None
        
        logger.warning(f"Unknown entity type: {entity_type} for {entity_name}")
        return None
    
    def _infer_layer_from_name(self, entity_name: str) -> str:
        """Infer layer name from entity name"""
        name_lower = entity_name.lower()
        
        if 'wall' in name_lower or 'boundary' in name_lower or 'room' in name_lower:
            return 'Walls'
        elif 'door' in name_lower or 'opening' in name_lower or 'swing' in name_lower:
            return 'Doors'
        elif 'cabinet' in name_lower or 'counter' in name_lower:
            return 'Cabinets'
        elif 'sink' in name_lower or 'stove' in name_lower or 'appliance' in name_lower or 'burner' in name_lower:
            return 'Appliances'
        elif 'dimension' in name_lower:
            return 'Dimensions'
        else:
            return 'Cabinets'  # Default


# Global instance
json_instruction_parser = JSONInstructionParser()

