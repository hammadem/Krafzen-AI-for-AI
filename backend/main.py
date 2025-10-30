"""
KRAFZEN AI - Main FastAPI Application
Entry point for the backend service
"""

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, transcriber
from app.core.config import settings

# Initialize Sentry for error monitoring
if settings.SENTRY_DSN and settings.ENVIRONMENT != "development":
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )

app = FastAPI(
    title="KRAFZEN AI API",
    description="AI-powered CAD/BIM generation from voice and text",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(transcriber.router, prefix="/api/v1", tags=["Transcriber"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "KRAFZEN AI API",
        "version": "0.1.0",
        "status": "running"
    }

