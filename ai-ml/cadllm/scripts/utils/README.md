# Utility Scripts

This folder contains utility scripts used by other parts of the project.

## Scripts

### `cadllm_client.py`
**Purpose**: Python client for Hugging Face Inference API

Provides a convenient interface for calling the CAD-LLM model via Hugging Face Inference API.

**Usage**:
```python
from cadllm_client import CADLLMClient

client = CADLLMClient(
    model_name="username/model-name",
    token="your_hf_token",
    endpoint_url=None  # Optional: custom endpoint
)

result = client.generate("Create a bedroom with bed and desk")
print(result)
```

**Features**:
- Qwen chat template format (matches training)
- System prompt integration
- Error handling
- Support for custom endpoints

**Used By**:
- `testing/test_hf_api.py` (for Inference API testing)

---

### `dsl_parser.py`
**Purpose**: Convert DSL format to DXF files

Parses the DSL (Domain-Specific Language) output from the model and converts it to DXF (Drawing Exchange Format) files for CAD applications.

**Usage**:
```python
from dsl_parser import parse_dsl_to_dxf

# DSL text from model output
dsl_text = """
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=3000 h=3000 center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
BED: rect w=1500 h=2000 center=(0,-500) layer=FURNITURE closed=true anchor_wall=south
"""

# Convert to DXF
dxf_file = parse_dsl_to_dxf(dsl_text, output_path="output.dxf")
```

**DSL Format Support**:
- `UNITS`: Measurement units (mm, cm, etc.)
- `ORIGIN_POLICY`: Origin positioning policy
- `ROOM`: Room definition (rectangles)
- `WALLS`: Wall perimeter definition
- `OBJECT_NAME`: Furniture/objects (rectangles and circles)
- Layers: `WALLS`, `FURNITURE`, `OBJECTS`
- Anchors: `north`, `south`, `east`, `west`, `none`

**Output**:
- DXF file with proper layers and entities
- Color-coded layers
- Line weights and styles

**Used By**:
- Space application (`deployment/space/cad-llm-api/app.py`)
- Any script that needs to convert DSL to DXF

**Example DSL Input**:
```
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=3000 h=3000 center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
BED: rect w=1500 h=2000 center=(0,-500) layer=FURNITURE closed=true anchor_wall=south
DESK: rect w=1200 h=600 center=(-1000,1200) layer=FURNITURE closed=true anchor_wall=north
```

**Example DXF Output**:
- DXF file with:
  - `WALLS` layer (red, thick lines)
  - `FURNITURE` layer (blue, medium lines)
  - `OBJECTS` layer (green, thin lines)
  - Proper entity definitions (rectangles, circles)

## Integration

These utilities are imported and used by:
- **Inference scripts**: For client API calls
- **Deployment scripts**: For Space application DXF conversion
- **Testing scripts**: For API client functionality

## Dependencies

- `ezdxf`: For DXF file creation
- `requests`: For HTTP API calls (in `cadllm_client.py`)

