from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from httpx import HTTPError

from app.db.queries import job_queries


@pytest.mark.asyncio
async def test_limited_jobs_use_existing_created_timestamp(monkeypatch):
    db = MagicMock()
    q = db.table.return_value.select.return_value.eq.return_value
    q.order.return_value.order.return_value.range.return_value.execute.return_value = SimpleNamespace(data=[{"id": "job"}])
    monkeypatch.setattr(job_queries, "db", db)
    monkeypatch.setattr(job_queries, "_user_owns_project", AsyncMock(return_value=True))
    assert await job_queries.get_jobs("project", {"user_id": "owner"}, 10) == [{"id": "job"}]
    q.order.assert_called_once_with("created_at", desc=True)


@pytest.mark.asyncio
async def test_job_list_database_error_is_not_an_empty_success(monkeypatch):
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.execute.side_effect = HTTPError("unavailable")
    monkeypatch.setattr(job_queries, "db", db)
    monkeypatch.setattr(job_queries, "_user_owns_project", AsyncMock(return_value=True))
    with pytest.raises(HTTPException) as exc:
        await job_queries.get_jobs("project", {"user_id": "owner"})
    assert exc.value.status_code == 503


@pytest.mark.asyncio
@pytest.mark.parametrize("transcript", ["Edited transcript", None])
async def test_job_transcript_updates_only_existing_columns(monkeypatch, transcript):
    db = MagicMock()
    table = db.table.return_value
    table.update.return_value.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[{"id": "job", "transcript": transcript}])
    monkeypatch.setattr(job_queries, "db", db)
    monkeypatch.setattr(job_queries, "get_job", AsyncMock(return_value={"id": "job", "project_id": "project"}))
    result = await job_queries.update_job("job", {"transcript": transcript}, {"user_id": "owner"})
    assert result["transcript"] == transcript
    table.update.assert_called_once_with({"transcript": transcript})
    table.update.return_value.eq.assert_called_once_with("id", "job")
    table.update.return_value.eq.return_value.eq.assert_called_once_with("project_id", "project")


@pytest.mark.asyncio
async def test_empty_or_unknown_fields_do_not_write(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(job_queries, "db", db)
    monkeypatch.setattr(job_queries, "get_job", AsyncMock(return_value={"project_id": "project"}))
    result = await job_queries.update_job("job", {"updated_at": "invalid"}, {"user_id": "owner"})
    assert result == {"error": "No valid update fields provided"}
    db.table.assert_not_called()
