import uuid
from app.db.supabase_client import db
from fastapi.concurrency import run_in_threadpool

# Validates that a string is a proper UUID format
# Used across queries to prevent invalid DB lookups
def _valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False
    
# Checks if a user owns a project by comparing user_id in projects table
# Used for ownership validation before any export or project operation
async def _user_owns_project(project_id: str, user_id: str) -> bool:
    
    try:
        res = await run_in_threadpool(
            lambda: db.table("projects")
                .select("user_id")
                .eq("id", project_id)
                .maybe_single()
                .execute()
        )
        if not res or not res.data:
            return False
        return res.data["user_id"] == user_id
    except Exception as e:
        from app.utils.logger import logger
        logger.error("[_user_owns_project] Error", error=str(e), exc_info=True)
        return False