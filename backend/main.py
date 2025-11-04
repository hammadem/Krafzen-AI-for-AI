"""
KRAFZEN AI - Main FastAPI Application
Entry point for the backend service
"""

import re
import sentry_sdk
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
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

# Custom CORS middleware to handle wildcards
class WildcardCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Check if origin is allowed
        is_allowed = False
        if origin:
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

