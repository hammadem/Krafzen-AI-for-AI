"""FastAPI entry point for KRAFZEN AI backend."""
import asyncio
import logging
import re

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.api import health, transcriber
from app.core.config import settings
from app.core.logging_config import init_sentry
from app.routes.activity_routes import router as activity_router
from app.routes.notification_routes import router as notification_router
from app.services.worker_service import _poll_export_jobs
from app.utils.error_handler import add_exception_handlers

logger = logging.getLogger(__name__)




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
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Middleware exception")
            from starlette.responses import JSONResponse
            response = JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

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
from app.routes import (
    architecture_routes,
    chat_routes,
    dashboard_routes,
    export_routes,
    export_validation_routes,
    file_routes,
    invite_routes,
    job_routes,
    payment_routes,
    project_routes,
    user_routes,
    workspace_routes,
)

# ... (middle of file)
logger.info("Registering API routes")
# Include API routers
app.include_router(project_routes.router, prefix="/api/v1", tags=["Projects"])
app.include_router(job_routes.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(file_routes.router, prefix="/api/v1", tags=["Files"])
app.include_router(chat_routes.router, prefix="/api/v1", tags=["Chat"])
app.include_router(payment_routes.router, prefix="/api/v1", tags=["Payments"])

app.include_router(user_routes.router, prefix="/api/v1", tags=["Users"])
app.include_router(architecture_routes.router, prefix="/api/v1", tags=["Architecture Contracts"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(transcriber.router, prefix="/api/v1", tags=["Transcriber"])
app.include_router(dashboard_routes.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(workspace_routes.router, prefix="/api/v1", tags=["Workspaces"])
app.include_router(activity_router, prefix="/api/v1", tags=["Activity"])
app.include_router(notification_router, prefix="/api/v1", tags=["Notifications"])
app.include_router(export_validation_routes.router, prefix="/api/v1", tags=["Export Validation"])
app.include_router(invite_routes.router, prefix="/api/v1", tags=["Invites"])
app.include_router(export_routes.router, prefix="/api/v1", tags=["Exports"])

# Parser module removed from build system as requested
# (Previously imported app.api.parser here)

# Include DXF generator router
dxf_generator_available = False
dxf_generator = None
try:
    logger.info("Attempting to import DXF generator module")
    from app.api import dxf_generator
    dxf_generator_available = True
    logger.info("DXF generator module imported successfully")
except Exception:
    logger.exception("Failed to import DXF generator module")
    dxf_generator_available = False
    dxf_generator = None

if dxf_generator_available and dxf_generator:
    try:
        logger.info("Attempting to register DXF generator router")
        app.include_router(dxf_generator.router, prefix="/api/v1/dxf", tags=["DXF Generator"])
        logger.info("DXF generator router registered successfully")
    except Exception:
        logger.exception("Failed to register DXF generator router")
else:
    reason = "DXF generator module import failed" if not dxf_generator_available else "DXF generator is None"
    logger.warning("DXF generator router not available - %s", reason)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "KRAFZEN AI API",
        "version": "0.1.0",
        "status": "running"
    }

# Swagger Schema Auto-Rebuild 
@app.on_event("startup")
async def rebuild_openapi_schema():
    """Force rebuild of Swagger schema to fix cache issues"""
    app.openapi_schema = None
    app.openapi()
    logger.info("OpenAPI schema rebuilt successfully; all routes loaded")

    if not (getattr(settings, "SUPABASE_JWT_SECRET", None) or "").strip():
        logger.warning(
            "SUPABASE_JWT_SECRET is not set. Authenticated API calls will return 401. "
            "Set SUPABASE_JWT_SECRET (and SUPABASE_PROJECT_ID) on Render to match your Supabase project."
        )
    if not (getattr(settings, "SUPABASE_PROJECT_ID", None) or "").strip():
        logger.warning(
            "SUPABASE_PROJECT_ID is not set. JWT issuer check will fail; authenticated calls may return 401. "
            "Set SUPABASE_PROJECT_ID on Render to match your Supabase project ref."
        )
    
    logger.info("Registered routes:")
    for route in app.routes:
        if hasattr(route, "path"):
            logger.info("  %s [%s]", route.path, ",".join(route.methods))

    import threading

    def _bootstrap_oda_bundle() -> None:
        try:
            from app.services.dwg_converter_service import dwg_converter_service
            from app.services.oda_bundle import warm_dwg_runtime

            warm_dwg_runtime()
            if dwg_converter_service.is_configured():
                logger.info("DWG: ODA converter ready after bundle bootstrap")
            else:
                logger.warning(
                    "DWG: converter not configured after bootstrap "
                    "(check R2 credentials or DWG_ODA_DEB_URL)"
                )
        except Exception:
            logger.exception("DWG: ODA bundle bootstrap failed")

    threading.Thread(target=_bootstrap_oda_bundle, daemon=True, name="oda-bundle-bootstrap").start()

    # Start background export job poller (Kiruthika Week 2 direction)
    asyncio.create_task(_poll_export_jobs())
    logger.info("[startup] Export job poller registered")

# Init logging / Sentry / error handlers
init_sentry(settings.SENTRY_DSN)
add_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
