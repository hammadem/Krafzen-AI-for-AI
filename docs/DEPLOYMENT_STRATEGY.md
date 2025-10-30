# KRAFZEN AI – MVP Deployment & CI/CD Overview

## Overview
KRAFZEN AI runs on a lean, low-cost stack designed for speed, simplicity, and reliability.  
This document outlines our development, review, and deployment process for the MVP.

---

## Tech Stack

| Layer | Technology | Host | Notes |
|--------|-------------|------|-------|
| **Frontend** | Next.js (React) | Vercel | Auto-deployed on push |
| **Backend** | FastAPI (Python) | Render | For Whisper + DXF generation |
| **Database** | Supabase (PostgreSQL) | Supabase | Auth, storage, DB |
| **Infra** | GitHub Actions | GitHub | CI/CD automation |
| **Domain & SSL** | Cloudflare | — | DNS + HTTPS |
| **Monitoring** | Sentry + GA4 + PostHog | — | Error + usage analytics |

---

## Branching & Environments

| Branch | Purpose | Environment | URL |
|---------|----------|-------------|-----|
| `main` | Production | Vercel + Render | `app.krafzen.com`, `api.krafzen.com` |
| `staging` | QA / Pre-Prod | Vercel + Render | `staging.krafzen.com`, `krafzen-staging.onrender.com` |
| `feature/*` | Dev work | Local / PR previews | — |

---

## Git Workflow

1. Create a feature branch from `main`
2. Push commits and open a Pull Request → **`staging`**
3. Reviewer approves and merges → staging auto-deploys
4. Verify app on staging
5. Reviewer merges `staging` → `main` → auto-deploy to production

---

## GitHub Rules

- Protect `main` and `staging`
- Require 1 review approval
- Block direct pushes
- All CI checks must pass

---

## CI/CD Configuration

### Frontend – Vercel

- Two projects:
  - `krafzen-frontend-staging` → branch: `staging`
  - `krafzen-frontend-prod` → branch: `main`
- Auto-deploy on push to corresponding branch

```yaml
on: push: [main, staging]
jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npx vercel --token ${{ secrets.VERCEL_TOKEN }} --prod --confirm
