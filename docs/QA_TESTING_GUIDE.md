# QA Testing Guide for KRAFZEN AI
## Guide for Ashwani Kumar - Jr. Developer / QA Engineer

This document provides step-by-step instructions for setting up your testing environment and completing your QA objectives.

---

## Table of Contents
1. [Environment Setup](#environment-setup)
2. [Week 1-2 Objectives: API Health Checks & Postman Setup](#week-1-2-objectives)
3. [Week 3-4 Objectives: AI Endpoints & JSON Schema Validation](#week-3-4-objectives)
4. [Test Scripts Location](#test-scripts-location)
5. [Issue Tracker Setup](#issue-tracker-setup)
6. [Regression Testing Checklist](#regression-testing-checklist)

---

## Environment Setup

### Prerequisites
- Python 3.12+ installed
- Node.js 18+ installed (for frontend testing)
- Postman Desktop App installed
- Git installed
- Text editor/IDE (VS Code recommended)

### Step 1: Clone and Setup Backend Environment

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment (if not already created):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file from template:**
   ```bash
   cp env.example .env
   ```

5. **Configure `.env` file:**
   - Get OpenAI API key from team lead
   - Get Supabase credentials from team lead
   - Set `ENVIRONMENT=development` for local testing
   - Set `DEBUG=True` for local development

### Step 2: Start the Backend Server

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

3. **Verify server is running:**
   - Open browser: `http://localhost:8000`
   - Should see: `{"message":"KRAFZEN AI API","version":"0.1.0","status":"running"}`

### Step 3: Install Testing Tools

1. **Python testing tools (already in requirements.txt):**
   - `pytest` - Test framework
   - `pytest-asyncio` - Async test support
   - `httpx` - HTTP client for testing

2. **Verify installation:**
   ```bash
   pytest --version
   ```

### Step 4: Setup Frontend Environment (for UI testing)

1. **Navigate to root directory:**
   ```bash
   cd ..
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Verify frontend is running:**
   - Open browser: `http://localhost:3000`

---

## Week 1-2 Objectives: API Health Checks & Postman Setup

### Objective 1: Test API Health Checks

#### Endpoints to Test:

1. **Root Endpoint:**
   - URL: `GET http://localhost:8000/`
   - Expected Response:
     ```json
     {
       "message": "KRAFZEN AI API",
       "version": "0.1.0",
       "status": "running"
     }
     ```

2. **Basic Health Check:**
   - URL: `GET http://localhost:8000/health/`
   - Expected Response:
     ```json
     {
       "status": "healthy",
       "timestamp": "2024-01-01T12:00:00.000000",
       "service": "KRAFZEN AI Backend"
     }
     ```

3. **Detailed Health Check:**
   - URL: `GET http://localhost:8000/health/detailed`
   - Expected Response Schema:
     ```json
     {
       "status": "healthy",
       "timestamp": "string (ISO format)",
       "service": "KRAFZEN AI Backend",
       "version": "0.1.0",
       "environment": "development",
       "response_time_ms": 0.0,
       "uptime": "N/A",
       "dependencies": {
         "database": "connected" | "disconnected",
         "openai": "pending"
       },
       "supabase": {
         "status": "success" | "error",
         "message": "string",
         "connected": true | false
       },
       "monitoring": {
         "sentry_enabled": true | false,
         "environment": "string"
       }
     }
     ```

#### Running Automated Tests:

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Run health check tests:**
   ```bash
   pytest tests/test_health.py -v
   ```

3. **Run all tests:**
   ```bash
   pytest tests/ -v
   ```

#### Manual Testing Checklist:

- [ ] Root endpoint returns correct JSON structure
- [ ] Basic health check endpoint responds within 200ms
- [ ] Detailed health check includes all required fields
- [ ] Database connection status is accurate
- [ ] Response time is reasonable (< 1000ms)
- [ ] Error handling works when services are down

### Objective 2: Setup Postman Workspace

#### Step 1: Create Postman Workspace

1. **Open Postman Desktop App**
2. **Click "Workspaces" → "Create Workspace"**
3. **Name:** `KRAFZEN AI API Testing`
4. **Description:** `Testing workspace for KRAFZEN AI FastAPI endpoints`
5. **Visibility:** Team (if working in team) or Personal

#### Step 2: Create Environment Variables

1. **Click "Environments" → "Create Environment"**
2. **Name:** `KRAFZEN AI - Local`
3. **Add Variables:**
   - `base_url` = `http://localhost:8000`
   - `api_version` = `v1`

4. **Create another environment:** `KRAFZEN AI - Staging`
   - `base_url` = `https://your-staging-url.com`
   - `api_version` = `v1`

#### Step 3: Create Collection Structure

Create a collection named: `KRAFZEN AI API Tests`

**Folder 1: Health Checks**
- `Root Endpoint` (GET {{base_url}}/)
- `Basic Health Check` (GET {{base_url}}/health/)
- `Detailed Health Check` (GET {{base_url}}/health/detailed)

**Folder 2: Transcriber API**
- `Transcribe Audio File` (POST {{base_url}}/api/v1/transcribe)
- `Transcribe from URL` (POST {{base_url}}/api/v1/transcribe-url)

#### Step 4: Create Test Scripts in Postman

For each request, add tests in the "Tests" tab:

**Example for Basic Health Check:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has status field", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
});

pm.test("Status is healthy", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.status).to.eql('healthy');
});

pm.test("Response time is less than 500ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(500);
});
```

**Example for Detailed Health Check:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has all required fields", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('status');
    pm.expect(jsonData).to.have.property('timestamp');
    pm.expect(jsonData).to.have.property('service');
    pm.expect(jsonData).to.have.property('dependencies');
    pm.expect(jsonData).to.have.property('supabase');
});

pm.test("Database dependency status is present", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.dependencies).to.have.property('database');
});
```

#### Step 5: Export and Share Collection

1. **Right-click collection → "Export"**
2. **Save as:** `KRAFZEN_AI_API_Tests.postman_collection.json`
3. **Commit to repository** (in `docs/` or `backend/` folder)
4. **Share with team** via Postman sharing or Git

---

## Week 3-4 Objectives: AI Endpoints & JSON Schema Validation

### Objective 1: QA Test AI Endpoints

#### Endpoints to Test:

1. **Transcribe Audio File:**
   - URL: `POST http://localhost:8000/api/v1/transcribe`
   - Method: POST
   - Headers: `Content-Type: multipart/form-data`
   - Body: Form-data
     - `file`: [Select File] (mp3, wav, m4a, etc.)
     - `language`: `en` (optional, default: en)

   **Test Cases:**
   - [ ] Valid audio file upload returns success
   - [ ] Response contains `status`, `text`, `language`, `filename`
   - [ ] Invalid file type returns error
   - [ ] Missing file returns 422 error
   - [ ] Large file (>10MB) handles gracefully
   - [ ] Multiple language codes work correctly

2. **Transcribe from URL:**
   - URL: `POST http://localhost:8000/api/v1/transcribe-url`
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Body:
     ```json
     {
       "audio_url": "https://example.com/audio.mp3",
       "language": "en"
     }
     ```

   **Test Cases:**
   - [ ] Valid URL returns success
   - [ ] Response contains `status`, `text`, `url`
   - [ ] Invalid URL returns error
   - [ ] Missing URL returns 422 error
   - [ ] Non-audio URL returns appropriate error
   - [ ] URL timeout handled gracefully

### Objective 2: Validate JSON Schema Parsing

#### Create JSON Schema Files

Store schemas in `backend/tests/schemas/` directory.

#### Example Schema for Health Check Response:

Create `backend/tests/schemas/health_schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["status", "timestamp", "service"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["healthy", "unhealthy"]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "service": {
      "type": "string"
    },
    "version": {
      "type": "string"
    },
    "environment": {
      "type": "string"
    },
    "response_time_ms": {
      "type": "number"
    },
    "dependencies": {
      "type": "object",
      "properties": {
        "database": {
          "type": "string"
        },
        "openai": {
          "type": "string"
        }
      }
    }
  }
}
```

#### Validate Schema in Tests

Use `jsonschema` library in Python tests:

```python
import jsonschema
import json

def test_detailed_health_check_schema(client):
    response = client.get("/health/detailed")
    assert response.status_code == 200
    
    # Load schema
    with open("tests/schemas/health_schema.json") as f:
        schema = json.load(f)
    
    # Validate response against schema
    jsonschema.validate(instance=response.json(), schema=schema)
```

#### Running Schema Validation Tests:

```bash
pytest tests/test_schemas.py -v
```

---

## Test Scripts Location

All test files are located in:
- **Backend:** `backend/tests/`
- **Frontend:** `__tests__/` (root directory)

### Test File Structure:

```
backend/tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_health.py           # Health check endpoint tests
├── test_transcriber.py      # Transcriber endpoint tests
├── test_schemas.py          # JSON schema validation tests
└── schemas/
    ├── health_schema.json
    ├── transcriber_schema.json
    └── error_schema.json
```

---

## Issue Tracker Setup

### Recommended Tools:

1. **GitHub Issues** (if using GitHub)
2. **Linear** (if team uses it)
3. **Notion** (if team uses it)
4. **Excel/Google Sheets** (simple tracking)

### Issue Template:

**Title:** `[API/UI] [Severity] Brief description`

**Severity Levels:**
- `Critical`: Blocks core functionality
- `High`: Major feature broken
- `Medium`: Minor issue, workaround exists
- `Low`: Cosmetic or nice-to-have

**Issue Fields:**
- **Endpoint/Component:** Which API endpoint or UI component
- **Steps to Reproduce:** Detailed steps
- **Expected Behavior:** What should happen
- **Actual Behavior:** What actually happens
- **Environment:** Local/Staging/Production
- **Status:** Open/In Progress/Fixed/Verified
- **Test Case:** Which test case failed
- **Screenshots/Logs:** Attach relevant files

### Example Issue:

```
Title: [API] [High] Detailed health check returns 500 when Supabase is down

Endpoint: GET /health/detailed
Environment: Local
Status: Open

Steps to Reproduce:
1. Stop Supabase service
2. Call GET /health/detailed
3. Observe 500 error

Expected Behavior:
Should return 200 with "connected": false in dependencies

Actual Behavior:
Returns 500 Internal Server Error

Test Case: test_detailed_health_check_with_disconnected_db
```

---

## Regression Testing Checklist

Before each release/demo, run through this checklist:

### Backend API Tests:
- [ ] All health check endpoints return 200
- [ ] All transcriber endpoints handle valid requests
- [ ] All endpoints handle invalid requests gracefully
- [ ] Error responses follow consistent schema
- [ ] Response times are acceptable (< 5s for AI endpoints)
- [ ] CORS headers are properly set
- [ ] Authentication/Authorization works (if implemented)

### Schema Validation:
- [ ] All response schemas validated
- [ ] All request body schemas validated
- [ ] Schema files committed to repository

### Integration Tests:
- [ ] Database connectivity works
- [ ] External API calls (OpenAI) work
- [ ] File uploads work correctly
- [ ] Error handling works for external service failures

### Performance Tests:
- [ ] Health checks respond in < 500ms
- [ ] AI endpoints respond in < 30s (depends on audio length)
- [ ] Server handles concurrent requests
- [ ] Large file uploads don't crash server

### Documentation:
- [ ] Postman collection updated
- [ ] Test results documented
- [ ] Known issues documented
- [ ] API documentation updated (if changed)

---

## Running Tests

### Run All Backend Tests:
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Run Specific Test File:
```bash
pytest tests/test_health.py -v
```

### Run Tests with Coverage:
```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Run Frontend Tests:
```bash
npm test
```

### Run Frontend Tests in UI Mode:
```bash
npm run test:ui
```

---

## Troubleshooting

### Issue: Tests can't find modules
**Solution:** Make sure you're in the backend directory and virtual environment is activated.

### Issue: Import errors
**Solution:** Check that `backend/` is in Python path, or run from backend directory.

### Issue: Database connection fails
**Solution:** Verify `.env` file has correct Supabase credentials.

### Issue: Server not starting
**Solution:** Check if port 8000 is already in use: `lsof -i :8000`

---

## Next Steps

1. **Week 1-2:**
   - Set up environment
   - Write health check tests
   - Create Postman workspace
   - Document findings

2. **Week 3-4:**
   - Write transcriber endpoint tests
   - Create JSON schemas
   - Validate all API responses
   - Document test results

3. **Ongoing:**
   - Maintain test scripts
   - Update Postman collection
   - Track issues
   - Run regression tests before releases

---

## Contact & Support

If you encounter issues:
1. Check this guide first
2. Review existing test files
3. Check GitHub issues/team chat
4. Contact team lead if blocked

**Happy Testing! 🚀**

