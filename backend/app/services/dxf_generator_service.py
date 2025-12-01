"""
DXF Generator Service for converting CAD instructions to DXF files using ezdxf
"""

import io
import logging
from typing import List, Optional, Tuple
from ezdxf import new, units
from app.schemas.parser import ParsedInstruction, CADFileType

logger = logging.getLogger(__name__)


class DXFGeneratorService:
    """Service for generating DXF files from parsed CAD instructions"""
    
    def __init__(self):
        """Initialize DXF generator service"""
        self.dxf_version = 'R2010'  # DXF version (R2010 is widely compatible)
        self.units = units.MM  # Use millimeters as default unit
        
    def _extract_point(self, params: dict, key: str, default: Tuple[float, float] = (0.0, 0.0)) -> Tuple[float, float]:
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
    
    def _add_line(self, msp, params: dict):
        """Add a line entity to the modelspace"""
        start = self._extract_point(params, 'start', (0.0, 0.0))
        end = self._extract_point(params, 'end', (100.0, 100.0))
        
        msp.add_line(start, end)
        logger.debug(f"Added line from {start} to {end}")
    
    def _add_circle(self, msp, params: dict):
        """Add a circle entity to the modelspace"""
        center = self._extract_point(params, 'center', (0.0, 0.0))
        radius = self._extract_number(params, 'radius', 10.0)
        
        if radius <= 0:
            logger.warning(f"Invalid radius {radius}, using default 10.0")
            radius = 10.0
        
        msp.add_circle(center, radius)
        logger.debug(f"Added circle at {center} with radius {radius}")
    
    def _add_rectangle(self, msp, params: dict):
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
        
        msp.add_lwpolyline(points, close=True)
        logger.debug(f"Added rectangle at {corner} with size {width}x{height}")
    
    def _add_arc(self, msp, params: dict):
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
        msp.add_arc(center, radius, start_angle, end_angle)
        logger.debug(f"Added arc at {center} with radius {radius}, angles {start_angle} to {end_angle}")
    
    def _add_polyline(self, msp, params: dict):
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
        msp.add_lwpolyline(points, close=close)
        logger.debug(f"Added polyline with {len(points)} points, closed={close}")
    
    def _add_dimension(self, msp, params: dict):
        """Add a dimension entity to the modelspace"""
        dim_type = params.get('type', 'linear').lower()
        
        if dim_type == 'linear':
            # Linear dimension
            start = self._extract_point(params, 'start', (0.0, 0.0))
            end = self._extract_point(params, 'end', (100.0, 0.0))
            dim_line = self._extract_point(params, 'dim_line', (50.0, -10.0))
            value = self._extract_number(params, 'value', 0.0)
            
            try:
                msp.add_linear_dim(
                    base=dim_line,
                    p1=start,
                    p2=end,
                    dimstyle='STANDARD',
                    text=value if value > 0 else None
                )
                logger.debug(f"Added linear dimension from {start} to {end}")
            except Exception as e:
                logger.warning(f"Failed to add linear dimension: {e}")
        elif dim_type == 'angular':
            # Angular dimension
            center = self._extract_point(params, 'center', (0.0, 0.0))
            start_angle = self._extract_number(params, 'start_angle', 0.0)
            end_angle = self._extract_number(params, 'end_angle', 90.0)
            radius = self._extract_number(params, 'radius', 10.0)
            
            try:
                msp.add_angular_dim(
                    base=center,
                    line1=(start_angle, radius),
                    line2=(end_angle, radius),
                    dimstyle='STANDARD'
                )
                logger.debug(f"Added angular dimension at {center}")
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
        
        # Get modelspace
        msp = doc.modelspace()
        
        # Process each instruction
        processed_count = 0
        for instruction in instructions:
            try:
                command = instruction.command.lower()
                params = instruction.parameters
                
                if command == 'line':
                    self._add_line(msp, params)
                    processed_count += 1
                elif command == 'circle':
                    self._add_circle(msp, params)
                    processed_count += 1
                elif command == 'rectangle':
                    self._add_rectangle(msp, params)
                    processed_count += 1
                elif command == 'arc':
                    self._add_arc(msp, params)
                    processed_count += 1
                elif command in ['polyline', 'poly']:
                    self._add_polyline(msp, params)
                    processed_count += 1
                elif command == 'dimension':
                    self._add_dimension(msp, params)
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

