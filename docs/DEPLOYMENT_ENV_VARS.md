# Environment Variables & Deployment Guide

This project uses a unified `.env` file at the root of the repository. This file is **ignored by Git** for security.

For local development, we use symlinks to make this file accessible to both the frontend and backend:
*   `frontend/.env.local` -> `../.env`
*   `backend/.env` -> `../.env`

## 🚀 Deployment

When deploying to cloud platforms like Vercel (Frontend) and Render (Backend), these local symlinks do **not** work. You must manually add the environment variables to each platform's dashboard.

### 1. Frontend Variables (Vercel)

Go to **Vercel Dashboard** > **Settings** > **Environment Variables** and add the following:

| Variable Name | Description |
| :--- | :--- |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase Project URL. |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase Anonymous Key. |
| `NEXT_PUBLIC_API_URL` | The URL of your deployed Backend (e.g., on Render). |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe Publishable Key. |
| `NEXT_PUBLIC_CALENDLY_URL` | URL for Calendly scheduling. |

> **Note:** Variables starting with `NEXT_PUBLIC_` are exposed to the browser.

### Supabase Auth (redirects for production & staging)

If login redirects to **localhost** on production or staging, fix it in **Supabase Dashboard**:

1. Go to [Supabase Dashboard](https://supabase.com/dashboard) → your project → **Authentication** → **URL Configuration**.
2. **Site URL:** Set to your primary app URL (e.g. `https://www.krafzen.com` for production, or leave as-is if you use Redirect URLs for each env).
3. Under **Redirect URLs**, add **all** environments (one per line):
   - Production: `https://www.krafzen.com/**`, `https://krafzen.com/**`
   - Staging: `https://staging.krafzen.com/**`
   - Local: `http://localhost:3000/**`
4. Save. OAuth and magic-link redirects will then go back to the correct origin (the app uses `window.location.origin`, so staging.krafzen.com → staging, www.krafzen.com → production).

### 2. Backend Variables (Render / Cloud)

Go to **Render Dashboard** > **Settings** > **Environment** and add the following:

| Variable Name | Description |
| :--- | :--- |
| `ENVIRONMENT` | Set to `production`. |
| `PORT` | Set to `8000`. |
| `SUPABASE_URL` | Your Supabase Project URL. |
| `SUPABASE_KEY` | Your Supabase Service Role Key (or Anon Key depending on usage, usually Service). |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase Service Role Key. |
| `SUPABASE_JWT_SECRET` | Secret for verifying Supabase JWTs. |
| `SUPABASE_PROJECT_ID` | Your Supabase Project ID. |
| `GEMINI_API_KEY` | API Key for Google Gemini. |
| `USE_GEMINI_FOR_IMAGE` | `true` or `false`. |
| `HF_TOKEN` | Hugging Face Access Token. |
| `HF_ENDPOINT_URL` | Endpoint for the CAD LLM. |
| `DXF_GENERATION_METHOD` | `local` or `api`. |
| `STRIPE_SECRET_KEY` | Stripe Secret Key. |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook Secret. |
| `STRIPE_PRICE_ID_100_MINS` | Stripe Price ID. |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed frontend URLs (e.g., `https://your-vercel-app.vercel.app`). |

## 🛠 Local Setup (If creating a fresh clone)

If you clone this repo anew, run the setup script to link the env files:

```bash
# In the root directory
ln -s .env frontend/.env.local
ln -s .env backend/.env
```


### 3. Enterprise USA data-residency routing (required for sovereign tenants)

Set these **backend-only secrets** on the dedicated US worker and API service:

| Variable | Purpose |
| :--- | :--- |
| `SUPABASE_URL_US` | HTTPS REST API URL for a dedicated US Supabase project (different from `SUPABASE_URL`). |
| `SUPABASE_SERVICE_ROLE_KEY_US` | Service role key for that US project. Never expose to browser/frontend. |
| `SUPABASE_STORAGE_KEY_US` | Credentials used for US storage integration. |
| `SUPABASE_STORAGE_BUCKET_US` | US-region object bucket. |
| `CURRENT_REGION_CODE` | Set to `us` **only** for verified US workers. |
| `WORKER_POOL_NAME` | Must match `US_WORKER_POOL` for the sovereign queue. |

The optional `SUPABASE_DATABASE_URL_US` is a PostgreSQL connection string, **not** a valid
`create_client()` REST URL. Missing regional configuration, invalid residency state,
and routing failures now block the operation (HTTP 503) rather than falling back to
central infrastructure.

**Deployment gate:** before enabling residency for customers, independently verify the
actual physical regions for Supabase databases/storage, processing, backups, logs, AI
inference providers, analytics, and third-party data processors. Routing code alone
is **not** evidence of a complete US-only data residency guarantee.
