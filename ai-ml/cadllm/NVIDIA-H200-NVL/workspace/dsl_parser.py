#!/usr/bin/env python3
"""
Parser to convert CAD-LLM DSL format to DXF file.

The model outputs DSL format:
  UNITS: mm
  ORIGIN_POLICY: room_center_at_(0,0)
  ROOM: rect w=WIDTH h=HEIGHT center=(0,0)
  WALLS: rect_perimeter closed=true layer=WALLS
  OBJECT_NAME: rect w=WIDTH h=HEIGHT center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL
  OBJECT_NAME: circle r=RADIUS center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL

This parser converts these to a DXF file using ezdxf.
"""

import re
import os
import tempfile
from typing import Optional, Dict, List, Tuple
from pathlib import Path

try:
    import ezdxf
    from ezdxf import units
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


class DSLParser:
    """Parser for CAD-LLM DSL format to DXF file."""
    
    # Regex patterns for parsing DSL format
    UNITS_PATTERN = re.compile(r'UNITS:\s*(\w+)', re.IGNORECASE)
    ORIGIN_POLICY_PATTERN = re.compile(r'ORIGIN_POLICY:\s*([^\n]+)', re.IGNORECASE)
    ROOM_PATTERN = re.compile(r'ROOM:\s*rect\s+w=([\d.]+)\s+h=([\d.]+)\s+center=\(([-\d.]+),\s*([-\d.]+)\)', re.IGNORECASE)
    WALLS_PATTERN = re.compile(r'WALLS:\s*rect_perimeter', re.IGNORECASE)
    RECT_PATTERN = re.compile(r'(\w+):\s*rect\s+w=([\d.]+)\s+h=([\d.]+)\s+center=\(([-\d.]+),\s*([-\d.]+)\)\s+layer=(\w+)', re.IGNORECASE)
    CIRCLE_PATTERN = re.compile(r'(\w+):\s*circle\s+r=([\d.]+)\s+center=\(([-\d.]+),\s*([-\d.]+)\)\s+layer=(\w+)', re.IGNORECASE)
    
    # Layer definitions with colors and line weights
    # Colors: 1=red, 2=yellow, 3=green, 4=cyan, 5=blue, 6=magenta, 7=white/black
    # Line weights in hundredths of mm: 13 (thin), 25 (medium), 50 (thick)
    LAYER_CONFIG = {
        'WALLS': {'color': 7, 'lineweight': 50},  # Thick line for walls
        'FIXTURES': {'color': 3, 'lineweight': 25},  # Green for fixtures
        'APPLIANCES': {'color': 1, 'lineweight': 25},  # Red for appliances
        'FURNITURE': {'color': 5, 'lineweight': 25},  # Blue for furniture
        'OPENINGS': {'color': 2, 'lineweight': 13},  # Yellow for openings (doors/windows)
        'OBJECTS': {'color': 7, 'lineweight': 25},  # Default for objects
    }
    
    def __init__(self):
        """Initialize the DSL parser."""
        self.units = units.MM  # Default to millimeters
        self.room_width = 0.0
        self.room_height = 0.0
        self.room_center = (0.0, 0.0)
    
    def parse(self, dsl_text: str, output_path: Optional[str] = None) -> str:
        """
        Parse DSL format and generate DXF file.
        
        Args:
            dsl_text: Raw model output in DSL format
            output_path: Optional path to save DXF file. If None, uses temp file.
            
        Returns:
            Path to the generated DXF file
        """
        if not EZDXF_AVAILABLE:
            raise ImportError(
                "ezdxf is required to generate DXF files. Install it with: pip install ezdxf"
            )
        
        # Clean the text
        dsl_text = dsl_text.strip()
        
        # Create DXF document
        doc = ezdxf.new('R2010', units=self.units)
        msp = doc.modelspace()
        
        # Parse DSL lines
        lines = [line.strip() for line in dsl_text.split('\n') if line.strip()]
        
        # Parse units
        units_value = None
        for line in lines:
            match = self.UNITS_PATTERN.match(line)
            if match:
                units_value = match.group(1).lower()
                if units_value == 'mm':
                    self.units = units.MM
                elif units_value == 'cm':
                    self.units = units.CM
                elif units_value in ['m', 'meter', 'meters']:
                    self.units = units.M
                break
        
        # Parse room dimensions
        for line in lines:
            match = self.ROOM_PATTERN.match(line)
            if match:
                self.room_width = float(match.group(1))
                self.room_height = float(match.group(2))
                self.room_center = (float(match.group(3)), float(match.group(4)))
                break
        
        # Create layers
        self._create_layers(doc)
        
        # Parse and add walls (room perimeter)
        walls_added = False
        for line in lines:
            if self.WALLS_PATTERN.search(line):
                self._add_walls(msp)
                walls_added = True
                break
        
        # If walls not explicitly defined but room is, add walls anyway
        if not walls_added and self.room_width > 0 and self.room_height > 0:
            self._add_walls(msp)
        
        # Parse and add rectangles
        for line in lines:
            match = self.RECT_PATTERN.match(line)
            if match:
                name = match.group(1)
                width = float(match.group(2))
                height = float(match.group(3))
                center_x = float(match.group(4))
                center_y = float(match.group(5))
                layer = match.group(6)
                self._add_rectangle(msp, name, width, height, (center_x, center_y), layer)
        
        # Parse and add circles
        for line in lines:
            match = self.CIRCLE_PATTERN.match(line)
            if match:
                name = match.group(1)
                radius = float(match.group(2))
                center_x = float(match.group(3))
                center_y = float(match.group(4))
                layer = match.group(5)
                self._add_circle(msp, name, radius, (center_x, center_y), layer)
        
        # Save DXF file
        if output_path is None:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"cad_dsl_{os.getpid()}.dxf")
        
        doc.saveas(output_path)
        return output_path
    
    def _create_layers(self, doc: 'ezdxf.Document'):
        """Create DXF layers with appropriate colors and line weights."""
        for layer_name, config in self.LAYER_CONFIG.items():
            layer = doc.layers.add(layer_name)
            layer.color = config['color']
            layer.lineweight = config['lineweight']
    
    def _add_walls(self, msp: 'ezdxf.ModelSpace'):
        """Add room walls as a rectangle perimeter."""
        if self.room_width <= 0 or self.room_height <= 0:
            return
        
        # Calculate room corners (room is centered at room_center)
        half_width = self.room_width / 2.0
        half_height = self.room_height / 2.0
        
        # Calculate corners relative to room center
        bottom_left = (self.room_center[0] - half_width, self.room_center[1] - half_height)
        bottom_right = (self.room_center[0] + half_width, self.room_center[1] - half_height)
        top_right = (self.room_center[0] + half_width, self.room_center[1] + half_height)
        top_left = (self.room_center[0] - half_width, self.room_center[1] + half_height)
        
        # Create closed polyline for walls
        points = [bottom_left, bottom_right, top_right, top_left]
        polyline = msp.add_lwpolyline(points, close=True)
        polyline.dxf.layer = 'WALLS'
        if 'WALLS' in self.LAYER_CONFIG:
            polyline.dxf.color = self.LAYER_CONFIG['WALLS']['color']
    
    def _add_rectangle(self, msp: 'ezdxf.ModelSpace', name: str, width: float, 
                      height: float, center: Tuple[float, float], layer: str):
        """Add a rectangle entity to the modelspace."""
        # Calculate rectangle corners from center
        half_width = width / 2.0
        half_height = height / 2.0
        
        bottom_left = (center[0] - half_width, center[1] - half_height)
        bottom_right = (center[0] + half_width, center[1] - half_height)
        top_right = (center[0] + half_width, center[1] + half_height)
        top_left = (center[0] - half_width, center[1] + half_height)
        
        # Create closed polyline
        points = [bottom_left, bottom_right, top_right, top_left]
        polyline = msp.add_lwpolyline(points, close=True)
        
        # Set layer
        layer_name = layer.upper()
        if layer_name not in self.LAYER_CONFIG:
            layer_name = 'OBJECTS'  # Default layer
        
        polyline.dxf.layer = layer_name
        if layer_name in self.LAYER_CONFIG:
            polyline.dxf.color = self.LAYER_CONFIG[layer_name]['color']
    
    def _add_circle(self, msp: 'ezdxf.ModelSpace', name: str, radius: float,
                   center: Tuple[float, float], layer: str):
        """Add a circle entity to the modelspace."""
        if radius <= 0:
            return
        
        circle = msp.add_circle(center=center, radius=radius)
        
        # Set layer
        layer_name = layer.upper()
        if layer_name not in self.LAYER_CONFIG:
            layer_name = 'OBJECTS'  # Default layer
        
        circle.dxf.layer = layer_name
        if layer_name in self.LAYER_CONFIG:
            circle.dxf.color = self.LAYER_CONFIG[layer_name]['color']


def parse_dsl_to_dxf(dsl_text: str, output_path: Optional[str] = None) -> str:
    """
    Convenience function to parse DSL format to DXF file.
    
    Args:
        dsl_text: Raw model output in DSL format
        output_path: Optional path to save DXF file. If None, uses temp file.
        
    Returns:
        Path to the generated DXF file
    """
    parser = DSLParser()
    return parser.parse(dsl_text, output_path)


if __name__ == "__main__":
    # Test the parser
    test_dsl = """UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=4000 h=3000 center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
SINK: rect w=600 h=500 center=(0,1400) layer=FIXTURES closed=true anchor_wall=north
COOKTOP: rect w=800 h=800 center=(-1600,0) layer=APPLIANCES closed=true anchor_wall=west
BURNER_1: circle r=100 center=(-1600,0) layer=APPLIANCES closed=true anchor_wall=west subfeature_of=COOKTOP
FRIDGE: rect w=700 h=1800 center=(1600,0) layer=APPLIANCES closed=true anchor_wall=east"""
    
    parser = DSLParser()
    result = parser.parse(test_dsl)
    print(f"✅ DXF file generated at: {result}")

