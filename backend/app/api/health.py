"""
Health check endpoints
"""

import importlib.util
import os
import shutil
import time
from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from httpx import HTTPError
from postgrest.exceptions import APIError

from app.core.config import settings
from app.core.security import _trusted_issuer
from app.db.supabase_client import db
from app.services.supabase_service import supabase_service
from app.services.scanner_readiness import scanner_status

router = APIRouter()

@router.get("")
async def health_check():
    """Basic health check endpoint (Render probes GET /health)."""
    try:
        result = db.table("projects").select("id", count="exact").execute()
        return {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "service": "KRAFZEN AI Backend",
            "db_project_count": result.count,
        }
    except (APIError, HTTPError, RuntimeError):
        return {
            "status": "degraded",
            "timestamp": datetime.now(UTC).isoformat(),
            "service": "KRAFZEN AI Backend",
            "db": "unreachable",
        }

@router.get("/ready")
async def readiness_check():
    """503 unless essential connected dependencies are usable.

    Unlike /health, which is a liveness probe, /health/ready indicates
    deployment readiness. Never include credentials or connection errors.
    """
    # The backend accepts either a securely configured legacy JWT secret or
    # the project's PUBLIC anon key for server-side /auth/v1/user verification.
    # Asymmetric JWTs are verified against the project's trusted JWKS.
    # This checks identity configuration, not successful customer sign-in.
    auth_ready = bool(
        settings.SUPABASE_PROJECT_ID
        and _trusted_issuer()
        and (settings.SUPABASE_JWT_SECRET or settings.SUPABASE_ANON_KEY)
    )
    database_configured = bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)
    database_ready = False
    if database_configured:
        try:
            result = await run_in_threadpool(supabase_service.test_connection)
            database_ready = bool(result.get("connected"))
        except Exception:
            database_ready = False

    ai_ready = bool(settings.GEMINI_API_KEY)
    stripe_ready = bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET)
    dodo_key = (
        settings.DODO_PAYMENTS_TEST_API_KEY
        if settings.DODO_PAYMENTS_ENVIRONMENT == "test_mode"
        else settings.DODO_PAYMENTS_API_KEY
    )
    dodo_ready = bool(dodo_key and settings.DODO_PAYMENTS_WEBHOOK_SECRET)
    billing_ready = stripe_ready or dodo_ready

    from app.services.dwg_converter_service import dwg_converter_service
    dwg_ready = bool(dwg_converter_service.is_configured())
    # A working web server does not imply imports can scan customer files.
    try:
        scanner = await run_in_threadpool(scanner_status)
    except Exception:
        scanner = {"scanner_binary_detected": False, "scanner_signature_metadata_current": False}
    scanner_detected = scanner["scanner_binary_detected"]
    ifc_parser_installed = importlib.util.find_spec("ifcopenshell") is not None
    potrace_detected = bool(shutil.which("potrace"))

    # These tables/columns are required by deployed AEC workflows. A healthy
    # Postgres connection cannot prove that migrations were applied. Each
    # probe is bounded, read-only, and performed with the server's configured
    # service identity; no credentials or database exception text is returned.
    required_schema = {
        "ifc_import_schema": ("files", "import_metadata"),
        "file_storage_metadata_schema": ("files", "project_id,bucket,path,mime_type,size_bytes,version,archived_at,approval_state,reviewed_by,reviewed_at"),
        "activity_audit_schema": ("activity_events", "event_id,action,entity_type,entity_id,file_id,organization_id,workspace_id,timestamp"),
        "paid_webhook_ledger_schema": ("payment_webhook_events", "event_id"),
        "paid_subscription_schema": ("user_subscriptions", "last_paid_at"),
        "project_archive_schema": ("projects", "archived_at"),
        "project_metadata_schema": ("projects", "title,description,project_type,lifecycle_stage"),
        "field_notes_schema": ("field_observation_notes", "id,inspection_id,kind,body"),
        "asbuilt_comparison_schema": ("asbuilt_comparisons", "id"),
        "drawing_redline_schema": ("drawing_redlines", "id"),
        "field_inspection_schema": ("field_inspections", "id"),
        "ada_assessment_schema": ("compliance_assessments", "id"),
        "field_photo_schema": ("field_photos", "id"),
        "bim_spatial_screen_schema": ("bim_spatial_screenings", "id"),
    }
    schema_checks = {name: False for name in required_schema}
    if database_ready:
        for name, (table, column) in required_schema.items():
            try:
                await run_in_threadpool(
                    lambda table=table, column=column: db.table(table)
                    .select(column).limit(1).execute()
                )
                schema_checks[name] = True
            except Exception:
                # Missing relation, column, permissions or data API exposure:
                # all must block release readiness rather than be hidden.
                schema_checks[name] = False

    # Security is a release prerequisite independent of connectivity and
    # table existence. The restricted database RPC inspects live RLS/grants,
    # installed signup trigger and legacy free-credit balances. A missing
    # migration or malformed response fails closed; no raw database rows or
    # credential-bearing exception messages are exposed.
    security_contracts = {
        "branding_rls_and_privileges": False,
        "paid_only_signup_function": False,
        "signup_trigger_enabled": False,
        "no_free_trial_balances": False,
        "security_probe_passed": False,
    }
    if database_ready:
        try:
            report_response = await run_in_threadpool(
                lambda: db.rpc("krafzen_release_security_probe").execute()
            )
            report = report_response.data if report_response else None
            if isinstance(report, dict):
                for key in security_contracts:
                    if key != "security_probe_passed":
                        security_contracts[key] = report.get(key) is True
                security_contracts["security_probe_passed"] = (
                    report.get("ready") is True
                    and all(value for key, value in security_contracts.items()
                            if key != "security_probe_passed")
                )
        except Exception:
            pass

    checks = {
        "database": database_ready,
        "authentication": auth_ready,
        "ai_generation": ai_ready,
        "billing": billing_ready,
        "dwg_converter": dwg_ready,
        "import_scanner_detected": scanner_detected,
        "import_signature_metadata_current": scanner["scanner_signature_metadata_current"],
        "ifc_parser_installed": ifc_parser_installed,
        "dxf_tracer_detected": potrace_detected,
        **schema_checks,
        **security_contracts,
    }
    ready = all(checks.values())
    payload = {
        "status": "ready" if ready else "not_ready",
        "dependencies": {
            name: "ready" if is_ready else "unavailable"
            for name, is_ready in checks.items()
        },
    }
    if ready:
        return payload
    return JSONResponse(status_code=503, content=payload)


@router.get("/imports")
async def import_capabilities():
    """Non-secret diagnostics of CAD/BIM import prerequisites.

    Detection of a binary does not verify antivirus signatures or ability to
    successfully process a model. Import endpoints still fail closed.
    """
    checks = {
        **(await run_in_threadpool(scanner_status)),
        "ifc_parser_installed": importlib.util.find_spec("ifcopenshell") is not None,
        "dxf_tracer_detected": bool(shutil.which("potrace")),
    }
    return {
        "status": "prerequisites_detected" if all(checks.values()) else "incomplete",
        "dependencies": checks,
        "scanner_signatures_verified": False,
        "diagnostic_scope": "Binary and signature date only; actual scanning and storage are verified separately.",
        "storage_upload_verified": False,
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system info"""
    start_time = time.time()
    
    # Test Supabase connection
    supabase_status = supabase_service.test_connection()
    
    # Calculate response time
    response_time = round((time.time() - start_time) * 1000, 2)  # in milliseconds
    
    return {
        "status": "healthy" if supabase_status["connected"] else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "KRAFZEN AI Backend",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "response_time_ms": response_time,
        "uptime": "N/A",  # TODO: Add actual uptime tracking
        "dependencies": {
            "database": "connected" if supabase_status["connected"] else "disconnected",
            "openai": "pending"  # TODO: Add OpenAI API check
        },
        "supabase": supabase_status,
        "monitoring": {
            "sentry_enabled": bool(settings.SENTRY_DSN and settings.ENVIRONMENT != "development"),
            "environment": settings.ENVIRONMENT
        },
        "cors": {
            "allowed_origins": getattr(settings, "ALLOWED_ORIGINS_LIST", []),
            "allowed_origins_raw": getattr(settings, "ALLOWED_ORIGINS", "")
        }
    }


@router.get("/dwg")
async def dwg_health_check():
    """Verify that the production ODA bundle includes a usable Qt platform plugin."""
    from app.services.dwg_converter_service import dwg_converter_service
    from app.services.oda_bundle import ensure_oda_bundle, get_last_oda_error

    ready = dwg_converter_service.is_configured()
    payload = {
        "status": "healthy" if ready else "unavailable",
        "service": "DWG converter",
        "engine": dwg_converter_service.converter_type,
        "roundtrip_verified": False,
        "detail": None if ready else "Selected native converter unavailable or not authorized",
    }
    if ready:
        return payload
    return JSONResponse(status_code=503, content=payload)
