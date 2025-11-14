# GitHub Secrets Configuration Guide

## Overview
This guide explains which environment variables from `backend/.env` should be configured as GitHub Secrets for CI/CD workflows.

## 🔐 **MUST be Secrets** (Sensitive/Private)

These contain sensitive credentials and **must** be stored as GitHub Secrets:

### Required for Production/Staging Deployments:
1. **`SUPABASE_URL`** - Your Supabase project URL
   - Example: `https://xxxxx.supabase.co`
   - Used for: Database connections

2. **`SUPABASE_ANON_KEY`** - Supabase anonymous key
   - Used for: Client-side operations
   - Get from: Supabase Dashboard → Settings → API

3. **`SUPABASE_SERVICE_ROLE_KEY`** - Supabase service role key ⚠️ **VERY SENSITIVE**
   - Used for: Server-side operations with elevated privileges
   - Get from: Supabase Dashboard → Settings → API
   - **Never expose this in logs or client-side code**

4. **`OPENAI_API_KEY`** - OpenAI API key
   - Used for: AI transcription and parsing features
   - Get from: https://platform.openai.com/api-keys

5. **`SENTRY_DSN`** - Sentry error tracking DSN (optional but recommended)
   - Used for: Error monitoring and tracking
   - Get from: https://sentry.io

### Already Configured:
- `RENDER_API_KEY` ✅ (already in secrets)
- `RENDER_SERVICE_ID_PRODUCTION` ✅ (already in secrets)
- `RENDER_SERVICE_ID_STAGING` ✅ (already in secrets)
- `RENDER_STAGING_URL` ✅ (already in secrets)
- `RENDER_PRODUCTION_URL` ✅ (already in secrets)

## ⚙️ **Optional/Not Required for Tests** (Can be set in workflow)

These can be set directly in workflow files or have defaults:

1. **`ENVIRONMENT`** - `development`, `staging`, or `production`
   - Default: `development`
   - Can be set in workflow: `env: ENVIRONMENT: staging`

2. **`DEBUG`** - Debug mode (True/False)
   - Default: `False`
   - Can be set in workflow if needed

3. **`PORT`** - Server port
   - Default: `8000`
   - Usually handled by deployment platform

4. **`ALLOWED_ORIGINS`** - CORS allowed origins
   - Has defaults in code
   - Can be set in workflow if needed

5. **`FRONTEND_URL`** - Frontend URL
   - Default: `http://localhost:3000`
   - Can be set in workflow

6. **`LOG_LEVEL`** - Logging level
   - Default: `INFO`
   - Can be set in workflow if needed

## 📝 **Current Test Behavior**

**Good news:** Your tests are designed to work **without** Supabase credentials! 

- ✅ Unit tests pass without secrets (they mock/validate structure)
- ✅ Integration tests pass without secrets (they test endpoints, not DB operations)
- ✅ Health checks return "degraded" status when credentials are missing (expected)

**You only need secrets if:**
- Running integration tests that actually hit the database
- Deploying to staging/production environments
- Testing full end-to-end workflows

## 🚀 **How to Add Secrets to GitHub**

1. Go to your repository on GitHub
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Add each secret with the exact name (case-sensitive):
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `OPENAI_API_KEY`
   - `SENTRY_DSN` (optional)

## 🔧 **Using Secrets in Workflows**

Secrets are automatically available in GitHub Actions. Example:

```yaml
env:
  SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
  SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
```

## ⚠️ **Important Notes**

1. **Never commit secrets** to the repository
2. **Never log secrets** in workflow output
3. **Use different keys** for staging and production
4. **Rotate keys regularly** for security
5. **Service Role Key** has full database access - treat it as highly sensitive

## 📋 **Recommended Setup**

### For CI/CD Tests (Current Setup - No Changes Needed):
- ✅ Tests work without secrets
- ✅ Secrets are optional for test workflows

### For Staging/Production Deployments:
- ✅ Add all required secrets listed above
- ✅ Use environment-specific values
- ✅ Configure in Render.com or your deployment platform

## 🔍 **Verification**

To verify secrets are set correctly:
1. Check workflow logs (secrets are masked automatically)
2. Verify deployment health checks pass
3. Check that database operations work in deployed environments

