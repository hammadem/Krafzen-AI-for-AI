# KRAFZEN AI Backend

FastAPI backend for voice/text to DXF generation using fine-tuned CAD-LLM model.

## Features

- **CAD-LLM Integration**: Uses fine-tuned CAD-LLM model for 2D CAD generation (recommended)
- **GPT-4 Fallback**: Uses GPT-4 for complex parsing when needed
- **Audio Transcription**: Whisper API for speech-to-text
- **DXF Generation**: Converts natural language to DXF files

## Setup

1. `pip install -r requirements.txt`
2. `cp env.example .env` → Fill in configuration:
   - Supabase keys (for database)
   - OpenAI API key (for Whisper transcription)
   - Hugging Face token and model (for CAD-LLM)
3. `./scripts/setup_supabase.sh` (pushes schema.sql)
4. `make run` → <http://localhost:8000/docs>

## Configuration

### Required Environment Variables

**Supabase** (for database):

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

**OpenAI** (for audio transcription):

- `OPENAI_API_KEY`

**Hugging Face** (for CAD-LLM model - recommended):

- `HF_TOKEN` - Your Hugging Face API token
- `HF_MODEL_NAME` - Model identifier (e.g., "username/cad-llm-krafzen")
- `HF_ENDPOINT_URL` - Optional: Custom endpoint URL (e.g., Hugging Face Space)
38:
39: **Api2Convert** (for professional DXF conversion):
- `API_2_CONVERT_KEY` - API Key from api2convert.com (V2)
- `API_2_CONVERT_URL` - API Endpoint (default: `https://api.api2convert.com/v2`)

See `env.example` for complete configuration options.

## API Endpoints

### CAD-LLM Endpoints (Recommended for 2D CAD)

- `POST /api/v1/dxf/generate-from-text-cadllm` - Generate DXF from text using CAD-LLM
- `POST /api/v1/dxf/generate-from-audio-cadllm` - Generate DXF from audio using CAD-LLM

These endpoints use the fine-tuned CAD-LLM model that outputs coordinates directly, which are then converted to DXF files. Faster and more cost-effective than GPT-4 for 2D CAD.

### GPT-4 Endpoints (Fallback for complex cases)

- `POST /api/v1/dxf/generate-from-text` - Generate DXF from text using GPT-4
- `POST /api/v1/dxf/generate-from-audio` - Generate DXF from audio using GPT-4

### Other Endpoints

- `POST /api/v1/dxf/generate` - Generate DXF from structured instructions
- `POST /api/v1/dxf/generate-from-json` - Generate DXF from JSON format
- `POST /api/v1/dxf/validate` - Validate DXF file format

## Development

- Tests: `make test` (100% coverage target)
- Deploy: Render via render.yaml

## Team

Kiruthika (Lead), Sonu (Frontend), Laxmi (Data), Ashwani (QA).
