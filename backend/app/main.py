"""FastAPI entry point for KRAFZEN AI backend."""
import re
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.config import settings
from app.core.logging_config import init_sentry
from app.utils.error_handler import add_exception_handlers
from app.routes import project_routes
from app.api import health, transcriber
from app.db.supabase_client import db


app = FastAPI(
    title="KRAFZEN AI Backend",
    description="API for voice/text to DXF conversion MVP",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Custom CORS middleware to handle wildcards (from staging)
class WildcardCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Check if origin is allowed
        is_allowed = False
        if origin:
            # Check against FRONTEND_URL first (from PR)
            if hasattr(settings, 'FRONTEND_URL') and settings.FRONTEND_URL == origin:
                is_allowed = True
            # Check against ALLOWED_ORIGINS_LIST (from staging)
            elif hasattr(settings, 'ALLOWED_ORIGINS_LIST'):
                for allowed_origin in settings.ALLOWED_ORIGINS_LIST:
                    if allowed_origin == origin:
                        is_allowed = True
                        break
                    elif '*' in allowed_origin:
                        # Convert wildcard to regex
                        pattern = allowed_origin.replace('.', r'\.').replace('*', '.*')
                        if re.match(pattern, origin):
                            is_allowed = True
                            break
        
        # Handle OPTIONS preflight request
        if request.method == "OPTIONS":
            response = Response()
            if is_allowed:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "*"
                response.headers["Access-Control-Max-Age"] = "600"
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers if allowed
        if is_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response

# Use custom middleware for wildcard support
app.add_middleware(WildcardCORSMiddleware)


# Include API routers
app.include_router(project_routes.router, prefix="/api/v1", tags=["Projects"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(transcriber.router, prefix="/api/v1", tags=["Transcriber"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "KRAFZEN AI API",
        "version": "0.1.0",
        "status": "running"
    }


# Health check route (PR version - kept for backward compatibility)
@app.get("/health")
async def health_check():
    """Check API and DB connectivity."""
    try:
        result = db.table("projects").select("id", count="exact").execute()
        return {"status": "healthy", "db_project_count": result.count}
    except Exception as e:
        print(f"Health check error: {e}")
        return {"status": "degraded", "db": "unreachable"}


# Init logging / Sentry / error handlers
init_sentry(settings.SENTRY_DSN)
add_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
