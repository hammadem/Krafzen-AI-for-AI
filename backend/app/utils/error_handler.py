"""Global exception handling."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.error_handler")


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        payload: dict[str, Any] = {"detail": exc.detail}
        if isinstance(exc.detail, str):
            payload["message"] = exc.detail
        elif isinstance(exc.detail, dict) and "error" in exc.detail:
            err = exc.detail["error"]
            payload["message"] = err.get("message") if isinstance(err, dict) else str(err)
        return JSONResponse(
            status_code=exc.status_code,
            content=payload,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"message": "Validation Error", "detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
        error_msg = exc.decode("utf-8", errors="replace") if isinstance(exc, bytes) else str(exc)
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error",
                "detail": {
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": error_msg,
                    }
                },
            },
        )