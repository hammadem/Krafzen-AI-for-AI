"""Initialize route modules for FastAPI."""

from importlib import import_module

project_routes = import_module("app.routes.project_routes")
job_routes = import_module("app.routes.job_routes")
file_routes = import_module("app.routes.file_routes")
chat_routes = import_module("app.routes.chat_routes")
payment_routes = import_module("app.routes.payment_routes")
user_routes = import_module("app.routes.user_routes")
architecture_routes = import_module("app.routes.architecture_routes")
dashboard_routes = import_module("app.routes.dashboard_routes")
workspace_routes = import_module("app.routes.workspace_routes")
activity_routes = import_module("app.routes.activity_routes")
notification_routes = import_module("app.routes.notification_routes")
export_validation_routes = import_module("app.routes.export_validation_routes")
invite_routes = import_module("app.routes.invite_routes")
export_routes = import_module("app.routes.export_routes")
region_routes = import_module("app.routes.region_routes")
branding_routes = import_module("app.routes.branding_routes")
report_routes = import_module("app.routes.report_routes")

__all__ = [
    "activity_routes",
    "architecture_routes",
    "branding_routes",
    "chat_routes",
    "dashboard_routes",
    "export_routes",
    "export_validation_routes",
    "file_routes",
    "invite_routes",
    "job_routes",
    "notification_routes",
    "payment_routes",
    "project_routes",
    "region_routes",
    "report_routes",
    "user_routes",
    "workspace_routes",
]