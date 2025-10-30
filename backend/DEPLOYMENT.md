# KRAFZEN AI Backend Deployment Guide

## 🚀 Multi-Environment Render Deployment

### Prerequisites
1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Ensure your code is pushed to GitHub
3. **Environment Variables**: Get your API keys ready
4. **Sentry Account**: Set up error monitoring at [sentry.io](https://sentry.io)

### Step 1: Create Staging and Production Services on Render

#### Staging Service
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the repository: `KRAFZEN-AI-`

**Staging Settings:**
- **Name**: `krafzen-api-staging`
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `staging`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health/`
- **Auto-Deploy**: `Yes`

#### Production Service
1. Create another service following same steps
2. **Name**: `krafzen-api-prod`
3. **Branch**: `main`
4. All other settings same as staging

### Step 2: Environment Variables

Add these environment variables in both Render services:

#### Staging Environment
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Environment
ENVIRONMENT=staging

# Monitoring
SENTRY_DSN=your_sentry_dsn_here

# Optional (defaults provided)
PORT=8000
DEBUG=False
ALLOWED_ORIGINS=https://staging.krafzen.com,https://*.vercel.app
```

#### Production Environment
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Environment
ENVIRONMENT=production

# Monitoring
SENTRY_DSN=your_sentry_dsn_here

# Optional (defaults provided)
PORT=8000
DEBUG=False
ALLOWED_ORIGINS=https://app.krafzen.com,https://*.vercel.app
```

### Step 3: GitHub Actions Integration

The CI/CD pipeline is configured in `.github/workflows/deploy-backend.yml`.

**Required GitHub Secrets:**
- `RENDER_API_KEY`: Get from Render dashboard → Account Settings → API Keys
- `RENDER_SERVICE_ID_STAGING`: Get from staging service settings
- `RENDER_SERVICE_ID_PRODUCTION`: Get from production service settings
- `RENDER_STAGING_URL`: Your staging service URL
- `RENDER_PRODUCTION_URL`: Your production service URL

### Step 4: Deploy

1. Create services in Render (both staging and production)
2. Configure environment variables for each service
3. Set up GitHub secrets
4. Push to `staging` branch → Auto-deploys to staging
5. Push to `main` branch → Auto-deploys to production

### Step 5: Verify Deployment

Test your deployed APIs:

#### Staging Environment
```bash
# Health check
curl https://krafzen-staging.onrender.com/health/

# Detailed health check
curl https://krafzen-staging.onrender.com/health/detailed

# Root endpoint
curl https://krafzen-staging.onrender.com/
```

#### Production Environment
```bash
# Health check
curl https://api.krafzen.com/health/

# Detailed health check
curl https://api.krafzen.com/health/detailed

# Root endpoint
curl https://api.krafzen.com/
```

### Step 6: Monitoring & Observability

**Health Monitoring:**
- Render provides built-in health checks
- Monitor response times in Render dashboard
- Set up alerts for service downtime

**Error Monitoring:**
- Sentry integration for error tracking
- Real-time error notifications
- Performance monitoring

**API Documentation:**
- Staging: `https://krafzen-staging.onrender.com/docs`
- Production: `https://api.krafzen.com/docs`
- Interactive Swagger UI available

**Branch Protection:**
- Configure branch protection rules for `main` and `staging`
- Require pull request reviews
- Enforce CI/CD pipeline completion

## 🔧 Local Development

### Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Locally
```bash
uvicorn main:app --reload
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8000/health/

# API documentation
open http://localhost:8000/docs
```

## 📊 Performance Targets

- **Response Time**: < 1 second
- **Uptime**: > 99%
- **Health Check**: Every 30 seconds

## 🐛 Troubleshooting

### Common Issues

1. **Build Fails**
   - Check Python version (3.11+)
   - Verify all dependencies in requirements.txt
   - Check build logs in Render dashboard

2. **Service Won't Start**
   - Verify start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Check environment variables
   - Review service logs

3. **Health Check Fails**
   - Ensure health endpoint is accessible
   - Check CORS settings
   - Verify port configuration

### Logs
- **Render Logs**: Available in service dashboard
- **Local Logs**: Check terminal output when running locally

## 📝 Next Steps

After successful deployment:
1. Set up monitoring alerts
2. Configure custom domain (optional)
3. Set up database (Supabase)
4. Implement actual AI features
5. Add authentication

---

**Status**: Ready for deployment ✅
**Last Updated**: Week 1-2