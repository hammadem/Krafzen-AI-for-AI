"""Append and verify three clearly tagged audit events in a staging database."""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.db.supabase_client import db
from app.services.activity_service import record_audit_event


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate three append-only file audit events and read them back."
    )
    parser.add_argument("--actor-user-id", required=True, help="Existing Supabase auth user UUID.")
    parser.add_argument("--project-id", required=True, help="Existing project owned by that user.")
    parser.add_argument("--entity-id", required=True, help="Existing file UUID to reference.")
    parser.add_argument("--organization-id", help="Optional existing workspace UUID.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Actually append events. Without this flag, only validate arguments and preview.",
    )
    return parser.parse_args()


def validate_uuid(value: str, name: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as error:
        raise ValueError(f"{name} must be a UUID") from error


async def _fetch_one(table_name: str, columns: str, row_id: str) -> dict[str, Any]:
    response = await run_in_threadpool(
        lambda: db.table(table_name).select(columns).eq("id", row_id).maybe_single().execute()
    )
    if not response or not response.data:
        raise RuntimeError(f"No {table_name} row found for id {row_id}")
    return response.data


async def generate_events(args: argparse.Namespace) -> None:
    actor_user_id = validate_uuid(args.actor_user_id, "actor-user-id")
    project_id = validate_uuid(args.project_id, "project-id")
    entity_id = validate_uuid(args.entity_id, "entity-id")
    organization_id = (
        validate_uuid(args.organization_id, "organization-id")
        if args.organization_id
        else None
    )
    run_id = str(uuid4())
    actions = ("file.updated", "file.renamed", "file.exported")

    if not args.write:
        print("Preview only; no database connection or writes are made.")
        print(json.dumps({
            "audit_test_run_id": run_id,
            "actor_user_id": actor_user_id,
            "organization_id": organization_id,
            "project_id": project_id,
            "entity_type": "file",
            "entity_id": entity_id,
            "actions": actions,
        }, indent=2))
        print("Re-run with --write only after selecting the staging backend.")
        return

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the backend environment")

    host = urlparse(settings.SUPABASE_URL).hostname or "unknown host"
    print(f"Configured Supabase host: {host}")
    print("This will permanently append 3 audit rows; append-only events cannot be deleted.")

    project = await _fetch_one("projects", "id,user_id", project_id)
    if project.get("user_id") != actor_user_id:
        raise RuntimeError("The supplied actor user does not own the supplied project")
    file_row = await _fetch_one("files", "id,job_id", entity_id)
    if not file_row.get("job_id"):
        raise RuntimeError("The supplied file has no job link; cannot verify its project")
    job = await _fetch_one("jobs", "id,project_id", file_row["job_id"])
    if job.get("project_id") != project_id:
        raise RuntimeError("The supplied file does not belong to the supplied project")

    if organization_id:
        membership = await run_in_threadpool(
            lambda: db.table("workspace_members")
                .select("user_id")
                .eq("workspace_id", organization_id)
                .eq("user_id", actor_user_id)
                .maybe_single()
                .execute()
        )
        if not membership or not membership.data:
            raise RuntimeError("The supplied actor is not a member of the supplied workspace")

    confirmation = input("Type APPEND TEST EVENTS to continue: ")
    if confirmation != "APPEND TEST EVENTS":
        print("Cancelled; no events were written.")
        return

    print(f"Audit test run ID: {run_id}")
    event_ids = []
    write_started_at = datetime.now(UTC)
    for index, action in enumerate(actions, start=1):
        metadata = {
            "audit_test_run_id": run_id,
            "audit_test_event": True,
            "sequence": index,
        }
        if action == "file.renamed":
            metadata.update({"old_name": "audit-test-old.dxf", "new_name": "audit-test-new.dxf"})
        event = await record_audit_event(
            action=action,
            entity_type="file",
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            project_id=project_id,
            metadata=metadata,
        )
        event_ids.append(event["event_id"])

    columns = (
        "event_id,actor_user_id,organization_id,project_id,action,"
        "entity_type,entity_id,timestamp,metadata"
    )
    rows = []
    for event_id in event_ids:
        response = await run_in_threadpool(
            lambda event_id=event_id: db.table("activity_events")
                .select(columns)
                .eq("event_id", event_id)
                .maybe_single()
                .execute()
        )
        if not response or not response.data:
            raise RuntimeError(f"Could not read back audit event {event_id}")
        row = response.data
        expected = {
            "action": actions[len(rows)],
            "actor_user_id": actor_user_id,
            "organization_id": organization_id,
            "project_id": project_id,
            "entity_type": "file",
            "entity_id": entity_id,
        }
        for key, value in expected.items():
            if row.get(key) != value:
                raise AssertionError(
                    f"Event {event_id}: expected {key}={value!r}, got {row.get(key)!r}"
                )
        if row.get("metadata", {}).get("audit_test_run_id") != run_id:
            raise AssertionError(f"Event {event_id} has an unexpected test run marker")
        event_timestamp = datetime.fromisoformat(row["timestamp"])
        if event_timestamp.tzinfo is None or event_timestamp.utcoffset() != UTC.utcoffset(event_timestamp):
            raise AssertionError(f"Event {event_id} timestamp is not UTC")
        if event_timestamp < write_started_at:
            raise AssertionError(f"Event {event_id} timestamp predates this test run")
        rows.append(row)

    print("Verified stored rows:")
    print(json.dumps(rows, indent=2, default=str))


def main() -> None:
    args = parse_args()
    asyncio.run(generate_events(args))


if __name__ == "__main__":
    main()
