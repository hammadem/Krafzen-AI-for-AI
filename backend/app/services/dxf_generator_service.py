"""
DXF Generator Service for converting CAD instructions to DXF files using ezdxf.

This service provides functionality to generate DXF (Drawing Exchange Format) files
from parsed CAD instructions. It supports multiple entity types, layer management,
and line weight assignment for professional CAD drawings.
"""

import io
import logging
from typing import List, Optional, Tuple
from ezdxf import new, units
from app.schemas.parser import ParsedInstruction, CADFileType

logger = logging.getLogger(__name__)


class DXFGeneratorService:
    """
    Service for generating DXF files from parsed CAD instructions.
    
    Supports multiple entity types (rectangles, lines, arcs, circles, polylines, dimensions)
    with automatic layer assignment and line weight management.
    """
    
    # Layer definitions with line weights (in hundredths of mm)
    # Standard line weights: 13 (thin), 25 (medium), 50 (thick)
    LAYERS = {
        'Walls': {'color': 7, 'lineweight': 50},  # Thick line for structural elements
        'Cabinets': {'color': 7, 'lineweight': 25},  # Medium line for fixtures/furniture
        'Appliances': {'color': 7, 'lineweight': 25},  # Medium line for equipment
        'Doors': {'color': 7, 'lineweight': 13},  # Thin line for openings
        'Dimensions': {'color': 7, 'lineweight': 13},  # Thin line for dimensions
        'Annotations': {'color': 7, 'lineweight': 13},  # Thin line for annotations
    }
    
    def __init__(self):
        """Initialize DXF generator service"""
        self.dxf_version = 'R2010'  # DXF version (R2010 is widely compatible)
        self.units = units.MM  # Use millimeters as default unit
        
    def _extract_point(self, params: dict, key: str, default: Tuple[float, float] = (0.0, 0.0), index: Optional[int] = None) -> Tuple[float, float]:
        """Extract point coordinates from parameters"""
        if key in params:
            point = params[key]
            if isinstance(point, list) and index is not None and 0 <= index < len(point):
                # Extract from list at specific index
                point = point[index]
            
            if isinstance(point, dict):
                x = float(point.get('x', default[0]))
                y = float(point.get('y', default[1]))
                return (x, y)
            elif isinstance(point, (list, tuple)) and len(point) >= 2:
                return (float(point[0]), float(point[1]))
        return default
    
    def _extract_number(self, params: dict, key: str, default: float = 0.0) -> float:
        """Extract numeric value from parameters"""
        if key in params:
            value = params[key]
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    logger.warning(f"Could not convert {value} to float for key {key}")
        return default
    
    def _setup_layers(self, doc):
        """Create layers with appropriate line weights"""
        for layer_name, layer_props in self.LAYERS.items():
            layer = doc.layers.add(layer_name)
            layer.color = layer_props['color']
            layer.lineweight = layer_props['lineweight']
            logger.debug(f"Created layer '{layer_name}' with lineweight {layer_props['lineweight']}")
    
    def _infer_layer(self, command: str, params: dict, instruction_index: int, all_instructions: List) -> str:
        """
        Infer which layer an entity should be on based on context
        
        Args:
            command: The CAD command
            params: Command parameters
            instruction_index: Index of current instruction
            all_instructions: All instructions for context
        
        Returns:
            Layer name
        """
        # Check if layer is explicitly specified in parameters
        if 'layer' in params:
            layer_name = params['layer']
            if layer_name in self.LAYERS:
                return layer_name
        
        # Dimension commands go to Dimensions layer
        if command == 'dimension':
            return 'Dimensions'
        
        # Arc commands are typically opening swing paths or curved elements
        if command == 'arc':
            return 'Doors'
        
        # For rectangles, infer based on size and context
        if command == 'rectangle':
            width = abs(self._extract_number(params, 'width', 0))
            height = abs(self._extract_number(params, 'height', 0))
            
            # Large rectangles (typically room/space boundaries) are walls
            if width > 3000 or height > 3000:
                return 'Walls'
            
            # Medium-sized rectangles: infer based on size and position
            corner = self._extract_point(params, 'corner', (0, 0))
            x, y = corner
            
            # Medium rectangles (equipment/appliance size range)
            if 600 <= width <= 1200 and 600 <= height <= 1200:
                # Check if positioned in corners or specific areas (common for equipment)
                if (x > 2000 and y < 1000) or (x < 500 and y < 500):
                    return 'Appliances'
            
            # Small to medium rectangles (fixture/furniture size range)
            if 200 <= width <= 2000 or 200 <= height <= 2000:
                # Check if negative dimensions (might indicate overhead/elevated elements)
                if height < 0 or width < 0:
                    return 'Cabinets'
                # Default to cabinets for medium-sized rectangles
                return 'Cabinets'
            
            return 'Walls'  # Default for large rectangles
        
        # Lines could be walls or opening frames
        if command == 'line':
            start = self._extract_point(params, 'start', (0, 0))
            end = self._extract_point(params, 'end', (0, 0))
            
            # Calculate line length
            line_length = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
            
            # Short lines are typically opening frames (doors, windows)
            if line_length < 1500:  # Short line, likely opening frame
                return 'Doors'
            
            return 'Walls'  # Default for longer lines (wall segments)
        
        # Default layer
        return 'Walls'
    
    def _add_line(self, msp, params: dict, layer: str = 'Walls'):
        """Add a line entity to the modelspace"""
        start = self._extract_point(params, 'start', (0.0, 0.0))
        end = self._extract_point(params, 'end', (100.0, 100.0))
        
        line = msp.add_line(start, end)
        # Set layer and properties
        line.dxf.layer = layer
        if layer in self.LAYERS:
            line.dxf.color = self.LAYERS[layer]['color']
        else:
            line.dxf.color = 7
        logger.debug(f"Added line from {start} to {end} on layer '{layer}'")
    
    def _add_circle(self, msp, params: dict, layer: str = 'Walls'):
        """Add a circle entity to the modelspace"""
        center = self._extract_point(params, 'center', (0.0, 0.0))
        radius = self._extract_number(params, 'radius', 10.0)
        
        if radius <= 0:
            logger.warning(f"Invalid radius {radius}, using default 10.0")
            radius = 10.0
        
        circle = msp.add_circle(center, radius)
        # Set layer and properties
        circle.dxf.layer = layer
        if layer in self.LAYERS:
            circle.dxf.color = self.LAYERS[layer]['color']
        else:
            circle.dxf.color = 7
        logger.debug(f"Added circle at {center} with radius {radius} on layer '{layer}'")
    
    def _add_rectangle(self, msp, params: dict, layer: str = 'Walls'):
        """Add a rectangle entity to the modelspace"""
        corner = self._extract_point(params, 'corner', (0.0, 0.0))
        width = self._extract_number(params, 'width', 100.0)
        height = self._extract_number(params, 'height', 100.0)
        
        # Create rectangle as closed polyline
        points = [
            corner,
            (corner[0] + width, corner[1]),
            (corner[0] + width, corner[1] + height),
            (corner[0], corner[1] + height),
        ]
        
        polyline = msp.add_lwpolyline(points, close=True)
        # Set layer and properties
        polyline.dxf.layer = layer
        if layer in self.LAYERS:
            polyline.dxf.color = self.LAYERS[layer]['color']
        else:
            polyline.dxf.color = 7
        logger.debug(f"Added rectangle at {corner} with size {width}x{height} on layer '{layer}'")
    
    def _add_arc(self, msp, params: dict, layer: str = 'Doors'):
        """Add an arc entity to the modelspace"""
        center = self._extract_point(params, 'center', (0.0, 0.0))
        radius = self._extract_number(params, 'radius', 10.0)
        start_angle = self._extract_number(params, 'start_angle', 0.0)
        end_angle = self._extract_number(params, 'end_angle', 90.0)
        
        if radius <= 0:
            logger.warning(f"Invalid radius {radius}, using default 10.0")
            radius = 10.0
        
        # Convert angles from degrees to radians if needed
        # ezdxf uses degrees for angles
        arc = msp.add_arc(center, radius, start_angle, end_angle)
        # Set layer and properties
        arc.dxf.layer = layer
        if layer in self.LAYERS:
            arc.dxf.color = self.LAYERS[layer]['color']
        else:
            arc.dxf.color = 7
        logger.debug(f"Added arc at {center} with radius {radius}, angles {start_angle} to {end_angle} on layer '{layer}'")
    
    def _add_polyline(self, msp, params: dict, layer: str = 'Walls'):
        """Add a polyline entity to the modelspace"""
        points_data = params.get('points', [])
        if not points_data:
            logger.warning("No points provided for polyline")
            return
        
        points = []
        for point_data in points_data:
            if isinstance(point_data, dict):
                x = float(point_data.get('x', 0.0))
                y = float(point_data.get('y', 0.0))
                points.append((x, y))
            elif isinstance(point_data, (list, tuple)) and len(point_data) >= 2:
                points.append((float(point_data[0]), float(point_data[1])))
        
        if len(points) < 2:
            logger.warning(f"Insufficient points for polyline: {len(points)}")
            return
        
        close = params.get('close', False)
        polyline = msp.add_lwpolyline(points, close=close)
        # Set layer and properties
        polyline.dxf.layer = layer
        if layer in self.LAYERS:
            polyline.dxf.color = self.LAYERS[layer]['color']
        else:
            polyline.dxf.color = 7
        logger.debug(f"Added polyline with {len(points)} points, closed={close} on layer '{layer}'")
    
    def _add_dimension(self, msp, params: dict, layer: str = 'Dimensions'):
        """Add a dimension entity to the modelspace"""
        dim_type = params.get('type', 'linear').lower()
        
        if dim_type == 'linear':
            # Linear dimension
            # Try to get points from 'points' array or individual 'start'/'end'
            points = params.get('points', [])
            if points and len(points) >= 2:
                start = self._extract_point(params, 'points', (0.0, 0.0), index=0)
                end = self._extract_point(params, 'points', (100.0, 0.0), index=1)
            else:
                start = self._extract_point(params, 'start', (0.0, 0.0))
                end = self._extract_point(params, 'end', (100.0, 0.0))
            
            # Calculate dimension line position (offset from the dimension)
            dim_line = self._extract_point(params, 'dim_line', None)
            if dim_line is None:
                # Default: offset perpendicular to dimension
                mid_x = (start[0] + end[0]) / 2
                mid_y = (start[1] + end[1]) / 2
                # Offset by 50mm perpendicular
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = (dx**2 + dy**2)**0.5
                if length > 0:
                    perp_x = -dy / length * 50
                    perp_y = dx / length * 50
                    dim_line = (mid_x + perp_x, mid_y + perp_y)
                else:
                    dim_line = (mid_x, mid_y - 50)
            
            value = self._extract_number(params, 'value', 0.0)
            
            try:
                # Create dimension (returns DimStyleOverride, not Dimension entity directly)
                dim_override = msp.add_linear_dim(
                    base=dim_line,
                    p1=start,
                    p2=end,
                    dimstyle='STANDARD'
                )
                
                # Get the actual Dimension entity from the override
                # The override wraps the dimension entity
                dimension_entity = dim_override.dimension
                
                # Set layer on the DIMENSION entity itself
                # Dimensions in ezdxf have an associated anonymous block for visual representation
                # We need to set the layer on BOTH the dimension entity AND its geometry block
                try:
                    # Step 1: Set layer on the DIMENSION entity
                    dimension_entity.dxf.layer = layer
                    
                    # Step 2: Get the anonymous block containing the dimension's visual geometry
                    # and set the layer on all entities within that block
                    try:
                        # Access the block via the dimension entity
                        block_name = dimension_entity.dxf.geometry
                        if block_name and block_name in doc.blocks:
                            block = doc.blocks[block_name]
                            for entity in block:
                                try:
                                    entity.dxf.layer = layer
                                except (AttributeError, TypeError):
                                    # Some entities in the block might not support layer assignment
                                    pass
                    except (AttributeError, TypeError, KeyError):
                        # Alternative: try to get block via dimension's block reference
                        try:
                            # Dimensions store their geometry in an anonymous block
                            # The block name is typically stored in the dimension's geometry attribute
                            if hasattr(dimension_entity.dxf, 'geometry'):
                                block_ref = dimension_entity.dxf.geometry
                                # This might be a block name or handle - try to access it
                                pass
                        except:
                            pass
                    
                    # Set color based on layer
                    if layer in self.LAYERS:
                        dimension_entity.dxf.color = self.LAYERS[layer]['color']
                    else:
                        dimension_entity.dxf.color = 7
                        
                    logger.debug(f"Set dimension layer to '{layer}' including geometry block entities")
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error setting layer on dimension: {e}")
                
                # Set dimension text if provided using dimstyle overrides
                if value > 0:
                    try:
                        # Use dimstyle overrides to set text
                        overrides = dim.dimstyle.overrides
                        overrides['dimtext'] = str(value)
                    except:
                        # If overrides don't work, try setting text directly
                        try:
                            dim.dxf.text = str(value)
                        except:
                            pass
                
                logger.debug(f"Added linear dimension from {start} to {end} on layer '{layer}'")
            except Exception as e:
                logger.warning(f"Failed to add linear dimension: {e}")
                import traceback
                traceback.print_exc()
        elif dim_type == 'angular':
            # Angular dimension
            center = self._extract_point(params, 'center', (0.0, 0.0))
            start_angle = self._extract_number(params, 'start_angle', 0.0)
            end_angle = self._extract_number(params, 'end_angle', 90.0)
            radius = self._extract_number(params, 'radius', 10.0)
            
            try:
                dim = msp.add_angular_dim(
                    base=center,
                    line1=(start_angle, radius),
                    line2=(end_angle, radius),
                    dimstyle='STANDARD'
                )
                # Set layer and properties
                dim.dxf.layer = layer
                if layer in self.LAYERS:
                    dim.dxf.color = self.LAYERS[layer]['color']
                else:
                    dim.dxf.color = 7
                logger.debug(f"Added angular dimension at {center} on layer '{layer}'")
            except Exception as e:
                logger.warning(f"Failed to add angular dimension: {e}")
    
    def generate_dxf(
        self,
        instructions: List[ParsedInstruction],
        filename: Optional[str] = None
    ) -> bytes:
        """
        Generate DXF file from parsed CAD instructions
        
        Args:
            instructions: List of parsed CAD instructions
            filename: Optional filename for logging purposes
        
        Returns:
            bytes: DXF file content as bytes
        
        Raises:
            ValueError: If no valid instructions provided
            Exception: If DXF generation fails
        """
        if not instructions:
            raise ValueError("No instructions provided for DXF generation")
        
        # Create new DXF document
        doc = new(self.dxf_version, setup=True)
        doc.units = self.units
        
        # Set up layers with line weights
        self._setup_layers(doc)
        
        # Get modelspace
        msp = doc.modelspace()
        
        # Process each instruction
        processed_count = 0
        for idx, instruction in enumerate(instructions):
            try:
                command = instruction.command.lower()
                params = instruction.parameters
                
                # Infer layer for this entity
                layer = self._infer_layer(command, params, idx, instructions)
                
                if command == 'line':
                    self._add_line(msp, params, layer)
                    processed_count += 1
                elif command == 'circle':
                    self._add_circle(msp, params, layer)
                    processed_count += 1
                elif command == 'rectangle':
                    self._add_rectangle(msp, params, layer)
                    processed_count += 1
                elif command == 'arc':
                    self._add_arc(msp, params, layer)
                    processed_count += 1
                elif command in ['polyline', 'poly', 'lwpolyline']:
                    self._add_polyline(msp, params, layer)
                    processed_count += 1
                elif command == 'dimension':
                    self._add_dimension(msp, params, layer)
                    processed_count += 1
                else:
                    logger.warning(f"Unsupported command: {command}")
                    
            except Exception as e:
                logger.error(f"Error processing instruction {instruction.command}: {e}", exc_info=True)
                # Continue processing other instructions
                continue
        
        if processed_count == 0:
            raise ValueError("No valid instructions were processed")
        
        # Write DXF to bytes
        try:
            # ezdxf.write() expects a text stream, so we use TextIOWrapper
            output_stream = io.BytesIO()
            text_stream = io.TextIOWrapper(output_stream, encoding='utf-8', newline='')
            doc.write(text_stream)
            text_stream.flush()
            dxf_bytes = output_stream.getvalue()
            text_stream.close()
            output_stream.close()
            
            logger.info(f"Generated DXF file: {processed_count} entities processed, {len(dxf_bytes)} bytes")
            return dxf_bytes
            
        except Exception as e:
            logger.error(f"Failed to save DXF file: {e}", exc_info=True)
            raise
    
    def validate_dxf(self, dxf_bytes: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate DXF file format
        
        Args:
            dxf_bytes: DXF file content as bytes
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            from ezdxf import read
            # ezdxf.read() expects a text stream
            input_stream = io.BytesIO(dxf_bytes)
            text_stream = io.TextIOWrapper(input_stream, encoding='utf-8', newline='')
            doc = read(text_stream)
            text_stream.close()
            input_stream.close()
            
            # Basic validation checks
            if not doc:
                return False, "DXF document is empty"
            
            if not doc.modelspace():
                return False, "DXF document has no modelspace"
            
            return True, None
            
        except Exception as e:
            return False, f"DXF validation failed: {str(e)}"
    
    def is_configured(self) -> bool:
        """Check if service is properly configured"""
        try:
            # Test if ezdxf is available
            from ezdxf import new
            return True
        except ImportError:
            return False


# Global instance
try:
    dxf_generator_service = DXFGeneratorService()
except Exception as e:
    logger.error(f"Failed to initialize DXF generator service: {e}", exc_info=True)
    dxf_generator_service = None

