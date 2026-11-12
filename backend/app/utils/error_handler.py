"""Global exception handling."""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def add_exception_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Use `detail` like FastAPI's default so clients (e.g. design-file download) can show errors.
        payload: dict = {"detail": exc.detail}
        if isinstance(exc.detail, str):
            payload["message"] = exc.detail
        return JSONResponse(
            status_code=exc.status_code,
            content=payload,
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"message": "Validation Error", "detail": exc.errors()},
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        import logging
<<<<<<< HEAD
        logging.getLogger("app.error_handler").error(f"Global exception: {exc}")
=======
        logging.getLogger("app.error_handler").error(f"Middleware Exception: %s", exc, exc_info=True)
        error_msg = exc.decode("utf-8", errors="replace") if isinstance(exc, bytes) else str(exc)
>>>>>>> origin/feat/enterprise-regional-and-white-label-reporting
        return JSONResponse(
        status_code=500,
        content={"detail": {"error": {"code": "INTERNAL_SERVER_ERROR", "message": error_msg}}}
        )
