"""
Initialize route modules for FastAPI
"""

from importlib import import_module

# Explicit imports for FastAPI routers
project_routes = import_module("app.routes.project_routes")
job_routes = import_module("app.routes.job_routes")

__all__ = ["project_routes", "job_routes"]
