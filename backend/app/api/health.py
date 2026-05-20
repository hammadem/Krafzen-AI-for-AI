"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime
import time
from app.services.supabase_service import supabase_service
from app.core.config import settings
from app.db.supabase_client import db

router = APIRouter()

@router.get("")
async def health_check():
    """Basic health check endpoint (Render probes GET /health)."""
    try:
        result = db.table("projects").select("id", count="exact").execute()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "KRAFZEN AI Backend",
            "db_project_count": result.count,
        }
    except Exception:
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "KRAFZEN AI Backend",
            "db": "unreachable",
        }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system info"""
    start_time = time.time()
    
    # Test Supabase connection
    supabase_status = supabase_service.test_connection()
    
    # Calculate response time
    response_time = round((time.time() - start_time) * 1000, 2)  # in milliseconds
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "KRAFZEN AI Backend",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "response_time_ms": response_time,
        "uptime": "N/A",  # TODO: Add actual uptime tracking
        "dependencies": {
            "database": "connected" if supabase_status["connected"] else "disconnected",
            "openai": "pending"  # TODO: Add OpenAI API check
        },
        "supabase": supabase_status,
        "monitoring": {
            "sentry_enabled": bool(settings.SENTRY_DSN and settings.ENVIRONMENT != "development"),
            "environment": settings.ENVIRONMENT
        },
        "cors": {
            "allowed_origins": getattr(settings, "ALLOWED_ORIGINS_LIST", []),
            "allowed_origins_raw": getattr(settings, "ALLOWED_ORIGINS", "")
        }
    }

