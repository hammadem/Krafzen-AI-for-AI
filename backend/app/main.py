"""FastAPI entry point for KRAFZEN AI backend."""
import re
import sys
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.config import settings
from app.core.logging_config import init_sentry
from app.utils.error_handler import add_exception_handlers
from app.api import health, transcriber
from app.db.supabase_client import db
import logging
import sys

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
        except Exception as e:
            logger.error(f"Middleware Exception: {e}")
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
    project_routes,
    job_routes,
    file_routes,
    chat_routes,
    payment_routes,
    user_routes,
    architecture_routes,
    dashboard_routes,
    workspace_routes,
    invite_routes
)

# ... (middle of file)
print("✅ Registering User Routes...")
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
app.include_router(invite_routes.router,prefix="/api/v1", tags=["Invites"])

# Parser module removed from build system as requested
# (Previously imported app.api.parser here)

# Include DXF generator router
dxf_generator_available = False
dxf_generator = None
try:
    sys.stdout.write("🔍 Attempting to import DXF generator module...\n")
    sys.stdout.flush()
    from app.api import dxf_generator
    dxf_generator_available = True
    sys.stdout.write("✅ DXF generator module imported successfully\n")
    sys.stdout.flush()
    logger.info("DXF generator module imported successfully")
except Exception as e:
    import traceback
    error_msg = f"⚠️ Failed to import DXF generator module: {e}"
    sys.stdout.write(error_msg + "\n")
    sys.stdout.flush()
    traceback.print_exc()
    logger.error(f"Failed to import DXF generator module: {e}", exc_info=True)
    dxf_generator_available = False
    dxf_generator = None

if dxf_generator_available and dxf_generator:
    try:
        sys.stdout.write("🔍 Attempting to register DXF generator router...\n")
        sys.stdout.flush()
        app.include_router(dxf_generator.router, prefix="/api/v1/dxf", tags=["DXF Generator"])
        sys.stdout.write("✅ DXF generator router registered successfully\n")
        sys.stdout.flush()
        logger.info("DXF generator router registered successfully")
    except Exception as e:
        import traceback
        error_msg = f"❌ Failed to register DXF generator router: {e}"
        sys.stdout.write(error_msg + "\n")
        sys.stdout.flush()
        traceback.print_exc()
        logger.error(f"Failed to register DXF generator router: {e}", exc_info=True)
else:
    reason = "DXF generator module import failed" if not dxf_generator_available else "DXF generator is None"
    sys.stdout.write(f"⚠️ DXF generator router not available - {reason}\n")
    sys.stdout.flush()
    logger.warning(f"DXF generator router not available - {reason}")


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
    print("🔁 OpenAPI schema rebuilt successfully — all routes loaded.")

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
    
    print("\n🔍 Registered Routes:")
    for route in app.routes:
        if hasattr(route, "path"):
             print(f"   - {route.path} [{','.join(route.methods)}]")
    print("---------------------\n")

    import threading

    def _bootstrap_oda_bundle() -> None:
        try:
            from app.services.oda_bundle import warm_dwg_runtime
            from app.services.dwg_converter_service import dwg_converter_service

            warm_dwg_runtime()
            if dwg_converter_service.is_configured():
                logger.info("DWG: ODA converter ready after bundle bootstrap")
            else:
                logger.warning(
                    "DWG: converter not configured after bootstrap "
                    "(check R2 credentials or DWG_ODA_DEB_URL)"
                )
        except Exception as oda_err:
            logger.error("DWG: ODA bundle bootstrap failed: %s", oda_err, exc_info=True)

    threading.Thread(target=_bootstrap_oda_bundle, daemon=True, name="oda-bundle-bootstrap").start()

# Init logging / Sentry / error handlers
init_sentry(settings.SENTRY_DSN)
add_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
