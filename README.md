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
├── backend/                     # FastAPI backend
│   ├── main.py                  # Application entry point
│   ├── requirements.txt         # Python dependencies
│   ├── render.yaml             # Multi-environment deployment config
│   ├── DEPLOYMENT.md           # Backend deployment guide
│   └── app/                    # Application modules
├── app/                         # Next.js frontend
│   ├── page.tsx                 # Home page
│   ├── layout.tsx               # Root layout
│   └── globals.css              # Global styles
├── components/                  # React components
│   ├── Hero.tsx                 # Hero section
│   ├── Navbar.tsx               # Navigation
│   └── ui/                      # UI components
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

### Frontend Setup
```bash
npm install
npm run dev
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
```

### 🧪 Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### 📝 Code Style

- Use TypeScript for all new files
- Follow ESLint rules
- Use Prettier for formatting
- Write meaningful commit messages
- Add tests for new features