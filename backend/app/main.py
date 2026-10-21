"""FastAPI entry point for KRAFZEN AI backend."""

import asyncio
import logging
import re
import sys
import threading
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.api import health, transcriber
from app.core.config import settings
from app.core.logging_config import init_sentry
from app.db.supabase_client import db
from app.routes import (
    activity_routes,
    architecture_routes,
    branding_routes,
    chat_routes,
    dashboard_routes,
    export_routes,
    export_validation_routes,
    file_routes,
    invite_routes,
    job_routes,
    notification_routes,
    payment_routes,
    project_routes,
    region_routes,
    report_routes,
    user_routes,
    workspace_routes,
)
from app.services.worker_service import _poll_export_jobs
from app.utils.error_handler import add_exception_handlers

logger = logging.getLogger(__name__)


def _bootstrap_oda_bundle() -> None:
    """Warm up DWG runtime asynchronously."""
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
    except Exception as oda_err:
        logger.error("DWG: ODA bundle bootstrap failed: %s", oda_err, exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # 1. Warm OpenAPI cache
    app.openapi_schema = None
    app.openapi()
    print("🔁 OpenAPI schema rebuilt successfully — all routes loaded.")

    # 2. Check Supabase JWT environment
    if not (getattr(settings, "SUPABASE_JWT_SECRET", None) or "").strip():
        logger.warning(
            "SUPABASE_JWT_SECRET is not set. Authenticated API calls will return 401."
        )
    if not (getattr(settings, "SUPABASE_PROJECT_ID", None) or "").strip():
        logger.warning(
            "SUPABASE_PROJECT_ID is not set. JWT issuer check will fail; calls may return 401."
        )

    # 3. Print route directory
    print("\n🔍 Registered Routes:")
    for route in app.routes:
        if hasattr(route, "path"):
            methods = getattr(route, "methods", ["GET"])
            print(f"   - {route.path} [{','.join(methods)}]")
    print("---------------------\n")

    # 4. Bootstrap ODA bundle in worker thread
    threading.Thread(
        target=_bootstrap_oda_bundle, daemon=True, name="oda-bundle-bootstrap"
    ).start()

    # 5. Start background export job poller
    poll_task = asyncio.create_task(_poll_export_jobs())
    logger.info("[startup] Export job poller registered")

    yield

    # Clean shutdown
    poll_task.cancel()
    try:
        await poll_task
    except asyncio.CancelledError:
        logger.info("[shutdown] Export job poller cancelled successfully")


app = FastAPI(
    title="KRAFZEN AI Backend",
    description="API for voice/text to DXF conversion MVP",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


class WildcardCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        is_allowed = False

        if origin:
            # 1. Allow local development origins automatically (any port on localhost or 127.0.0.1)
            if re.match(r"^http://(localhost|127\.0\.0\.1)(:\d+)?$", origin):
                is_allowed = True
            elif hasattr(settings, "FRONTEND_URL") and settings.FRONTEND_URL == origin:
                is_allowed = True
            elif hasattr(settings, "ALLOWED_ORIGINS_LIST"):
                for allowed_origin in settings.ALLOWED_ORIGINS_LIST:
                    if allowed_origin == origin:
                        is_allowed = True
                        break
                    elif "*" in allowed_origin:
                        pattern = allowed_origin.replace(".", r"\.").replace("*", ".*")
                        if re.match(pattern, origin):
                            is_allowed = True
                            break

        if request.method == "OPTIONS":
            response = Response()
            if is_allowed:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                )
                response.headers["Access-Control-Allow-Headers"] = (
                    "Authorization, Content-Type, Idempotency-Key, If-Match, Accept"
                )
                response.headers["Access-Control-Expose-Headers"] = (
                    "Idempotency-Key, ETag"
                )
                response.headers["Access-Control-Max-Age"] = "600"
            return response

        try:
            response = await call_next(request)
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Middleware Exception: {e}", exc_info=True)
            response = JSONResponse(
                status_code=500, content={"detail": "Internal Server Error"}
            )

        if is_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type, Idempotency-Key, If-Match, Accept"
            )
            response.headers["Access-Control-Expose-Headers"] = (
                "Idempotency-Key, ETag"
            )

        return response


app.add_middleware(WildcardCORSMiddleware)

# Register Core API Routers
app.include_router(project_routes.router, prefix="/api/v1", tags=["Projects"])
app.include_router(job_routes.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(file_routes.router, prefix="/api/v1", tags=["Files"])
app.include_router(chat_routes.router, prefix="/api/v1", tags=["Chat"])
app.include_router(payment_routes.router, prefix="/api/v1", tags=["Payments"])
app.include_router(user_routes.router, prefix="/api/v1", tags=["Users"])
app.include_router(
    architecture_routes.router, prefix="/api/v1", tags=["Architecture Contracts"]
)
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(transcriber.router, prefix="/api/v1", tags=["Transcriber"])
app.include_router(dashboard_routes.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(workspace_routes.router, prefix="/api/v1", tags=["Workspaces"])
app.include_router(activity_routes.router, prefix="/api/v1", tags=["Activity"])
app.include_router(notification_routes.router, prefix="/api/v1", tags=["Notifications"])
app.include_router(
    export_validation_routes.router, prefix="/api/v1", tags=["Export Validation"]
)
app.include_router(invite_routes.router, prefix="/api/v1", tags=["Invites"])
app.include_router(export_routes.router, prefix="/api/v1", tags=["Exports"])

# Enterprise & White-Label Routers
app.include_router(region_routes.router, prefix="/api/v1")
app.include_router(branding_routes.router, prefix="/api/v1")
app.include_router(report_routes.router, prefix="/api/v1")

# DXF Generator Router
try:
    sys.stdout.write("🔍 Attempting to import DXF generator module...\n")
    sys.stdout.flush()
    from app.api import dxf_generator

    app.include_router(
        dxf_generator.router, prefix="/api/v1/dxf", tags=["DXF Generator"]
    )
    sys.stdout.write("✅ DXF generator module registered successfully\n")
    sys.stdout.flush()
    logger.info("DXF generator router registered successfully")
except Exception as e:
    error_msg = f"⚠️ Failed to import/register DXF generator module: {e}"
    sys.stdout.write(error_msg + "\n")
    sys.stdout.flush()
    traceback.print_exc()
    logger.error(
        f"Failed to import/register DXF generator module: {e}", exc_info=True
    )


@app.get("/")
async def root():
    return {
        "message": "KRAFZEN AI API",
        "version": "0.1.0",
        "status": "running",
    }


# Initialize Sentry and error handlers
init_sentry(settings.SENTRY_DSN)
add_exception_handlers(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)