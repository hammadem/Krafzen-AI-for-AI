import ezdxf
import os
import uuid
from typing import Dict, Any

class DxfService:
    def __init__(self, output_dir: str = "temp"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate_dxf(self, data: Dict[str, Any]) -> str:
        """
        Generates a DXF file from the provided JSON data.
        Returns the absolute path to the generated file.
        """
        # Create a new DXF document
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # Define Layers
        doc.layers.new(name="WALLS", dxfattribs={"color": 7}) # White/Black
        doc.layers.new(name="FURNITURE", dxfattribs={"color": 4}) # Cyan
        doc.layers.new(name="TEXT", dxfattribs={"color": 2}) # Yellow

        # Metadata extraction for coordinate conversion
        metadata = data.get("metadata", {})
        
        # Normalized Grid System
        GRID_SIZE = 1000.0
        
        # Scale Factor: Convert 0-1000 units to mm
        # Default fallback: If metadata is missing, assume 1 unit = 10mm (1000 units = 10m room)
        mm_per_unit = float(metadata.get("scale_factor_mm_per_unit", 10.0))
        
        def transform_point(p):
            if not p or len(p) < 2: return (0,0)
            x, y = p[0], p[1]
            # Flip Y (using 1000 grid), then Scale to mm
            return (x * mm_per_unit, (GRID_SIZE - y) * mm_per_unit)

        # 1. Draw Walls
        walls = data.get("walls", [])
        for wall in walls:
            start = transform_point(wall.get("start"))
            end = transform_point(wall.get("end"))
            if start and end:
                msp.add_line(start, end, dxfattribs={"layer": "WALLS"})

        # Define Dimension Style
        if "KRAFZEN_DIM" not in doc.dimstyles:
            dimstyle = doc.dimstyles.new("KRAFZEN_DIM")
            dimstyle.dxf.dimtxt = 60.0   # Text height (Much smaller)
            dimstyle.dxf.dimasz = 50.0   # Arrow size
            dimstyle.dxf.dimgap = 20.0   # Gap
            dimstyle.dxf.dimscale = 1.0  # Scale factor
            dimstyle.dxf.dimdec = 0      # Precision
            dimstyle.dxf.dimtih = 0      # Text inside horizontal
            dimstyle.dxf.dimtoh = 0      # Text outside horizontal
            dimstyle.dxf.dimtad = 1      # Text Place Above Dim Line
            dimstyle.dxf.dimclrt = 2     # Text Color = Yellow (Visibility Fix)
            dimstyle.dxf.dimclrd = 3     # Dim Line Color = Green
            dimstyle.dxf.dimclre = 3     # Extension Line Color = Green

        doc.layers.new(name="DIMENSIONS", dxfattribs={"color": 3}) # Green

        # 2. Draw Furniture
        furniture_items = data.get("furniture", [])
        for item in furniture_items:
            raw_center = item.get("center", [0, 0])
            center = transform_point(raw_center)
            
            # Scale dimensions
            width = item.get("width", 100) * mm_per_unit
            depth = item.get("depth", 100) * mm_per_unit
            rotation = item.get("rotation_degrees", 0)
            name = item.get("name", "Unknown")

            # Create block or Polyline
            # For rotated rectangles, we calculate corners relative to 0,0 then rotate, then translate
            w2 = width / 2
            d2 = depth / 2
            
            # Local coordinates (Clockwise)
            local_points = [
                (-w2, d2), (w2, d2), (w2, -d2), (-w2, -d2), (-w2, d2)
            ]
            
            import math
            rad = math.radians(rotation)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)
            
            world_points = []
            for lx, ly in local_points:
                # Rotate
                rx = lx * cos_a - ly * sin_a
                ry = lx * sin_a + ly * cos_a
                # Translate to Center
                world_points.append((center[0] + rx, center[1] + ry))
            
            # Draw Geometry
            msp.add_lwpolyline(world_points, dxfattribs={"layer": "FURNITURE"})
            
            # Add Dimensions (Width and Depth) with Explicit Text
            # P0 is Top-Left, P1 is Top-Right (Width)
            p0 = world_points[0]
            p1 = world_points[1]
            p3 = world_points[3] # Bottom-Left (Depth)
            
            # Width Dimension (Top)
            msp.add_aligned_dim(
                p1=p0, p2=p1, distance=100,
                dxfattribs={"layer": "DIMENSIONS", "dimstyle": "KRAFZEN_DIM"},
                text=f"{int(width)} mm" # Explicit Value
            ).render()
            
            # Depth Dimension (Left)
            msp.add_aligned_dim(
                p1=p3, p2=p0, distance=100,
                dxfattribs={"layer": "DIMENSIONS", "dimstyle": "KRAFZEN_DIM"},
                text=f"{int(depth)} mm" # Explicit Value
            ).render()

            # Add Name Label
            # Text Height: reduced to 40.0
            text_height = 40.0 
            
            text_name = msp.add_text(
                name, 
                dxfattribs={
                    "layer": "TEXT", 
                    "height": text_height
                }
            )
            text_name.set_placement(center, align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)
            text_name.dxf.rotation = rotation
            
            # Add Coordinate Label (Below Name)
            coord_str = f"({int(center[0])}, {int(center[1])})"
            text_coords = msp.add_text(
                coord_str,
                dxfattribs={
                    "layer": "TEXT", 
                    "height": text_height * 0.8 # Slightly smaller
                }
            )
            # Offset center slightly down for the second line
            # Need to rotate the offset vector if the object is rotated
            # Simple approximation: align TOP_CENTER at the same center point
            text_coords.set_placement(center, align=ezdxf.enums.TextEntityAlignment.TOP_CENTER)
            text_coords.dxf.rotation = rotation

        # 3. Text Annotations
        annotations = data.get("text_annotations", [])
        for note in annotations:
            text_str = note.get("text", "")
            pos = transform_point(note.get("position", [0, 0]))
            if text_str:
                msp.add_text(
                    text_str,
                    dxfattribs={"layer": "TEXT", "height": 80} # Reduced from 150
                ).set_placement(pos)

        # Save File
        filename = f"plan_{uuid.uuid4().hex}.dxf"
        filepath = os.path.join(self.output_dir, filename)
        doc.saveas(filepath)
        
        return filepath
