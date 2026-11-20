"""Export source-job tenant boundaries must be enforced before inserting exports."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.db.queries import export_queries

PROJECT = "00000000-0000-0000-0000-000000000002"
FOREIGN_PROJECT = "00000000-0000-0000-0000-000000000009"
SOURCE_JOB = "00000000-0000-0000-0000-000000000003"
USER = "00000000-0000-0000-0000-000000000001"


def _db_for_source(source_project: str | None):
    db = MagicMock()
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.maybe_single.return_value = query
    query.execute.return_value = SimpleNamespace(
        data={"project_id": source_project} if source_project else None
    )
    db.table.return_value = query
    return db, query


@pytest.mark.asyncio
@pytest.mark.parametrize("source_project", [FOREIGN_PROJECT, None])
async def test_export_rejects_foreign_or_nonexistent_source_job(source_project):
    db, query = _db_for_source(source_project)

    async def inline(fn):
        return fn()

    with (
        patch.object(export_queries, "_user_owns_project", AsyncMock(return_value=True)),
        patch.object(export_queries, "db", db),
        patch.object(export_queries, "run_in_threadpool", inline),
    ):
        with pytest.raises(HTTPException) as err:
            await export_queries.create_export(
                project_id=PROJECT,
                format="dxf",
                idempotency_key="owned-project-test-123456",
                user_id=USER,
                source_job_id=SOURCE_JOB,
            )
    assert err.value.status_code == 403
    db.table.assert_called_once_with("jobs")
    query.eq.assert_called_once_with("id", SOURCE_JOB)


@pytest.mark.asyncio
async def test_export_accepts_same_project_source_job_and_continues_creation():
    db = MagicMock()
    jobs = MagicMock()
    jobs.select.return_value = jobs
    jobs.eq.return_value = jobs
    jobs.maybe_single.return_value = jobs
    jobs.execute.return_value = SimpleNamespace(data={"project_id": PROJECT})
    exports = MagicMock()
    exports.select.return_value = exports
    exports.eq.return_value = exports
    exports.maybe_single.return_value = exports
    exports.execute.return_value = SimpleNamespace(data=None)
    exports.insert.return_value = exports

    # The duplicate-check query returns no row, then INSERT returns the created export.
    def execute_exports():
        if exports.insert.called:
            return SimpleNamespace(data=[{
                "id": "export-1", "project_id": PROJECT, "source_job_id": SOURCE_JOB
            }])
        return SimpleNamespace(data=None)

    exports.execute.side_effect = execute_exports
    db.table.side_effect = lambda table: jobs if table == "jobs" else exports

    async def inline(fn):
        return fn()

    with (
        patch.object(export_queries, "_user_owns_project", AsyncMock(return_value=True)),
        patch.object(export_queries, "db", db),
        patch.object(export_queries, "run_in_threadpool", inline),
    ):
        result = await export_queries.create_export(
            project_id=PROJECT, format="dxf",
            idempotency_key="owned-project-test-123456",
            user_id=USER, source_job_id=SOURCE_JOB,
        )
    assert result["source_job_id"] == SOURCE_JOB
    assert exports.insert.call_args.args[0]["source_job_id"] == SOURCE_JOB


@pytest.mark.asyncio
async def test_export_does_not_query_source_job_when_project_unowned():
    db = MagicMock()
    with (
        patch.object(export_queries, "_user_owns_project", AsyncMock(return_value=False)),
        patch.object(export_queries, "db", db),
    ):
        with pytest.raises(HTTPException) as err:
            await export_queries.create_export(
                project_id=PROJECT, format="dxf",
                idempotency_key="forbidden-project-1234", user_id=USER,
                source_job_id=SOURCE_JOB,
            )
    assert err.value.status_code == 403
    db.table.assert_not_called()
