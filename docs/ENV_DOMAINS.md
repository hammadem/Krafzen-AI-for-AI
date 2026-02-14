# Domains & env files (Staging vs Production)

## Domains

| Environment | Frontend (Vercel) | Backend (Render) |
|-------------|-------------------|------------------|
| **Production** | https://krafzen.com | https://backend.krafzen.com |
| **Staging** | https://staging.krafzen.com | https://backend.staging.krafzen.com |
| **Local** | http://localhost:3000 | http://localhost:8000 |

## Which env file to use where

| Where | Use |
|-------|-----|
| **Vercel – Production** | Variables from `.env.production.example` (live Stripe, production API URL, production origins). |
| **Vercel – Staging / Preview** | Variables from `.env.staging.example` (test Stripe, staging API URL, staging origins). |
| **Render – Production backend** | Same as `.env.production.example` (live Stripe, `STRIPE_LIVE_MODE=true`, `ALLOWED_ORIGINS` with krafzen.com). |
| **Render – Staging backend** | Same as `.env.staging.example` (test Stripe, `STRIPE_LIVE_MODE=false`, `ALLOWED_ORIGINS` with staging.krafzen.com). |
| **Local `.env`** | Copy from `.env.example` or `.env.staging.example`; use test Stripe keys or leave Stripe empty for mock. |

## Env file templates

- **`.env.staging.example`** – Staging: test Stripe keys, staging API URL, `STRIPE_LIVE_MODE=false`.
- **`.env.production.example`** – Production: live Stripe keys, production API URL, `STRIPE_LIVE_MODE=true`.

Copy the relevant example and fill in real values in Vercel/Render (do not commit real secrets). Local dev can use `.env` (gitignored) based on `.env.example` or `.env.staging.example`.

## Supabase Redirect URLs

In **Supabase** → **Authentication** → **URL Configuration** → **Redirect URLs**, include:

- `https://www.krafzen.com/**`
- `https://krafzen.com/**`
- `https://staging.krafzen.com/**`
- `http://localhost:3000/**`

Set **Site URL** to `https://krafzen.com` for production.
