"""
Initialize route modules for FastAPI
"""

from importlib import import_module

project_routes = import_module("app.routes.project_routes")
job_routes = import_module("app.routes.job_routes")
file_routes = import_module("app.routes.file_routes")
chat_routes = import_module("app.routes.chat_routes")

__all__ = ["project_routes", "job_routes", "file_routes", "chat_routes"]
