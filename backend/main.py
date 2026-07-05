"""KRAFZEN AI - Main FastAPI Application (Final Clean Version)"""

import re
import sentry_sdk
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.config import settings
from app.core.logging_config import init_sentry
from app.utils.error_handler import add_exception_handlers
from app.routes import project_routes, job_routes, file_routes, user_routes, workspace_routes, chat_routes, payment_routes
from app.api import health, transcriber
from app.db.supabase_client import db
import logging
import sys

logger = logging.getLogger(__name__)

# Import parser with error handling to ensure app starts even if parser fails
parser_available = False
parser = None
try:
    if settings.DEBUG:
        sys.stdout.write("🔍 Attempting to import parser module...\n")
        sys.stdout.flush()
    from app.api import parser
    parser_available = True
    if settings.DEBUG:
        sys.stdout.write("✅ Parser module imported successfully\n")
        sys.stdout.flush()
        logger.info("Parser module imported successfully")
except Exception as e:
    import traceback
    error_msg = f"⚠️ Failed to import parser module: {e}"
    sys.stdout.write(error_msg + "\n")
    sys.stdout.flush()
    traceback.print_exc()
    logger.error(f"Failed to import parser module: {e}", exc_info=True)
    parser_available = False
    parser = None


# Initialize Sentry (only outside dev)
if settings.SENTRY_DSN and settings.ENVIRONMENT != "development":
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )


# App initialization
# App initialization
# Only enable docs in development
docs_url = "/docs" if settings.ENVIRONMENT == "development" else None
redoc_url = "/redoc" if settings.ENVIRONMENT == "development" else None

app = FastAPI(
    title="KRAFZEN AI API",
    description="AI-powered CAD/BIM generation from voice and text",
    version="0.1.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
)


# ------------------- CORS -------------------
class WildcardCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        is_allowed = False

        if origin:
            allowed_origins = getattr(settings, "ALLOWED_ORIGINS_LIST", [])
            if settings.DEBUG:
                logger.debug(f"CORS check - Origin: {origin}, Allowed origins: {allowed_origins}")
            
            for allowed_origin in allowed_origins:
                if allowed_origin == origin:
                    is_allowed = True
                    if settings.DEBUG:
                        logger.debug(f"CORS: Exact match found for {origin}")
                    break
                elif "*" in allowed_origin:
                    # Convert wildcard pattern to regex
                    # https://*.vercel.app -> https://.*\.vercel\.app
                    # Escape dots and convert * to .* (match any characters)
                    pattern = "^" + allowed_origin.replace(".", r"\.").replace("*", ".*") + "$"
                    if re.match(pattern, origin):
                        is_allowed = True
                        if settings.DEBUG:
                            logger.debug(f"CORS: Wildcard match - pattern '{pattern}' matched origin '{origin}'")
                        break
                    elif settings.DEBUG:
                        logger.debug(f"CORS: Wildcard pattern '{pattern}' did not match origin '{origin}'")

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
            else:
                # Log CORS failures for debugging
                logger.warning(f"CORS preflight rejected - Origin: {origin}, Allowed: {getattr(settings, 'ALLOWED_ORIGINS_LIST', [])}")
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
        elif origin:
            # Log CORS failures for debugging
            logger.warning(f"CORS request rejected - Origin: {origin}, Allowed: {getattr(settings, 'ALLOWED_ORIGINS_LIST', [])}")
        return response


app.add_middleware(WildcardCORSMiddleware)


# ------------------- Routers -------------------
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(transcriber.router, prefix="/api/v1", tags=["Transcriber"])
app.include_router(project_routes.router, prefix="/api/v1", tags=["Projects"])
app.include_router(job_routes.router, prefix="/api/v1", tags=["Jobs"])

app.include_router(file_routes.router, prefix="/api/v1", tags=["Files"])
app.include_router(chat_routes.router, prefix="/api/v1", tags=["Chat"])
app.include_router(payment_routes.router, prefix="/api/v1", tags=["Payments"])
app.include_router(user_routes.router, prefix="/api/v1", tags=["Users"])
app.include_router(workspace_routes.router, prefix="/api/v1", tags=["Workspaces"])

# Include parser router if available
if settings.DEBUG:
    sys.stdout.write(f"🔍 Parser status: available={parser_available}, parser={parser is not None}\n")
    sys.stdout.flush()
if parser_available and parser:
    try:
        if settings.DEBUG:
            sys.stdout.write("🔍 Attempting to register parser router...\n")
            sys.stdout.flush()
        app.include_router(parser.router, prefix="/api/v1", tags=["Parser"])
        if settings.DEBUG:
            sys.stdout.write("✅ Parser router registered successfully\n")
            sys.stdout.flush()
            logger.info("Parser router registered successfully")
    except Exception as e:
        import traceback
        error_msg = f"❌ Failed to register parser router: {e}"
        sys.stdout.write(error_msg + "\n")
        sys.stdout.flush()
        traceback.print_exc()
        logger.error(f"Failed to register parser router: {e}", exc_info=True)
else:
    reason = "Parser module import failed" if not parser_available else "Parser is None"
    sys.stdout.write(f"⚠️ Parser router not available - {reason}\n")
    sys.stdout.flush()
    logger.warning(f"Parser router not available - {reason}")


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
