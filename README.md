# KRAFZEN AI - SaaS Platform for CAD/BIM Generation

## Project Overview
KRAFZEN AI is an AI-powered SaaS platform that converts voice and text instructions into CAD/BIM files (DXF, DWG, Revit, etc.).

## Tech Stack (MVP)

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Hosting**: Render.com (Multi-environment: Staging + Production)
- **Database**: Supabase (PostgreSQL)
- **AI Services**: OpenAI Whisper (transcription) + GPT-4 (parsing)
- **CAD Engine**: ezdxf (Python library)
- **CI/CD**: GitHub Actions with branch protection
- **Monitoring**: Sentry (error tracking) + Health checks
- **Environment**: Multi-environment support (dev/staging/production)

### Frontend
- **Framework**: Next.js 16+ with Tailwind CSS
- **Hosting**: Vercel (Multi-environment)
- **State Management**: React Context API
- **Auth**: Supabase (JWT sessions)
- **Monitoring**: Sentry + PostHog
- **Testing**: Vitest

## Project Structure
```
KRAFZEN-AI-/
├── README.md                    # This file
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py              # Application entry point
│   │   ├── api/                 # API endpoints
│   │   │   ├── health.py        # Health check endpoints
│   │   │   ├── transcriber.py   # Whisper transcription endpoints
│   │   │   └── parser.py        # GPT-4 parsing endpoints
│   │   ├── services/            # Business logic services
│   │   │   ├── whisper_service.py
│   │   │   └── gpt_parser_service.py
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── core/                # Core configuration
│   │   └── routes/              # Additional routes
│   ├── requirements.txt         # Python dependencies
│   ├── env.example              # Environment variables template
│   ├── Dockerfile               # Docker configuration
│   └── render.yaml              # Render deployment config
│
├── frontend/                    # Next.js frontend
│   ├── components/              # React components
│   ├── app/                     # App router structure
│   ├── lib/                     # Helper functions
│   └── public/                  # Static assets
│
├── .github/                     # GitHub Actions & configs
│   ├── workflows/               # CI/CD pipelines
│   ├── CODEOWNERS               # Code ownership rules
│   └── BRANCH_PROTECTION.md     # Branch protection guidelines
│
└── docs/                        # Project documentation
    ├── DEPLOYMENT_STRATEGY.md   # CTO's deployment strategy
    └── *.pdf                    # Planning documents (reference)
```

## Getting Started

### Prerequisites
- **Python 3.12+** installed on your system
- **Node.js 20+** and npm installed
- **Git** for cloning the repository

### Local Development Setup

#### 1. Clone the Repository
```bash
git clone git@github.com:KRAFZEN/KRAFZEN-AI-.git
cd KRAFZEN-AI-
```

#### 2. Backend Setup

**Step 1: Create and activate virtual environment**
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Step 2: Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 3: Configure environment variables**
```bash
cp env.example .env
# Edit .env with your actual credentials (see Credentials section below)
```

**Important**: The `.env` file is gitignored and will not be committed to the repository. Always use `env.example` as a template and never commit your actual `.env` file with real secrets.

**Step 4: Start the backend server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at:
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health/
- **API Documentation (Swagger)**: http://localhost:8000/docs

#### 3. Frontend Setup

**Step 1: Install dependencies**
```bash
cd frontend
npm install
```

**Step 2: Configure environment variables**
```bash
# Create .env.local file
touch .env.local
# Add your Supabase credentials (see Credentials section)
```

**Step 3: Start the development server**
```bash
npm run dev
```

The frontend will be available at:
- **Application**: http://localhost:3000

## Credentials Setup

### Required Credentials

1. **OpenAI API Key** - Required for Whisper transcription and GPT-4 parsing
   - Get from: https://platform.openai.com/api-keys
   - Add to `backend/.env`: `OPENAI_API_KEY=sk-your-key-here`

2. **Supabase Credentials** - Required for database operations
   - Get from: https://app.supabase.com → Settings → API
   - **Backend** (`backend/.env`):
     - `SUPABASE_URL=https://your-project.supabase.co`
     - `SUPABASE_ANON_KEY=your-anon-key` (for RLS)
     - `SUPABASE_SERVICE_ROLE_KEY=your-service-role-key` (for admin ops)
   - **Frontend** (`frontend/.env.local`):
     - `NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co`
     - `NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key`

3. **Sentry DSN** (Optional) - For error monitoring
   - Get from: https://sentry.io
   - Add to `backend/.env`: `SENTRY_DSN=your-dsn-here`

### Environment Variables

**Backend** (`backend/.env`):
```bash
# Application
ENVIRONMENT=development
DEBUG=True
PORT=8000

# OpenAI (Required for AI features)
OPENAI_API_KEY=sk-your-openai-key-here

# Supabase (Required for database)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://*.vercel.app

# Optional
SENTRY_DSN=your-sentry-dsn-here
GPT_MODEL=gpt-4-turbo-preview
GPT_MAX_TOKENS=2000
GPT_TEMPERATURE=0.3
MAX_FILE_SIZE_MB=25
```

**Frontend** (`frontend/.env.local`):
```bash
# Supabase (Public keys - safe for browser)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

⚠️ **Security Note**: Never commit `.env` or `.env.local` files. They are in `.gitignore`.

## API Endpoints

### Health & Status
- **`GET /health/`** - Basic health check endpoint returning service status and timestamp
- **`GET /health/detailed`** - Comprehensive health check with system info, dependency status, and response time metrics

### Transcription (Whisper Service)
- **`POST /api/v1/transcribe`** - Converts uploaded audio files (mp3, wav, m4a, ogg, flac, webm) to text using OpenAI Whisper
  - **Body**: `multipart/form-data` with `file` field
  - **Query**: `language` (optional, default: "en", use "auto" for auto-detection)
  - **Response**: `{"status": "success", "text": "...", "language": "en", "duration": 5.2, ...}`
- **`POST /api/v1/transcribe-url`** - Transcribes audio files from remote URLs using OpenAI Whisper
  - **Query**: `audio_url` (required), `language` (optional)
  - **Response**: Same format as file upload endpoint

### Parsing (GPT-4 Service)
- **`POST /api/v1/parse`** - Converts transcribed text into structured CAD instructions (DXF, DWG, Revit) using GPT-4
  - **Body**: `{"text": "...", "file_type": "dxf|dwg|revit", "additional_context": "..."}`
  - **Response**: `{"status": "success", "instructions": [...], "file_type": "dxf", ...}`
- **`POST /api/v1/parse-transcription`** - Convenience endpoint for parsing transcription text directly
  - **Body**: `{"transcription_id": "...", "file_type": "dxf"}`

### Projects Management API
The Projects Management API provides complete CRUD operations for managing user projects:
- **`GET /api/v1/projects/`** - Retrieves list of all projects for a specific user with optional filtering
- **`POST /api/v1/projects/`** - Creates a new project with metadata and stores it in Supabase database
- **`GET /api/v1/projects/{project_id}`** - Fetches detailed information for a specific project by ID
- **`PATCH /api/v1/projects/{project_id}`** - Updates project metadata and properties for an existing project
- **`DELETE /api/v1/projects/{project_id}`** - Removes a project and its associated data from the database

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

### Quick Test Script
```bash
cd backend
python3.12 tests/integration/test_endpoints.py

# With audio file:
python3.12 tests/integration/test_endpoints.py --audio /path/to/audio.mp3
```

### Microphone Testing (Whisper Transcription)
Test the complete workflow: Record from microphone → Transcribe → Parse
```bash
cd backend
source venv/bin/activate
python tests/integration/test_full_workflow.py
# Or test transcription only:
python tests/integration/test_whisper_mic.py
```

### Manual Testing
1. Start the backend server
2. Open http://localhost:8000/docs
3. Use Swagger UI to test endpoints interactively

### Health Check
```bash
curl http://localhost:8000/health/detailed
```

## Deployment

### Branching Strategy

| Branch | Purpose | Environment | Auto-Deploy |
|--------|---------|-------------|-------------|
| `main` | Production | Production | ✅ On merge |
| `staging` | QA/Pre-Prod | Staging | ✅ On push |
| `feature/*` | Development | Local/PR | ❌ Manual |

### CI/CD Pipeline

**Frontend (Vercel)**
- Auto-deploys on push to `staging` or `main`
- Preview deployments for PRs
- **Root Directory Configuration**: The project uses a monorepo structure with frontend in `frontend/` subdirectory. The root `vercel.json` is configured to handle this automatically. If you still see build errors, verify in Vercel Dashboard → Settings → General → Root Directory is set to `frontend/` (or leave empty if using root vercel.json)
- **Sharing Preview Deployments**: Use Vercel's "Shareable Links" feature to share preview URLs with external collaborators (designers, stakeholders) who don't have Vercel accounts. Go to Vercel Dashboard → Deployments → Select deployment → Click "Share" → Select "Anyone with the link"

**Backend (Render)**
- Auto-deploys via GitHub Actions
- Health checks after deployment
- Multi-environment support (staging/production)

### GitHub Secrets (Required for CI/CD)

Add these in: **Settings** → **Secrets and variables** → **Actions**

**Backend:**
- `RENDER_API_KEY`
- `RENDER_SERVICE_ID_STAGING`
- `RENDER_SERVICE_ID_PRODUCTION`
- `RENDER_STAGING_URL`
- `RENDER_PRODUCTION_URL`
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SENTRY_DSN` (optional)

**Frontend:**
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

### Environment URLs

**Staging:**
- Frontend: `https://krafzen-ai-staging.vercel.app`
- Backend: `https://krafzen-staging.onrender.com`

**Production:**
- Frontend: `https://app.krafzen.com` (when configured)
- Backend: `https://api.krafzen.com` (when configured)

## Monitoring & Observability
- **Error Tracking**: Sentry integration
- **Health Monitoring**: Response time and uptime tracking
- **Performance**: <1s response time target
- **Uptime**: >99% availability target

## Contributing

### Branch Strategy

| Branch Name | Purpose |
|-------------|---------|
| `main` | Production-ready code |
| `staging` | Integration testing & pre-demo |
| `feature/*` | Active development branch |

### Commit Message Format

We follow **[Conventional Commits](https://www.conventionalcommits.org/)**:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: new feature
- `fix`: bug fix
- `chore`: setup or minor update
- `refactor`: code improvement
- `style`: UI or CSS updates
- `docs`: documentation updates

### Development Workflow

```bash
# Checkout staging
git checkout staging
git pull origin staging

# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/your-feature
# Create Pull Request to staging branch
```

### Testing

**Backend:**
```bash
cd backend
pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm test
npm run test:ui  # UI mode
```

### Code Style

- **Backend**: Follow PEP 8, use type hints
- **Frontend**: TypeScript, ESLint, Prettier
- Write meaningful commit messages
- Add tests for new features

## Troubleshooting

### Backend Issues

**Server won't start:**
- Check if port 8000 is in use: `lsof -i :8000`
- Verify Python version: `python3.12 --version`
- Check dependencies: `pip list`

**OpenAI errors:**
- Verify `OPENAI_API_KEY` is set in `.env`
- Check API key is valid and has credits
- Restart server after updating `.env`

**Supabase errors:**
- Verify credentials in `.env`
- Check Supabase project is active
- App will start without Supabase, but DB features won't work

### Frontend Issues

**Build errors:**
- Clear cache: `rm -rf .next node_modules`
- Reinstall: `npm install`
- Check Node version: `node --version` (should be 20+)

**Environment variables not working:**
- Ensure variables start with `NEXT_PUBLIC_`
- Restart dev server after changing `.env.local`

## Documentation
- **Deployment Guide**: `backend/DEPLOYMENT.md`
- **Deployment Strategy**: `docs/DEPLOYMENT_STRATEGY.md`
- **Branch Protection**: `.github/BRANCH_PROTECTION.md`
- **API Documentation**: Available at `/docs` endpoint

## License
Proprietary - KRAFZEN AI

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs (when running locally)
- **OpenAI API Keys**: https://platform.openai.com/api-keys
- **Supabase Dashboard**: https://app.supabase.com
- **Sentry Dashboard**: https://sentry.io
- **Render Dashboard**: https://dashboard.render.com
- **Vercel Dashboard**: https://vercel.com/dashboard

## 🧭 Contributing Guidelines – Krafzen AI Frontend (Next.js)

### 🌿 Branch Strategy

| Branch Name | Purpose |
|--------------|----------|
| `main`       | Production-ready code |
| `staging`    | Integration testing & pre-demo before merging into main |
| `feature/*`   | Active branch on to add new feature |

### ✍️ Commit Message Format

We follow **[Conventional Commits](https://www.conventionalcommits.org/)**.

**Format:**
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]

```

**Types:**
- `feat`: new feature (e.g. `feat: add voice recording UI`)
- `fix`: bug fix (e.g. `fix: handle Supabase auth refresh`)
- `chore`: setup or minor update (e.g. `chore: setup Sentry + PostHog`)
- `refactor`: code improvement
- `style`: UI or CSS updates
- `docs`: documentation updates

### 🚀 Development Workflow

```bash
# Pre-checks tests and linting error
npm run lint
npm run test

# Check for staging branch locally 
git checkout staging

# Fetch the fresh changes from staging branch
git pull origin staging

# Create branch feature/details to make a meaningful commit
git checkout -b feature/setup

# Make your changes and commit
git add .
git commit -m "feat: add new component"

# Push to your fork
git push origin feature/setup

# Create a Pull Request to staging branch
# Do not merge the pull request untill someone from the team reviews it
```

### 🧪 Testing

```bash
# Run tests
npm test

# Run tests in UI mode
npm run test:ui

```

### 📝 Code Style

- Use TypeScript for all new files
- Follow ESLint rules
- Use Prettier for formatting
- Write meaningful commit messages
- Add tests for new features
