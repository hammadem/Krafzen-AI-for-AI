"""KRAFZEN AI - Main FastAPI Application (Final Clean Version)"""

import re
import sentry_sdk
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.config import settings
from app.core.logging_config import init_sentry
from app.utils.error_handler import add_exception_handlers
from app.routes import project_routes, job_routes
from app.api import health, transcriber
from app.db.supabase_client import db


# Initialize Sentry (only outside dev)
if settings.SENTRY_DSN and settings.ENVIRONMENT != "development":
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )


# App initialization
app = FastAPI(
    title="KRAFZEN AI API",
    description="AI-powered CAD/BIM generation from voice and text",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ------------------- CORS -------------------
class WildcardCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        is_allowed = False

        if origin:
            for allowed_origin in getattr(settings, "ALLOWED_ORIGINS_LIST", []):
                if allowed_origin == origin:
                    is_allowed = True
                    break
                elif "*" in allowed_origin:
                    pattern = allowed_origin.replace(".", r"\.").replace("*", ".*")
                    if re.match(pattern, origin):
                        is_allowed = True
                        break

        # Preflight handling
        if request.method == "OPTIONS":
            response = Response()
            if is_allowed:
                response.headers.update({
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "*"
                })
            return response

        # Regular request
        response = await call_next(request)
        if is_allowed:
            response.headers.update({
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "*"
            })
        return response


app.add_middleware(WildcardCORSMiddleware)


# ------------------- Routers -------------------
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(transcriber.router, prefix="/api/v1", tags=["Transcriber"])
app.include_router(project_routes.router, prefix="/api/v1", tags=["Projects"])
app.include_router(job_routes.router, prefix="/api/v1", tags=["Jobs"])


# ------------------- Root & Health -------------------
@app.get("/")
async def root():
    return {"message": "KRAFZEN AI API", "version": "0.1.0", "status": "running"}


@app.get("/health/db")
async def health_check():
    """Check DB connectivity"""
    try:
        result = db.table("projects").select("id", count="exact").execute()
        return {"status": "healthy", "db_project_count": result.count}
    except Exception as e:
        print(f"Health check error: {e}")
        return {"status": "degraded", "db": "unreachable"}


# ------------------- Init Error Handlers -------------------
init_sentry(settings.SENTRY_DSN)
add_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
