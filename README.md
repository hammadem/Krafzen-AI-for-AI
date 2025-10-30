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

### Frontend (for reference)
- **Framework**: Next.js with Tailwind CSS
- **Hosting**: Vercel (Multi-environment)
- **State Management**: React Context API

## Team
- **Kiruthika Ponnan** - Tech Lead / Architect
- **Sonu** - Frontend Lead
- **Krishnarajan V** - Full Stack Developer
- **Laxmi Pranitha Muskula** - Data/Systems Analyst
- **Ashwani Kumar** - Jr. Developer / QA Engineer

## ✅ Week 1-2 Completed (Kiruthika)
- ✅ Configure FastAPI backend on Render (Multi-environment)
- ✅ Set up CI/CD via GitHub Actions with branch protection
- ✅ Ensure API response time <1s and uptime >99% monitoring
- ✅ Implement Sentry error monitoring
- ✅ Create comprehensive deployment strategy
- ✅ Set up GitHub branch protection rules

## Project Structure
```
KRAFZEN-AI-/
├── README.md                    # This file
├── backend/                     # FastAPI backend
│   ├── main.py                  # Application entry point
│   ├── requirements.txt         # Python dependencies
│   ├── render.yaml             # Multi-environment deployment config
│   ├── DEPLOYMENT.md           # Backend deployment guide
│   └── app/                    # Application modules
├── .github/                    # GitHub Actions & configs
│   ├── workflows/              # CI/CD pipelines
│   ├── CODEOWNERS             # Code ownership rules
│   └── BRANCH_PROTECTION.md   # Branch protection guidelines
└── docs/                      # Project documentation
    ├── DEPLOYMENT_STRATEGY.md # CTO's deployment strategy
    └── *.pdf                  # Project planning documents
```

## Getting Started

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### API Endpoints
- **Health Check**: `GET /health/`
- **Detailed Health**: `GET /health/detailed`
- **API Documentation**: `GET /docs` (Swagger UI)
- **Transcription**: `POST /api/v1/transcribe` (placeholder)

### Environment Variables
Copy `backend/env.example` to `backend/.env` and configure:
```bash
ENVIRONMENT=development
OPENAI_API_KEY=your_key_here
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_key_here
SENTRY_DSN=your_dsn_here
```

## Deployment

### Staging Environment
- **Branch**: `staging`
- **URL**: `krafzen-staging.onrender.com`
- **Auto-deploy**: On push to `staging` branch

### Production Environment
- **Branch**: `main`
- **URL**: `api.krafzen.com` (when configured)
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

