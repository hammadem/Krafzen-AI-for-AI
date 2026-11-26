from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.utils import queue_monitor


@pytest.mark.asyncio
async def test_queue_health_reads_only_owned_jobs_and_reports_stuck_ids():
    actor = "00000000-0000-0000-0000-000000000001"
    query = MagicMock()
    for name in ("select", "eq", "order", "range"):
        getattr(query, name).return_value = query
    query.execute.return_value = SimpleNamespace(data=[
        {"id": "old-job", "status": "queued", "updated_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(), "projects": {"user_id": actor}},
        {"id": "done-job", "status": "completed", "updated_at": datetime.now(UTC).isoformat(), "projects": {"user_id": actor}},
    ])
    db = MagicMock()
    db.table.return_value = query
    with patch.object(queue_monitor, "db", db):
        result = await queue_monitor.get_customer_queue_health(actor)
    query.eq.assert_called_once_with("projects.user_id", actor)
    query.select.assert_called_once_with("id,status,updated_at,projects!inner(user_id)")
    assert result["counts_by_status"]["queued"] == 1
    assert result["counts_by_status"]["completed"] == 1
    assert result["stuck_job_ids"] == ["old-job"]


@pytest.mark.asyncio
async def test_queue_health_refuses_unverified_rows():
    query = MagicMock()
    for name in ("select", "eq", "order", "range"):
        getattr(query, name).return_value = query
    query.execute.return_value = SimpleNamespace(data=[
        {"id": "private-job", "status": "queued", "projects": {"user_id": "other"}},
    ])
    db = MagicMock()
    db.table.return_value = query
    with patch.object(queue_monitor, "db", db), pytest.raises(RuntimeError, match="ownership"):
        await queue_monitor.get_customer_queue_health("actor")


@pytest.mark.asyncio
async def test_queue_health_does_not_claim_empty_queue_on_missing_response():
    query = MagicMock()
    for name in ("select", "eq", "order", "range"):
        getattr(query, name).return_value = query
    query.execute.return_value = None
    db = MagicMock()
    db.table.return_value = query
    with patch.object(queue_monitor, "db", db), pytest.raises(RuntimeError, match="unavailable"):
        await queue_monitor.get_customer_queue_health("actor")
