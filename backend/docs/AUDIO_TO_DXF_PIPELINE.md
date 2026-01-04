# Audio to DXF Pipeline Documentation

## Overview
This document explains the different pipeline options available for converting audio recordings to DXF files.

## Pipeline Options

### Option 1: Direct Pipeline (Audio → Text → DXF)
**Recommended for:** Simple, quick conversions

```
Audio File
    ↓
[Whisper Service] → Transcribe audio to text
    ↓
[GPT Parser Service] → Parse text directly to CAD instructions
    ↓
[DXF Generator Service] → Generate DXF file
    ↓
DXF File Output
```

**Services Used:**
- `whisper_service` - Audio transcription (OpenAI Whisper)
- `gpt_parser_service` - Natural language to CAD instructions (GPT-4)
- `dxf_generator_service` - CAD instructions to DXF (ezdxf)

**Test Script:** `backend/tests/integration/test_audio_to_dxf.py`

**Pros:**
- Faster (fewer steps)
- Simpler workflow
- Good for straightforward instructions

**Cons:**
- Less precise for complex designs
- GPT parser may miss details or combine elements
- Harder to validate intermediate steps

---

### Option 2: JSON Pipeline (Audio → Text → JSON → DXF) ⭐ DEFAULT & RECOMMENDED
**Recommended for:** All use cases - provides best accuracy and precision

```
Audio File
    ↓
[Whisper Service] → Transcribe audio to text
    ↓
[Text to JSON Converter] → Convert text to structured JSON format
    ↓
[JSON Instruction Parser] → Parse JSON to CAD instructions
    ↓
[DXF Generator Service] → Generate DXF file
    ↓
DXF File Output
```

**Services Used:**
- `whisper_service` - Audio transcription (OpenAI Whisper)
- `text_to_json_converter` - Text to structured JSON (GPT-4)
- `json_instruction_parser` - JSON to CAD instructions (Custom parser)
- `dxf_generator_service` - CAD instructions to DXF (ezdxf)

**Test Script:** `backend/tests/integration/test_audio_to_json_to_dxf.py`

**Pros:**
- More accurate and precise
- Structured JSON format is machine-readable
- Easier to validate and debug
- Better for complex designs with many elements
- JSON can be edited manually if needed

**Cons:**
- Slightly slower (one extra step)
- Requires more detailed input text

---

## API Endpoints

### 1. Audio Transcription
**Endpoint:** `POST /api/v1/transcribe/audio`

Transcribes audio file to text using Whisper.

**Request:**
- File upload (mp3, wav, m4a, ogg, flac, webm)

**Response:**
```json
{
  "text": "Draw a 12 x 10 kitchen with a door on the right",
  "language": "en",
  "duration": 10.63
}
```

### 2. Audio to DXF (Unified Endpoint) ⭐ NEW & RECOMMENDED
**Endpoint:** `POST /api/v1/dxf/generate-from-audio`

Generates DXF directly from audio file using JSON pipeline (Option 2).

**Request:**
- File upload (mp3, wav, m4a, ogg, flac, webm)
- Query params:
  - `language` (optional, default: "en")
  - `units` (optional, default: "inches")

**Response:** Binary DXF file download

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/dxf/generate-from-audio?language=en&units=inches" \
  -F "file=@recording.mp3"
```

### 3. Text to DXF (Default: JSON Pipeline)
**Endpoint:** `POST /api/v1/dxf/generate-from-text`

Generates DXF from text. **Defaults to JSON pipeline (Option 2)** for better accuracy.

**Request:**
```json
{
  "text": "Draw a 12 x 10 kitchen with a door on the right",
  "file_type": "dxf"
}
```

**Query Parameters:**
- `use_json_pipeline` (optional, default: `true`) - Set to `false` to use direct parsing (Option 1)

**Response:** Binary DXF file download

**Note:** By default, this endpoint uses the JSON pipeline (Option 2). Set `use_json_pipeline=false` to use the direct pipeline (Option 1).

### 4. Text to DXF (via JSON) - Legacy
**Endpoint:** `POST /api/v1/dxf/generate-from-text-via-json`

Legacy endpoint. Use `/generate-from-text` instead (which defaults to JSON pipeline).

### 5. JSON to DXF
**Endpoint:** `POST /api/v1/dxf/generate-from-json`

Generates DXF directly from structured JSON format.

**Request:**
```json
{
  "units": "inches",
  "format": "DXF",
  "entities": {
    "room_boundary": {
      "type": "lwpolyline",
      "points": [[0, 0], [144, 0], [144, 120], [0, 120], [0, 0]]
    },
    "door": {
      "opening_line": {
        "type": "line",
        "start": [144, 20],
        "end": [144, 56]
      }
    }
  }
}
```

**Response:** Binary DXF file download

---

## Complete Workflow Examples

### Example 1: Using Direct Pipeline

```python
# Step 1: Transcribe audio
transcribed_text, language, duration = await whisper_service.transcribe_file(
    file_content=audio_bytes,
    filename="recording.mp3"
)

# Step 2: Parse to CAD instructions
instructions, _ = await gpt_parser_service.parse_text(
    text=transcribed_text,
    file_type=CADFileType.DXF
)

# Step 3: Generate DXF
dxf_bytes = dxf_generator_service.generate_dxf(
    instructions=instructions,
    filename="output.dxf"
)
```

### Example 2: Using JSON Pipeline (Recommended)

```python
# Step 1: Transcribe audio
transcribed_text, language, duration = await whisper_service.transcribe_file(
    file_content=audio_bytes,
    filename="recording.mp3"
)

# Step 2: Convert text to JSON
json_data = await text_to_json_converter.convert_text_to_json(
    text=transcribed_text,
    units="inches"
)

# Step 3: Parse JSON to CAD instructions
instructions = json_instruction_parser.parse_json(json_data)

# Step 4: Generate DXF
dxf_bytes = dxf_generator_service.generate_dxf(
    instructions=instructions,
    filename="output.dxf"
)
```

---

## When to Use Which Pipeline?

### Use JSON Pipeline (Option 2) - DEFAULT ⭐
**Use for all cases** - This is now the default pipeline:
- All production use cases
- Complex designs with many elements
- Need for precision and accuracy
- Professional CAD drawings
- Multiple layers and line weights
- Detailed measurements and coordinates
- Simple designs (works great for these too!)

### Use Direct Pipeline (Option 1) when:
- Quick testing of parser functionality
- Legacy compatibility
- Minimal detail requirements
- Set `use_json_pipeline=false` in `/generate-from-text` endpoint

---

## Testing

### Test Direct Pipeline:
```bash
cd backend
python tests/integration/test_audio_to_dxf.py /path/to/audio.mp3
```

### Test JSON Pipeline:
```bash
cd backend
python tests/integration/test_audio_to_json_to_dxf.py /path/to/audio.mp3
```

---

## Output Files

Both pipelines save DXF files to:
- Location: `backend/test_output/`
- Naming:
  - Direct: `{audio_filename}.dxf`
  - JSON: `{audio_filename}_json.dxf`

---

## Layer Support

Both pipelines support the following layers with appropriate line weights:

- **Walls** - Thick line (0.50mm) - Structural elements
- **Fixtures** - Medium line (0.25mm) - Furniture, cabinets
- **Equipment** - Medium line (0.25mm) - Appliances, machinery
- **Openings** - Thin line (0.13mm) - Doors, windows
- **Dimensions** - Thin line (0.13mm) - Dimension lines
- **Annotations** - Thin line (0.13mm) - Text, labels

---

## Troubleshooting

### Issue: Low quality output
**Solution:** Use JSON pipeline (Option 2) for better accuracy

### Issue: Missing elements in DXF
**Solution:** 
- Provide more detailed audio/text input
- Use JSON pipeline which is more thorough
- Check transcription quality

### Issue: Incorrect coordinates
**Solution:**
- Use JSON pipeline with explicit coordinate specification
- Provide measurements in consistent units
- Verify JSON structure before DXF generation

---

## Future Enhancements

- [ ] Audio preprocessing for better transcription
- [ ] Multi-language support
- [ ] Real-time audio streaming
- [ ] Interactive JSON editing interface
- [ ] Batch audio processing
- [ ] Quality scoring for generated DXF files

