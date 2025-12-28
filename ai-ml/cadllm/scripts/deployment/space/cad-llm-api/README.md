---
title: CAD-LLM API
emoji: 🔧
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: apache-2.0
app_port: 7860
---

# CAD-LLM API Space

FastAPI server for the CAD-LLM model that generates structured DSL (Domain-Specific Language) format from natural language CAD descriptions. The DSL output can be converted to DXF files using the `dsl_parser.py` script.

## API Endpoints

### POST `/generate`

Generate CAD DSL format from a natural language instruction.

**Request:**
```json
{
  "instruction": "Create a circle with radius 10mm centered at origin",
  "max_new_tokens": 400,
  "temperature": 0.7,
  "top_p": 0.9
}
```

**Response:**
```json
{
  "output": "UNITS: mm\nORIGIN_POLICY: room_center_at_(0,0)\nROOM: rect w=3000 h=3000 center=(0,0)\nWALLS: rect_perimeter closed=true layer=WALLS\nCIRCLE: circle r=10 center=(0,0) layer=OBJECTS closed=true anchor_wall=none",
  "model": "mkmad7/cad-llm-krafzen",
  "device": "cuda"
}
```

**Output Format:**
The model generates structured DSL format:
- `UNITS: mm` - Measurement units
- `ORIGIN_POLICY: room_center_at_(0,0)` - Coordinate system policy
- `ROOM: rect w=WIDTH h=HEIGHT center=(0,0)` - Room dimensions
- `WALLS: rect_perimeter closed=true layer=WALLS` - Wall perimeter
- `OBJECT_NAME: rect w=WIDTH h=HEIGHT center=(X,Y) layer=LAYER closed=true anchor_wall=WALL` - Rectangular objects
- `OBJECT_NAME: circle r=RADIUS center=(X,Y) layer=LAYER closed=true anchor_wall=WALL` - Circular objects

The DSL output can be converted to DXF files using the `dsl_parser.py` script from the CAD-LLM repository.

### GET `/health`

Check API health and model status.

### GET `/`

Root endpoint with basic info.

## Environment Variables

- `HF_MODEL_NAME`: Model identifier (default: `mkmad7/cad-llm-krafzen`)
- `HF_TOKEN`: Hugging Face token (required for private models)
- `PORT`: Server port (default: 8000)

## Usage

The API is automatically available at the Space URL. You can test it with:

```bash
curl -X POST "https://your-space.hf.space/generate" \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Create a circle with radius 10mm centered at origin"}'
```

**Example Response:**
```
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=3000 h=3000 center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
CIRCLE: circle r=10 center=(0,0) layer=OBJECTS closed=true anchor_wall=none
```

## Converting DSL to DXF

The DSL output can be converted to DXF files using the `dsl_parser.py` script:

```python
from dsl_parser import DSLParser

parser = DSLParser()
dxf_path = parser.parse(dsl_output, output_path="output.dxf")
```

See the [CAD-LLM repository](https://github.com/KRAFZEN/KRAFZEN-AI-) for the full parser implementation.

