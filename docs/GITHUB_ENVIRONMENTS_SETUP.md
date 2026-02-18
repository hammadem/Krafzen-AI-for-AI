# GitHub Environments: Staging & Production

This repo uses **GitHub Environments** so staging and production use separate secrets and (optionally) protection rules.

## Branch → Environment

| Branch    | Frontend workflow           | Backend workflow   | GitHub environment used |
|-----------|-----------------------------|--------------------|---------------------------|
| **staging** | `staging-frontend.yaml`     | `deploy-backend.yml` (staging job) | **staging**   |
| **main**    | `main-frontend.yaml`        | `deploy-backend.yml` (production job) | **Production** |

- Push to **staging** → deploys use the **staging** environment’s secrets (Vercel preview, Render staging).
- Push to **main** → deploys use the **Production** environment’s secrets (Vercel production, Render production).

## Environments in GitHub

In **Settings → Environments** you should have at least:

1. **staging** – used when pushing to `staging` (and `feature/*` for frontend).
2. **Production** – used when pushing to `main`.  
   If you use a different name (e.g. `Production – krafzen-ai-production`), set the same name in `main-frontend.yaml` and `deploy-backend.yml` under `environment:`.

## Secrets per environment

### Staging environment

Used by: staging frontend deploy, backend staging deploy.

| Secret | Description |
|--------|-------------|
| `VERCEL_TOKEN` | Vercel API token (can be same as production if same project) |
| `VERCEL_ORG_ID` | Vercel team/org ID |
| `VERCEL_PROJECT_ID` | Vercel project ID (staging project if you use a separate one) |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase URL (build) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key (build) |
| `NEXT_PUBLIC_API_URL` | Staging API, e.g. `https://backend.staging.krafzen.com` |
| `RENDER_API_KEY` | Render API key (for backend deploy) |
| `RENDER_SERVICE_ID_STAGING` | Render service ID for staging backend |
| `RENDER_STAGING_URL` | Staging backend URL, e.g. `https://backend.staging.krafzen.com` |

### Production environment

Used by: production frontend deploy, backend production deploy.

| Secret | Description |
|--------|-------------|
| `VERCEL_TOKEN` | Vercel API token |
| `VERCEL_ORG_ID` | Vercel team/org ID |
| `VERCEL_PROJECT_ID` | Vercel project ID (production) |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase URL (build) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key (build) |
| `NEXT_PUBLIC_API_URL` | Production API, e.g. `https://backend.krafzen.com` |
| `RENDER_API_KEY` | Render API key |
| `RENDER_SERVICE_ID_PRODUCTION` | Render service ID for production backend |
| `RENDER_PRODUCTION_URL` | Production backend URL, e.g. `https://backend.krafzen.com` |

## One Vercel project vs two

- **One project (recommended):** Same `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` in both environments. Staging branch deploys as preview; main deploys as production (`--prod`).
- **Two projects:** Use staging project IDs in the **staging** environment and production project IDs in the **Production** environment.

## Optional: protection rules

For **Production** you can add:

- **Required reviewers** – require approval before a production deploy.
- **Wait timer** – delay before deployment.

Configure under **Settings → Environments → Production → Protection rules**.

## Domains

| Environment | Frontend | Backend |
|-------------|----------|---------|
| Staging     | https://staging.krafzen.com, https://www.staging.krafzen.com | https://backend.staging.krafzen.com |
| Production  | https://krafzen.com         | https://backend.krafzen.com         |

See **docs/ENV_DOMAINS.md** for env files and Supabase redirect URLs.

## CORS (backend)

The backend allows origins from `ALLOWED_ORIGINS` (env) or its default list, which includes `https://staging.krafzen.com`, `https://www.staging.krafzen.com`, and production domains. If your frontend uses a different URL (e.g. a Vercel preview), set **ALLOWED_ORIGINS** on the Render service to a comma-separated list including that origin, or the CORS preflight will fail and API calls from the browser will be blocked.

## Backend 401 Unauthorized (Render)

If the frontend gets **401 (Unauthorized)** on all API calls (e.g. `/api/v1/users/profile`, `/api/v1/payments/subscription-status`, `/api/v1/chat/history`), the backend cannot validate the Supabase JWT. Set these on the **Render** service (Dashboard → Service → Environment) so they match the **same Supabase project** the frontend uses:

| Variable | Where to get it | Required for |
|----------|-----------------|--------------|
| **SUPABASE_JWT_SECRET** | Supabase Dashboard → Project Settings → API → **JWT Secret** | Verifying the Bearer token signature |
| **SUPABASE_PROJECT_ID** | Supabase project ref (e.g. from URL `https://<project_ref>.supabase.co`) | Verifying the token issuer |

- **Staging backend:** Use the same Supabase project as your staging frontend (same `NEXT_PUBLIC_SUPABASE_URL` / project ref). Copy **JWT Secret** and **Project ID** from that Supabase project.
- **Production backend:** Use the same Supabase project as your production frontend.

If either is missing or wrong on Render, every authenticated request will return 401. Until these are set on the staging backend, users may also be unable to log out in staging; the frontend now clears local state and redirects even if Supabase `signOut()` fails, but setting **SUPABASE_JWT_SECRET** and **SUPABASE_PROJECT_ID** on Render is required for full auth and logout behavior.

**If Render logs show "JWT decode error: Signature verification failed":** The value of **SUPABASE_JWT_SECRET** on that Render service does not match the Supabase project that issued the token. For the **staging** backend, use the JWT Secret from the **same** Supabase project your **staging** frontend uses (the one in `NEXT_PUBLIC_SUPABASE_URL` for staging). Do not use the production Supabase JWT Secret on the staging backend. In Supabase Dashboard: open that project → Project Settings → API → copy **JWT Secret** (not the anon key), paste into Render with no extra spaces, then redeploy.
