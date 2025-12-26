"""
Parser to convert CAD-LLM coordinate format to DXF file.

The model outputs coordinates in this format:
- <SOL> - Start of object
- <Circle>: x=176, y=128, r=48 - Circle with center and radius
- <Line>: x=223, y=128 - Line coordinates (multiple lines form a polyline)
- <Arc>: x=142, y=114, α=64, f=1 - Arc with center, angle, and flag
- <EOS> - End of sequence

This parser converts these to a DXF file directly.
"""

import re
import os
import tempfile
from typing import List, Dict, Tuple, Optional
from pathlib import Path

try:
    import ezdxf
    from ezdxf import units
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


class CoordinateParser:
    """Parser for CAD-LLM coordinate format to ezdxf code."""
    
    def __init__(self):
        # Patterns for parsing different primitives
        self.circle_pattern = re.compile(r'<Circle>:\s*x=([\d.]+),\s*y=([\d.]+),\s*r=([\d.]+)')
        self.line_pattern = re.compile(r'<Line>:\s*x=([\d.]+),\s*y=([\d.]+)')
        self.arc_pattern = re.compile(r'<Arc>:\s*x=([\d.]+),\s*y=([\d.]+),\s*α=([\d.]+),\s*f=([\d.]+)')
        self.sol_pattern = re.compile(r'<SOL>')
        self.eos_pattern = re.compile(r'<EOS>')
    
    def parse(self, text: str, output_path: Optional[str] = None, center_at_origin: bool = True) -> str:
        """
        Parse coordinate format and generate DXF file.
        
        Args:
            text: Raw model output in coordinate format
            output_path: Optional path to save DXF file. If None, uses temp file.
            center_at_origin: If True, transform coordinates to center at origin (0, 0)
            
        Returns:
            Path to the generated DXF file
        """
        if not EZDXF_AVAILABLE:
            raise ImportError(
                "ezdxf is required to generate DXF files. Install it with: pip install ezdxf"
            )
        
        # Clean the text
        text = text.strip()
        
        # Split by <SOL> to get separate objects
        objects = re.split(r'<SOL>', text)
        objects = [obj.strip() for obj in objects if obj.strip()]
        
        # Create DXF document
        doc = ezdxf.new('R2010', units=units.MM)
        msp = doc.modelspace()
        
        if not objects:
            # Empty DXF file
            pass
        else:
            # First pass: collect all coordinates to calculate bounding box for centering
            all_coords = []
            for obj in objects:
                obj_clean = re.sub(r'<EOS>', '', obj).strip()
                if not obj_clean:
                    continue
                
                # Extract all coordinates
                for match in self.circle_pattern.finditer(obj_clean):
                    x, y, r = float(match.group(1)), float(match.group(2)), float(match.group(3))
                    all_coords.append((x - r, y - r))  # Circle bottom-left
                    all_coords.append((x + r, y + r))  # Circle top-right
                
                for match in self.line_pattern.finditer(obj_clean):
                    x, y = float(match.group(1)), float(match.group(2))
                    all_coords.append((x, y))
                
                for match in self.arc_pattern.finditer(obj_clean):
                    x, y = float(match.group(1)), float(match.group(2))
                    all_coords.append((x, y))
            
            # Calculate offset to center at origin
            offset_x, offset_y = 0.0, 0.0
            if center_at_origin and all_coords:
                min_x = min(c[0] for c in all_coords)
                max_x = max(c[0] for c in all_coords)
                min_y = min(c[1] for c in all_coords)
                max_y = max(c[1] for c in all_coords)
                # Center offset
                offset_x = -(min_x + max_x) / 2.0
                offset_y = -(min_y + max_y) / 2.0
            
            # Parse each object and add to DXF
            for i, obj in enumerate(objects):
                # Remove <EOS> if present
                obj = re.sub(r'<EOS>', '', obj).strip()
                if not obj:
                    continue
                
                # Parse and add to DXF with offset
                self._add_object_to_dxf(msp, obj, i, offset_x, offset_y)
        
        # Save DXF file
        if output_path is None:
            # Use temporary file
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"cad_output_{os.getpid()}.dxf")
        
        doc.saveas(output_path)
        return output_path
    
    def _add_object_to_dxf(self, msp, obj_text: str, obj_index: int, offset_x: float = 0.0, offset_y: float = 0.0):
        """Parse a single object and add it to the DXF modelspace with optional offset."""
        # Collect all primitives in this object
        circles = []
        lines_coords = []
        arcs = []
        
        # Extract circles
        for match in self.circle_pattern.finditer(obj_text):
            x, y, r = float(match.group(1)), float(match.group(2)), float(match.group(3))
            circles.append((x + offset_x, y + offset_y, r))
        
        # Extract lines (form a polyline)
        for match in self.line_pattern.finditer(obj_text):
            x, y = float(match.group(1)), float(match.group(2))
            lines_coords.append((x + offset_x, y + offset_y))
        
        # Extract arcs
        for match in self.arc_pattern.finditer(obj_text):
            x, y, alpha, flag = float(match.group(1)), float(match.group(2)), float(match.group(3)), float(match.group(4))
            arcs.append((x + offset_x, y + offset_y, alpha, flag))
        
        # Add circles to DXF
        for x, y, r in circles:
            msp.add_circle(center=(x, y), radius=r)
        
        # Add polylines (lines) to DXF
        if lines_coords:
            msp.add_lwpolyline(lines_coords)
        
        # Add arcs to DXF
        # Note: Arc format may need adjustment based on actual requirements
        # For now, we'll create a simple arc representation
        for x, y, alpha, flag in arcs:
            # Convert angle from degrees to radians
            import math
            angle_rad = math.radians(alpha)
            # Create a simple arc (this is a basic implementation)
            # You may need to adjust based on your arc format requirements
            start_angle = 0
            end_angle = angle_rad
            radius = 10  # Default radius, adjust as needed
            msp.add_arc(center=(x, y), radius=radius, start_angle=math.degrees(start_angle), end_angle=math.degrees(end_angle))


def parse_coordinates_to_dxf(text: str, output_path: Optional[str] = None, center_at_origin: bool = True) -> str:
    """
    Convenience function to parse coordinate format to DXF file.
    
    Args:
        text: Raw model output in coordinate format
        output_path: Optional path to save DXF file. If None, uses temp file.
        center_at_origin: If True, transform coordinates to center at origin (0, 0)
        
    Returns:
        Path to the generated DXF file
    """
    parser = CoordinateParser()
    return parser.parse(text, output_path, center_at_origin)


# Backward compatibility alias
def parse_coordinates_to_ezdxf(text: str) -> str:
    """
    Legacy function name - now generates DXF file directly.
    Returns the path to the generated DXF file.
    """
    return parse_coordinates_to_dxf(text)


if __name__ == "__main__":
    # Test the parser
    test_input = """<SOL>
<Line>: x=223, y=128
<Line>: x=223, y=192
<Line>: x=128, y=192
<Line>: x=128, y=128
<EOS>"""
    
    parser = CoordinateParser()
    result = parser.parse(test_input)
    print(f"DXF file generated at: {result}")

