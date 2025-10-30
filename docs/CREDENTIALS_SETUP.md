# KRAFZEN AI - Credentials Setup Guide

## 🔐 Required Credentials

### **1. OpenAI API Key**
- **Purpose**: AI transcription and processing
- **Where to get**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Required for**: Backend AI functionality

### **2. Supabase Credentials**
- **Purpose**: Database and authentication
- **Where to get**: [Supabase Dashboard](https://supabase.com/dashboard)
- **Required for**: Database operations, user management

### **3. Sentry DSN**
- **Purpose**: Error monitoring and performance tracking
- **Where to get**: [Sentry.io](https://sentry.io)
- **Required for**: Production error monitoring

### **4. Render Service IDs**
- **Purpose**: CI/CD deployment automation
- **Where to get**: Render Dashboard → Service Settings
- **Required for**: Automated deployments

## 🛡️ Security Best Practices

### **Local Development (.env file)**
```bash
# Create .env file in backend/ directory
cp backend/env.example backend/.env

# Edit .env with your credentials
nano backend/.env
```

**Example .env file:**
```bash
# Environment
ENVIRONMENT=development

# OpenAI API
OPENAI_API_KEY=sk-your-openai-key-here

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Server Configuration
PORT=8000
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,https://*.vercel.app
```

### **Production Security (GitHub Secrets)**
Never commit credentials to git! Use GitHub Secrets:

#### **Required GitHub Secrets:**
1. `OPENAI_API_KEY`
2. `SUPABASE_URL`
3. `SUPABASE_KEY`
4. `SENTRY_DSN`
5. `RENDER_API_KEY`
6. `RENDER_SERVICE_ID_STAGING`
7. `RENDER_SERVICE_ID_PRODUCTION`
8. `RENDER_STAGING_URL`
9. `RENDER_PRODUCTION_URL`

#### **How to Add GitHub Secrets:**
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its value

## 📋 Step-by-Step Setup

### **Step 1: OpenAI Setup**
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create account
3. Click **"Create new secret key"**
4. Copy the key (starts with `sk-`)
5. Add to GitHub Secrets as `OPENAI_API_KEY`

### **Step 2: Supabase Setup**
1. Visit [Supabase Dashboard](https://supabase.com/dashboard)
2. Create new project or select existing
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY`
5. Add both to GitHub Secrets

### **Step 3: Sentry Setup**
1. Visit [Sentry.io](https://sentry.io)
2. Create new project (FastAPI/Python)
3. Copy the DSN from project settings
4. Add to GitHub Secrets as `SENTRY_DSN`

### **Step 4: Render Setup**
1. Visit [Render Dashboard](https://dashboard.render.com)
2. Create two web services:
   - `krafzen-api-staging` (branch: staging)
   - `krafzen-api-prod` (branch: main)
3. Get service IDs from each service settings
4. Add to GitHub Secrets:
   - `RENDER_SERVICE_ID_STAGING`
   - `RENDER_SERVICE_ID_PRODUCTION`
   - `RENDER_STAGING_URL`
   - `RENDER_PRODUCTION_URL`

### **Step 5: Render API Key**
1. Go to Render Dashboard → Account Settings
2. Click **API Keys**
3. Generate new API key
4. Add to GitHub Secrets as `RENDER_API_KEY`

## 🔒 Security Checklist

- [ ] `.env` file added to `.gitignore`
- [ ] No credentials in code or config files
- [ ] All secrets added to GitHub Secrets
- [ ] Different credentials for staging vs production
- [ ] Regular credential rotation planned
- [ ] Access logs monitored

## 🚨 Important Security Notes

1. **Never commit `.env` files**
2. **Use different credentials for each environment**
3. **Rotate credentials regularly**
4. **Monitor access logs**
5. **Use least privilege principle**
6. **Enable 2FA on all accounts**

## 🧪 Testing Credentials

### **Local Testing**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
curl http://localhost:8000/health/detailed
```

### **Verify in Health Check**
- Database should show "connected" when Supabase is configured
- Sentry should show "enabled" when DSN is configured
- Environment should match your setup

## 📞 Support

If you need help with any credential setup:
- **OpenAI**: [OpenAI Help Center](https://help.openai.com)
- **Supabase**: [Supabase Documentation](https://supabase.com/docs)
- **Sentry**: [Sentry Documentation](https://docs.sentry.io)
- **Render**: [Render Documentation](https://render.com/docs)
