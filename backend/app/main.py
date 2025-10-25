"""FastAPI entry point for KRAFZEN AI backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import init_sentry
from app.utils.error_handler import add_exception_handlers
from app.routes import project_routes  # Stub import

app = FastAPI(
    title="KRAFZEN AI Backend",
    description="API for voice/text to DXF conversion MVP",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (expand for jobs/files)
app.include_router(project_routes.router, prefix="/api/v1", tags=["projects"])

@app.get("/health")
async def health_check():
    # Quick DB ping (provisional)
    try:
        count = len(db.table("projects").select("count").execute().data)
        return {"status": "healthy", "db_projects": count}
    except:
        return {"status": "healthy", "db": "pending"}

# Init logging/Sentry/error handlers
init_sentry(settings.SENTRY_DSN)
add_exception_handlers(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
