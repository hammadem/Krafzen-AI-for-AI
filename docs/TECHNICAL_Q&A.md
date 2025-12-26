# Technical Q&A - KRAFZEN AI Implementation

## Overview
This document addresses potential technical follow-up questions about the Weeks 1-2 and Weeks 3-4 implementation of KRAFZEN AI.

---

## Deployment & Infrastructure

### Q1: How does the GitHub Actions CI/CD pipeline work for both frontend and backend?

**A:** The pipeline uses separate workflows:
- **Backend (Render)**: `deploy-backend.yml` runs tests, then deploys to staging/production based on branch
- **Frontend (Vercel)**: `staging-frontend.yaml` runs lint, tests, build, then deploys via Vercel Action
- Both use branch-based deployment: `staging` → staging environment, `main` → production
- Health checks run post-deployment to verify services are up

**Key Files:**
- `.github/workflows/deploy-backend.yml`
- `.github/workflows/staging-frontend.yaml`

---

### Q2: How did you resolve the CORS configuration issues?

**A:** Implemented a custom `WildcardCORSMiddleware` that:
- Supports wildcard patterns (e.g., `https://*.vercel.app`)
- Converts wildcards to regex for pattern matching
- Handles OPTIONS preflight requests
- Validates origins against `ALLOWED_ORIGINS` from environment variables
- Falls back to `FRONTEND_URL` if configured

**Implementation:** `backend/app/main.py` - `WildcardCORSMiddleware` class

---

### Q3: Why did you choose Render for backend and Vercel for frontend?

**A:** 
- **Render**: Better for Python/FastAPI, supports Docker, environment variables, and auto-deploy from GitHub
- **Vercel**: Optimized for Next.js, edge functions, automatic preview deployments, and excellent DX
- Both offer free tiers suitable for MVP
- Both integrate seamlessly with GitHub Actions

---

## Whisper Transcription Service

### Q4: How does the Whisper transcription service handle different audio formats?

**A:** The service:
- Accepts multiple formats: `mp3, wav, m4a, ogg, flac, webm`
- Validates file size (default: 25MB max, configurable)
- Uses OpenAI Whisper API (`whisper-1` model)
- Supports language detection (auto) or explicit language codes
- Handles both file uploads and URL-based transcription

**Key Features:**
- File validation before API call
- Temporary file handling for uploads
- Error handling for invalid formats/sizes
- Returns transcribed text, detected language, and duration

**Implementation:** `backend/app/services/whisper_service.py`

---

### Q5: What happens if an audio file is too large or in an unsupported format?

**A:** 
- **File size**: Returns `400 Bad Request` with error message before API call
- **Format**: Validates against `ALLOWED_AUDIO_FORMATS` list, returns `400` if invalid
- **API errors**: Catches OpenAI API errors and returns `500` with descriptive message
- All errors are logged for debugging

**Error Response Example:**
```json
{
  "detail": "File size exceeds maximum allowed size of 25MB"
}
```

---

### Q6: How do you handle language detection vs. explicit language specification?

**A:**
- **Explicit**: Pass `language` parameter (e.g., `"en"`, `"es"`) - faster, more accurate
- **Auto-detection**: Pass `"auto"` or omit parameter - Whisper detects automatically
- Default is `"en"` if not specified
- Detected language is returned in response for verification

**Usage:**
```bash
# Explicit
POST /api/v1/transcribe?language=en

# Auto-detect
POST /api/v1/transcribe?language=auto
```

---

## GPT-4 Parsing Service

### Q7: How does the GPT-4 parser convert natural language to CAD instructions?

**A:** The parser:
- Uses system prompts tailored to each CAD file type (DXF, DWG, Revit, STEP)
- Sends transcribed text to GPT-4 with structured output requirements
- Parses JSON response into `ParsedInstruction` objects
- Returns commands with parameters and confidence scores
- Supports additional context for better parsing

**Flow:**
1. User input: "Create a rectangle 100x50"
2. GPT-4 processes with CAD-specific prompt
3. Returns: `{"command": "RECTANGLE", "parameters": {"width": 100, "height": 50}}`
4. Service validates and structures response

**Implementation:** `backend/app/services/gpt_parser_service.py`

---

### Q8: What CAD file types are supported, and how do you handle different formats?

**A:** Currently supported:
- **DXF** (default) - AutoCAD Drawing Exchange Format
- **DWG** - AutoCAD native format
- **Revit** - BIM format
- **STEP** - 3D CAD format

**How it works:**
- Each file type has a custom system prompt with format-specific instructions
- GPT-4 generates commands appropriate to the target format
- Future: Actual file generation using `ezdxf` library (already in dependencies)

**Configuration:** `backend/app/schemas/parser.py` - `CADFileType` enum

---

### Q9: How do you ensure the GPT-4 responses are structured correctly?

**A:**
- **System prompts** explicitly request JSON format
- **Response validation** using Pydantic schemas
- **Error handling** for malformed JSON
- **Fallback** to raw response if parsing fails
- **Confidence scores** included in each instruction

**Example Response:**
```json
{
  "status": "success",
  "instructions": [
    {
      "command": "RECTANGLE",
      "parameters": {"width": 100, "height": 50},
      "confidence": 0.95
    }
  ],
  "file_type": "dxf"
}
```

---

## Projects Management API

### Q10: How is the Projects API integrated with Supabase?

**A:**
- Uses Supabase Python client for database operations
- **Service Role Key** for admin operations (bypasses RLS)
- **Anon Key** available for client-side operations
- CRUD operations: Create, Read, Update, Delete
- Query functions abstract database logic

**Architecture:**
- `backend/app/db/supabase_client.py` - Client initialization
- `backend/app/db/queries/project_queries.py` - Database operations
- `backend/app/routes/project_routes.py` - API endpoints

---

### Q11: How do you handle Supabase connection failures gracefully?

**A:**
- **Startup**: App starts even if Supabase credentials are missing (logs warning)
- **Runtime**: Checks if client is initialized before operations
- **Error handling**: Returns appropriate HTTP status codes
- **Health checks**: Reports Supabase status in `/health/detailed`

**Implementation:**
```python
# Graceful initialization
if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
    logger.warning("Supabase credentials not configured")
    self._client = None
```

---

## Error Handling & Monitoring

### Q12: How is error handling implemented across the services?

**A:**
- **Global exception handlers** in `app/utils/error_handler.py`
- **Service-level validation** before API calls
- **HTTP status codes**: 400 (validation), 500 (server errors), 503 (service unavailable)
- **Structured logging** using `structlog`
- **Sentry integration** for production error tracking

**Error Response Format:**
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

---

### Q13: How is Sentry configured, and what happens if it's not set up?

**A:**
- **Initialization**: Only initializes if valid DSN provided (not placeholder)
- **Validation**: Checks for `"sentry.io"` in DSN to prevent invalid configs
- **Graceful degradation**: App runs without Sentry if not configured
- **Integration**: Captures exceptions, performance data, and custom events

**Implementation:** `backend/app/core/logging_config.py` - `init_sentry()`

---

## Configuration & Environment

### Q14: How are environment variables managed across different environments?

**A:**
- **Local**: `.env` files (gitignored)
- **Staging/Production**: Environment variables in Render/Vercel dashboards
- **GitHub Secrets**: For CI/CD workflows
- **Validation**: Pydantic settings with defaults for optional values
- **Documentation**: `env.example` template with all required variables

**Key Variables:**
- `OPENAI_API_KEY` - Required for AI features
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` - Database
- `SENTRY_DSN` - Optional monitoring
- `ALLOWED_ORIGINS` - CORS configuration

---

### Q15: How did you resolve the dependency conflicts (postgrest, anyio)?

**A:**
- **postgrest**: Removed explicit version constraint, let `supabase` manage it
- **anyio**: Removed explicit version, `openai` and `httpx` resolve it
- **supabase**: Changed from `==2.5.1` to `>=2.5.1` for flexibility
- **Result**: Pip can now resolve dependencies automatically

**Fix Applied:**
```txt
# Before
postgrest==0.13.0
anyio==4.4.0
supabase==2.5.1

# After
# postgrest managed by supabase
# anyio managed by dependencies
supabase>=2.5.1
```

---

## Testing & Quality Assurance

### Q16: How can developers test the endpoints locally?

**A:**
- **Swagger UI**: `http://localhost:8000/docs` - Interactive API testing
- **Test script**: `backend/test_endpoints.py` - Automated endpoint testing
- **Health checks**: `/health/` and `/health/detailed` for status verification
- **Manual testing**: cURL or Postman for specific scenarios

**Test Script Usage:**
```bash
cd backend
python3.12 test_endpoints.py
python3.12 test_endpoints.py --audio /path/to/audio.mp3
```

---

### Q17: What testing is in place for the CI/CD pipeline?

**A:**
- **Backend**: Pytest runs on PR creation (if tests exist)
- **Frontend**: Vitest runs in GitHub Actions
- **Linting**: Code quality checks (flake8 for Python, ESLint for TypeScript)
- **Build verification**: Ensures code compiles before deployment

**Workflow:** `.github/workflows/deploy-backend.yml`

---

## Security

### Q18: How are API keys and sensitive credentials protected?

**A:**
- **Never committed**: `.env` files in `.gitignore`
- **GitHub Secrets**: For CI/CD workflows
- **Environment variables**: Set in Render/Vercel dashboards
- **Service role keys**: Only in backend, never exposed to frontend
- **Anon keys**: Safe for frontend (RLS enabled in Supabase)

**Best Practices:**
- Different credentials for staging/production
- Regular rotation recommended
- Least privilege principle
- 2FA enabled on all accounts

---

### Q19: How is file upload security handled?

**A:**
- **Size limits**: Configurable max file size (default: 25MB)
- **Format validation**: Whitelist of allowed audio formats
- **Temporary files**: Created in system temp directory, cleaned up after processing
- **No persistent storage**: Files are processed and discarded

**Configuration:**
```python
MAX_FILE_SIZE_MB=25
ALLOWED_AUDIO_FORMATS=mp3,wav,m4a,ogg,flac,webm
```

---

## Architecture Decisions

### Q20: Why did you use Pydantic schemas for request/response validation?

**A:**
- **Type safety**: Automatic validation and type checking
- **Documentation**: Auto-generated OpenAPI/Swagger docs
- **Error messages**: Clear validation errors for invalid inputs
- **Consistency**: Standardized request/response formats

**Example:**
```python
class TranscriptionResponse(BaseModel):
    status: str
    text: str
    language: str
    filename: Optional[str]
    duration: Optional[float]
    timestamp: datetime
```

---

### Q21: How is the codebase structured for scalability?

**A:**
- **Modular design**: Separate services, schemas, routes
- **Dependency injection**: Global service instances
- **Configuration management**: Centralized settings
- **Error handling**: Global exception handlers
- **Logging**: Structured logging throughout

**Structure:**
```
app/
├── api/          # API endpoints
├── services/     # Business logic
├── schemas/      # Data validation
├── core/         # Configuration
└── routes/       # Additional routes
```

---

## Performance & Optimization

### Q22: How do you handle long-running transcription requests?

**A:**
- **Async operations**: FastAPI async endpoints
- **Timeout handling**: OpenAI API has built-in timeouts
- **Error recovery**: Graceful error messages if timeout occurs
- **Future**: Could implement background jobs with Celery for very long files

**Current Implementation:**
- Synchronous OpenAI API calls (blocking)
- FastAPI async wrapper for concurrency
- No queue system yet (MVP scope)

---

### Q23: What are the rate limits and how are they handled?

**A:**
- **OpenAI API**: Rate limits based on tier (not handled in code yet)
- **Supabase**: Connection pooling handled by client
- **Future**: Implement rate limiting middleware for API endpoints
- **Monitoring**: Sentry tracks API errors including rate limits

**Recommendations:**
- Implement exponential backoff for retries
- Add rate limiting middleware (e.g., `slowapi`)
- Monitor API usage in production

---

## Future Enhancements

### Q24: What's the plan for actual CAD file generation?

**A:**
- **Library**: `ezdxf` already in dependencies
- **Next steps**: 
  1. Parse GPT-4 instructions into DXF commands
  2. Use `ezdxf` to generate actual `.dxf` files
  3. Store files in Supabase Storage
  4. Return download links to users

**Current Status:** Parsing complete, file generation pending

---

### Q25: How will you handle user authentication and project ownership?

**A:**
- **Supabase Auth**: Already integrated (JWT sessions)
- **RLS Policies**: Row Level Security in Supabase for data isolation
- **API**: Projects API ready for user association
- **Future**: Add user ID to project creation, implement ownership checks

**Current:** Projects API exists, user association pending

---

## Troubleshooting

### Q26: What should I do if the backend won't start?

**A:**
1. **Check Python version**: Requires Python 3.12+
2. **Verify dependencies**: `pip install -r requirements.txt`
3. **Check environment variables**: Ensure `.env` file exists
4. **Port conflicts**: Check if port 8000 is in use
5. **Logs**: Check terminal output for specific errors

**Common Issues:**
- Missing OpenAI API key → App starts but transcription fails
- Missing Supabase credentials → App starts but DB features fail
- Port 8000 in use → Use different port: `--port 8001`

---

### Q27: How do I debug Swagger endpoint duplication issues?

**A:**
- **Cause**: Router tags defined in both router definition and `include_router()`
- **Solution**: Remove tags from `include_router()` if router already has tags
- **Fix applied**: Standardized tags in router definitions only

**Example:**
```python
# Router definition
router = APIRouter(prefix="/projects", tags=["Projects"])

# Include (no tags needed)
app.include_router(router, prefix="/api/v1")
```

---

### Q28: What if Vercel deployment fails with "package.json not found"?

**A:**
- **Cause**: Vercel looking in root directory instead of `frontend/`
- **Solution**: 
  1. Move `vercel.json` to `frontend/` directory
  2. Configure Root Directory in Vercel dashboard → Settings → General → Root Directory: `frontend`

**Fix Applied:** `frontend/vercel.json` created, root directory configuration required

---

## Integration Points

### Q29: How does the frontend communicate with the backend?

**A:**
- **Environment variable**: `NEXT_PUBLIC_API_URL` points to backend
- **CORS**: Backend allows frontend origins
- **API calls**: Frontend uses fetch/axios to call backend endpoints
- **Authentication**: Supabase JWT tokens passed in headers

**Example:**
```typescript
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/transcribe`, {
  method: 'POST',
  body: formData
});
```

---

### Q30: How are environment variables shared between frontend and backend?

**A:**
- **Backend**: Uses `.env` file, loaded by `python-dotenv`
- **Frontend**: Uses `.env.local`, variables must start with `NEXT_PUBLIC_`
- **Shared**: Only Supabase URL and anon key (public, safe)
- **Separate**: Backend has service role key (never in frontend)

**Security Note:** Frontend variables are exposed in browser, backend variables are server-only

---

## Summary

### Key Achievements:
✅ **Weeks 1-2**: Staging deployment, CORS fixes, CI/CD automation  
✅ **Weeks 3-4**: Whisper transcription, GPT-4 parsing, Projects API  
✅ **Infrastructure**: Multi-environment support, error handling, monitoring  
✅ **Documentation**: Comprehensive README, testing guides, Q&A  

### Next Steps:
- [ ] Implement actual CAD file generation
- [ ] Add user authentication to Projects API
- [ ] Implement rate limiting
- [ ] Add background job processing for long transcriptions
- [ ] Expand test coverage
- [ ] Production deployment

---

## Additional Resources

- **API Documentation**:** http://localhost:8000/docs
- **Testing Guide**: `docs/LOCAL_TESTING_GUIDE.md` (consolidated into README)
- **Credentials Setup**: See README.md Credentials section
- **Deployment Guide**: See README.md Deployment section

