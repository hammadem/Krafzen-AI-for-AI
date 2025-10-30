"""FastAPI entry point for KRAFZEN AI backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import init_sentry
from app.utils.error_handler import add_exception_handlers
from app.routes import project_routes
from app.db.supabase_client import db  


app = FastAPI(
    title="KRAFZEN AI Backend",
    description="API for voice/text to DXF conversion MVP",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(project_routes.router, prefix="/api/v1")  


# Health check route
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
