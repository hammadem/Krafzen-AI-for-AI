# KRAFZEN AI - SaaS Platform for CAD/BIM Generation

## Project Overview
KRAFZEN AI is an AI-powered SaaS platform that converts voice and text instructions into CAD/BIM files (DXF, DWG, Revit, etc.).

## Tech Stack (MVP)

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Hosting**: Render.com (Multi-environment: Staging + Production)
- **Database**: Supabase (PostgreSQL)
- **AI Services**: OpenAI Whisper (transcription) + GPT-4 (parsing)
- **CAD Engine**: ezdxf (Python library)
- **CI/CD**: GitHub Actions with branch protection
- **Monitoring**: Sentry (error tracking) + Health checks
- **Environment**: Multi-environment support (dev/staging/production)

### Frontend
- **Framework**: Next.js 14+ with Tailwind CSS
- **Hosting**: Vercel (Multi-environment)
- **State Management**: React Context API
- **Auth**: Supabase (JWT sessions)
- **Monitoring**: Sentry + PostHog
- **Testing**: Vitest

## Project Structure
```
KRAFZEN-AI-/
├── README.md                    # This file
|
├── backend/                     # FastAPI backend
│   ├── main.py                  # Application entry point
│   ├── requirements.txt         # Python dependencies
│   ├── render.yaml              # Multi-environment deployment config
│   ├── DEPLOYMENT.md            # Backend deployment guide
│   └── app/                     # Application modules
|
├── frontend/                    # Next.js frontend
|   ├── components/              # React components
│   ├── app/                     # App structure
|   |   ├── page.tsx             # Home page
|   |   ├── layout.tsx           # Root layout
|   |   └── globals.css          # Global styles
|   ├── lib/                     # Helper functions  
|   ├── public/                  # Static assets and images 
|
├── .github/                     # GitHub Actions & configs
│   ├── workflows/               # CI/CD pipelines
│   ├── CODEOWNERS               # Code ownership rules
│   └── BRANCH_PROTECTION.md     # Branch protection guidelines
└── docs/                        # Project documentation
    ├── DEPLOYMENT_STRATEGY.md   # CTO's deployment strategy
    └── *.pdf                    # Project planning documents
```

## Getting Started

### Prerequisites
- **Python 3.11+** installed on your system
- **Node.js 18+** and npm installed
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
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Step 2: Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 3: Configure environment variables**
```bash
# Copy the example env file to create your .env file
# Note: This is a manual step - copy the file and update with your actual values
cp env.example .env

# Edit .env with your preferred text editor and add your actual API keys:
# - OPENAI_API_KEY (required for transcription)
# - SUPABASE_URL and SUPABASE_KEY (required for database)
# - SENTRY_DSN (optional, for error tracking)
# - Other optional variables as needed
```

**Important**: The `.env` file is gitignored and will not be committed to the repository. Always use `env.example` as a template and never commit your actual `.env` file with real secrets.

**Step 4: Start the backend server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
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

**Step 2: Start the development server**
```bash
npm run dev
```

The frontend will be available at:
- **Application**: http://localhost:3000

#### 4. Running Both Servers

You'll need to run both the backend and frontend servers simultaneously. Open two terminal windows:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### API Endpoints

- **Health Check**: `GET /health/`
- **Detailed Health**: `GET /health/detailed`
- **API Documentation**: `GET /docs` (Swagger UI)
- **Transcription**: `POST /api/v1/transcribe` (placeholder)

### Environment Variables

The backend requires a `.env` file in the `backend/` directory. Copy `backend/env.example` to `backend/.env` and configure:

```bash
# Required
ENVIRONMENT=development
OPENAI_API_KEY=your_key_here          # Required for AI features
SUPABASE_URL=your_url_here            # Required for database
SUPABASE_KEY=your_key_here            # Required for database

# Optional
SENTRY_DSN=your_dsn_here              # For error tracking
RENDER_SERVICE_ID_PRODUCTION=         # For production deployments
RENDER_SERVICE_ID_STAGING=            # For staging deployments

# CORS Origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,https://*.vercel.app,https://staging.krafzen.com,https://app.krafzen.com
```

**Note**: The backend will start even without all environment variables configured, but some features (like transcription) will require valid API keys.

## Deployment

### Staging Environment
- **Branch**: `staging`
- **Backend URL**: `krafzen-staging.onrender.com`
- **Frontend URL**: `staging.krafzen.com`
- **Auto-deploy**: On push to `staging` branch

### Production Environment
- **Branch**: `main`
- **Backend URL**: `api.krafzen.com` (when configured)
- **Frontend URL**: `app.krafzen.com`
- **Auto-deploy**: On merge to `main` branch

### CI/CD Pipeline
- **Testing**: Automated tests on PR creation
- **Linting**: Code quality checks
- **Deployment**: Automatic deployment to appropriate environment
- **Health Checks**: Post-deployment verification

## Monitoring & Observability
- **Error Tracking**: Sentry integration
- **Health Monitoring**: Response time and uptime tracking
- **Performance**: <1s response time target
- **Uptime**: >99% availability target

## Documentation
- **Deployment Guide**: `backend/DEPLOYMENT.md`
- **Deployment Strategy**: `docs/DEPLOYMENT_STRATEGY.md`
- **Branch Protection**: `.github/BRANCH_PROTECTION.md`
- **API Documentation**: Available at `/docs` endpoint

## License
Proprietary - KRAFZEN AI

---

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
# Check for staging branch locally 
git checkout staging

# Fetch the fresh changes from staging branch
git pull upstream staging

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