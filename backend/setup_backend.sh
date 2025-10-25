#!/bin/bash
# =====================================================
# KRAFZEN AI Backend Folder Setup Script (Updated)
# Author: Krishnarajan V
# Description: Creates full FastAPI + Supabase backend structure
# Aligned with 60-Day MVP Roadmap (Oct 25, 2025)
# =====================================================

echo "Setting up KRAFZEN AI backend structure..."

# Root backend directory
mkdir -p backend
cd backend || exit

# Core directories (per updated structure)
mkdir -p app/{core,db/{queries},models,routes,services,utils,middlewares,tests,docs}
mkdir -p scripts
touch requirements.txt Dockerfile render.yaml Makefile README.md .env.example

# Touch __init__.py for all Python packages
find app -type d -exec touch {}/__init__.py \;

# --- app/core/config.py ---
cat > app/core/config.py <<'EOF'
"""App configuration using Pydantic settings."""
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str  # Client-side
    SUPABASE_SERVICE_KEY: str  # Server-side ops
    
    # OpenAI (Weeks 3-4)
    OPENAI_API_KEY: str
    
    # App/Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Logging/Monitoring
    SENTRY_DSN: str | None = None
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
EOF

# --- app/core/security.py ---
cat > app/core/security.py <<'EOF'
"""JWT and password security utilities."""
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_minutes: int = 30):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)
EOF

# --- app/core/logging_config.py ---
cat > app/core/logging_config.py <<'EOF'
"""Centralized logging + Sentry integration."""
import logging
import structlog
from sentry_sdk.integrations.logging import SentryLoggingIntegration
from app.core.config import settings

# Basic stdlib setup
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Structured logging
timestamper = structlog.processors.TimeStamper(fmt="iso")
pre_chain = [
    structlog.stdlib.add_log_level,
    timestamper,
]
structlog.configure(
    processors=pre_chain + [structlog.processors.JSONRenderer()],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def init_sentry(dsn: str):
    if dsn:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            integrations=[SentryLoggingIntegration(level=logging.INFO)],
            traces_sample_rate=1.0,
        )
EOF

# --- app/db/supabase_client.py ---
cat > app/db/supabase_client.py <<'EOF'
"""Supabase client connection (singleton)."""
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

class SupabaseClient:
    _instance: Optional[Client] = None
    
    def __getattr__(self, name):
        if self._instance is None:
            self._instance = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY,  # Server-side full access
            )
        return getattr(self._instance, name)
    
    @classmethod
    def get_instance(cls) -> 'SupabaseClient':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

db = SupabaseClient.get_instance()
EOF

# --- app/db/queries/project_queries.py (Stub for Week 1 CRUD) ---
cat > app/db/queries/project_queries.py <<'EOF'
"""Project CRUD queries (provisional)."""
from typing import List, Dict
from supabase import Client
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    user_id: str
    input_text: str

async def create_project(client: Client, data: ProjectCreate) -> Dict:
    response = client.table("projects").insert(data.dict()).execute()
    return response.data[0] if response.data else {}

async def get_projects(client: Client, user_id: str) -> List[Dict]:
    response = client.table("projects").select("*").eq("user_id", user_id).execute()
    return response.data
EOF

# --- app/db/schema.sql (Provisional - Align with Laxmi's Design) ---
cat > app/db/schema.sql <<'EOF'
-- Supabase schema definition (Provisional for Weeks 1-2)
-- Designed/Validated by: Laxmi Pranitha Muskula
-- Notes: Users via Supabase Auth; RLS for security; JSONB for parsed AI output

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Projects table (voice/text inputs)
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    input_text TEXT NOT NULL,
    parsed_json JSONB,
    dxf_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table (workflow status: transcribe/parse/generate)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'transcribing', 'parsing', 'generating', 'completed', 'failed')),
    transcript TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Files table (DXF storage)
CREATE TABLE IF NOT EXISTS files (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL,
    file_type TEXT DEFAULT 'dxf',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies (Basic Auth - Expand for Full Layers)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own projects" ON projects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own projects" ON projects FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Similar for jobs/files
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own jobs" ON jobs FOR ALL USING (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));
CREATE POLICY "Users insert own jobs" ON jobs FOR INSERT WITH CHECK (auth.uid() = (SELECT user_id FROM projects WHERE id = project_id));

ALTER TABLE files ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own files" ON files FOR ALL USING (auth.uid() = (SELECT user_id FROM jobs j JOIN projects p ON j.project_id = p.id WHERE j.id = file_id));
CREATE POLICY "Users insert own files" ON files FOR INSERT WITH CHECK (auth.uid() = (SELECT user_id FROM jobs j JOIN projects p ON j.project_id = p.id WHERE j.id = file_id));
EOF

# --- app/main.py ---
cat > app/main.py <<'EOF'
"""FastAPI entry point for KRAFZEN AI backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import init_sentry
from app.utils.error_handler import add_exception_handlers
from app.routes import project_routes  # Stub import

app = FastAPI(
    title="KRAFZEN AI Backend",
    description="API for voice/text to DXF conversion MVP",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (expand for jobs/files)
app.include_router(project_routes.router, prefix="/api/v1", tags=["projects"])

@app.get("/health")
async def health_check():
    # Quick DB ping (provisional)
    try:
        count = len(db.table("projects").select("count").execute().data)
        return {"status": "healthy", "db_projects": count}
    except:
        return {"status": "healthy", "db": "pending"}

# Init logging/Sentry/error handlers
init_sentry(settings.SENTRY_DSN)
add_exception_handlers(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
EOF

# --- app/utils/error_handler.py ---
cat > app/utils/error_handler.py <<'EOF'
"""Global exception handling."""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

def add_exception_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail},
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"message": "Validation Error", "detail": exc.errors()},
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"message": "Internal Server Error", "detail": str(exc)},
        )
EOF

# --- app/utils/logger.py ---
cat > app/utils/logger.py <<'EOF'
"""Custom logger wrapper with structlog."""
from structlog import get_logger

logger = get_logger("krafzen")
EOF

# --- app/models/project_model.py (Stub Pydantic) ---
cat > app/models/project_model.py <<'EOF'
"""Pydantic models for validation."""
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class ProjectBase(BaseModel):
    user_id: str
    input_text: str

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: str
    created_at: datetime
    parsed_json: Optional[Dict] = None
    dxf_url: Optional[str] = None

    class Config:
        from_attributes = True
EOF

# --- app/routes/project_routes.py (Week 1 CRUD Stub) ---
cat > app/routes/project_routes.py <<'EOF'
"""Project API routes (CRUD stub)."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.db.supabase_client import db
from app.db.queries.project_queries import create_project, get_projects
from app.models.project_model import ProjectCreate, ProjectOut

router = APIRouter()

@router.post("/projects/", response_model=ProjectOut)
async def create_project_route(project: ProjectCreate):
    # TODO: Auth dep for user_id
    result = await create_project(db, project)
    if not result:
        raise HTTPException(status_code=400, detail="Project creation failed")
    return result

@router.get("/projects/", response_model=List[ProjectOut])
async def list_projects(user_id: str):  # From auth dep later
    projects = await get_projects(db, user_id)
    return projects
EOF

# --- app/tests/conftest.py ---
cat > app/tests/conftest.py <<'EOF'
"""Pytest fixtures."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def override_settings():
    # Mock settings for tests
    from app.core.config import settings
    return settings
EOF

# --- app/tests/test_health.py ---
cat > app/tests/test_health.py <<'EOF'
"""Basic health tests."""
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
EOF

# --- app/tests/test_projects.py (Stub for Coverage) ---
cat > app/tests/test_projects.py <<'EOF'
"""Project API tests (provisional)."""
def test_create_project(client):
    response = client.post(
        "/api/v1/projects/",
        json={"user_id": "test-uuid", "input_text": "Test input"}
    )
    assert response.status_code == 200
    assert "id" in response.json()

def test_list_projects(client):
    response = client.get("/api/v1/projects/?user_id=test-uuid")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
EOF

# --- app/docs/api.postman_collection.json (Stub for Postman) ---
cat > app/docs/api.postman_collection.json <<'EOF'
{
  "info": {"name": "KRAFZEN API Tests", "_postman_id": "initial"},
  "item": [
    {"name": "Health", "request": {"method": "GET", "url": "{{base_url}}/health"}},
    {"name": "Create Project", "request": {"method": "POST", "url": "{{base_url}}/api/v1/projects/", "body": {"mode": "raw", "raw": "{\"user_id\": \"test\", \"input_text\": \"Draw rectangle\"}"}}}
  ],
  "variable": [{"key": "base_url", "value": "http://localhost:8000"}]
}
EOF

# --- Root .env.example ---
cat > .env.example <<'EOF'
# Supabase (from dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# OpenAI (Weeks 3-4)
OPENAI_API_KEY=sk-your_openai_key

# Security
SECRET_KEY=your_generated_secret  # e.g., openssl rand -hex 32

# App
FRONTEND_URL=http://localhost:3000
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=INFO
EOF

# --- scripts/setup_supabase.sh ---
cat > scripts/setup_supabase.sh <<'EOF'
#!/bin/bash
# Init Supabase (run after CLI install: npm i -g supabase)
echo "🚀 Initializing Supabase schema..."
# Link project: supabase link --project-ref your-project-id
supabase db push app/db/schema.sql
echo "Schema pushed! Validate with Laxmi."
EOF
chmod +x scripts/setup_supabase.sh

# --- Makefile ---
cat > Makefile <<'EOF'
.PHONY: run test db-setup format lint install

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

test:
	pytest app/tests/ -v --cov=app/ --cov-report=html

db-setup:
	./scripts/setup_supabase.sh

format:
	black . && isort .

lint:
	ruff check .
EOF

# --- requirements.txt (Fixed Versions) ---
cat > requirements.txt <<'EOF'
# =====================================================
# KRAFZEN AI Backend Requirements (Week 1-2 Stable)
# Maintainer: Krishnarajan V
# =====================================================

# Core Framework
fastapi==0.115.0
uvicorn[standard]==0.30.6

# Database / Supabase
supabase==2.5.1
python-dotenv==1.0.1

# Auth & Security
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
cryptography==43.0.1

# Logging & Monitoring
structlog==24.4.0
sentry-sdk==2.42.1  # Fixed to latest stable

# Validation
pydantic[email]==2.9.2
pydantic-settings==2.5.2  # For BaseSettings

# Testing / Async
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
anyio==4.4.0

# Dev Tools (add to dev-requirements.txt later)
# black==24.8.0
# ruff==0.5.7
# pytest-cov==5.0.0

# Future (Weeks 3-6: AI & DXF)
# openai==1.51.2
# ezdxf==1.3.5
EOF

# --- README.md (Basic) ---
cat > README.md <<'EOF'
# KRAFZEN AI Backend

FastAPI backend for voice/text to DXF MVP (60-Day Roadmap).

## Setup (Week 1)
1. `pip install -r requirements.txt`
2. `cp .env.example .env` → Fill Supabase/OpenAI keys
3. `./scripts/setup_supabase.sh` (pushes schema.sql)
4. `make run` → http://localhost:8000/docs

## Milestones
- Weeks 1-2: Supabase schema + API connects (Krishnarajan V)
- Tests: `make test` (100% coverage target)
- Deploy: Render via render.yaml (Kiruthika)

Team: Kiruthika (Lead), Sonu (Frontend), Laxmi (Data), Ashwani (QA).
EOF

# --- render.yaml (Stub for Render) ---
cat > render.yaml <<'EOF'
services:
  - type: web
    name: krafzen-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
EOF

# --- Dockerfile (Stub) ---
cat > Dockerfile <<'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

echo "KRAFZEN AI backend structure updated successfully!"