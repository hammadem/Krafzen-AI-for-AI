"""Worker-region queue dispatch regression tests, no live database required.

Tests verify that US-residency export jobs are not consumed or failed by
central/global workers and that regional workers cannot process global jobs.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import worker_service

US_POOL = "render-us-nodes"
US_JOB = {
    "id": "00000000-0000-0000-0000-000000000008",
    "project_id": "00000000-0000-0000-0000-000000000009",
    "requested_by": "00000000-0000-0000-0000-000000000010",
    "metadata": {
        "organization_id": "00000000-0000-0000-0000-000000000011",
        "region_code": "us", "worker_pool": US_POOL,
    },
}
GLOBAL_JOB = {
    "id": "00000000-0000-0000-0000-000000000001",
    "project_id": "00000000-0000-0000-0000-000000000002",
    "requested_by": "00000000-0000-0000-0000-000000000003",
    "metadata": {"region_code": "global", "worker_pool": "render-default-nodes"},
}


def test_global_worker_never_claims_us_job():
    with patch.object(worker_service, "CURRENT_REGION_CODE", ""), patch.object(
        worker_service, "CURRENT_WORKER_POOL", ""
    ):
        assert not worker_service._eligible_for_worker(US_JOB)
        assert worker_service._eligible_for_worker(GLOBAL_JOB)


def test_us_worker_claims_only_its_own_organization_jobs():
    with patch.object(worker_service, "CURRENT_REGION_CODE", "us"), patch.object(
        worker_service, "CURRENT_WORKER_POOL", US_POOL
    ):
        assert worker_service._eligible_for_worker(US_JOB)
        assert not worker_service._eligible_for_worker(GLOBAL_JOB)


def test_mismatched_or_missing_worker_pool_is_never_claimed():
    with patch.object(worker_service, "CURRENT_REGION_CODE", "us"), patch.object(
        worker_service, "CURRENT_WORKER_POOL", US_POOL
    ):
        assert not worker_service._eligible_for_worker({
            **US_JOB, "metadata": {**US_JOB["metadata"], "worker_pool": "wrong"},
        })
        assert not worker_service._eligible_for_worker({
            **US_JOB, "metadata": {**US_JOB["metadata"], "worker_pool": ""},
        })


@pytest.mark.parametrize("metadata", [
    {"region_code": "us", "worker_pool": US_POOL},
    {"organization_id": "org-id", "worker_pool": US_POOL},
    {"region_code": "narnia", "organization_id": "org-id", "worker_pool": US_POOL},
    "malformed",
    [],
])
def test_ambiguous_region_or_untrusted_metadata_fails_dispatch_closed(metadata):
    with patch.object(worker_service, "CURRENT_REGION_CODE", "us"), patch.object(
        worker_service, "CURRENT_WORKER_POOL", US_POOL
    ):
        assert not worker_service._eligible_for_worker({**US_JOB, "metadata": metadata})


@pytest.mark.asyncio
async def test_global_poller_skips_regional_job_before_processing():
    processed = []
    scheduled = []
    stub_task = MagicMock()
    stub_task.done.return_value = False

    def record_task(coro):
        scheduled.append(coro)
        coro.close()
        return stub_task

    async def fake_process(job, user):
        processed.append(job["id"])

    with (
        patch.object(worker_service, "CURRENT_REGION_CODE", ""),
        patch.object(worker_service, "CURRENT_WORKER_POOL", ""),
        patch.object(
            worker_service, "run_in_threadpool",
            AsyncMock(return_value=SimpleNamespace(data=[US_JOB, GLOBAL_JOB])),
        ),
        patch.object(worker_service, "process_export_job", side_effect=fake_process) as process,
        patch.object(worker_service.asyncio, "create_task", side_effect=record_task),
        patch.object(
            worker_service.asyncio, "sleep",
            AsyncMock(side_effect=asyncio.CancelledError),
        ),
    ):
        with pytest.raises(asyncio.CancelledError):
            await worker_service._poll_export_jobs()

    # A global poller must never schedule a US job or mark it failed.
    assert process.call_count == 1
    assert process.call_args.args[0]["id"] == GLOBAL_JOB["id"]
    assert len(scheduled) == 1


@pytest.mark.asyncio
async def test_us_poller_skips_global_job_before_processing():
    created = []
    stub_task = MagicMock()
    stub_task.done.return_value = False

    def record_task(coro):
        created.append(coro)
        coro.close()
        return stub_task

    with (
        patch.object(worker_service, "CURRENT_REGION_CODE", "us"),
        patch.object(worker_service, "CURRENT_WORKER_POOL", US_POOL),
        patch.object(
            worker_service, "run_in_threadpool",
            AsyncMock(return_value=SimpleNamespace(data=[GLOBAL_JOB, US_JOB])),
        ),
        patch.object(worker_service, "process_export_job", new_callable=AsyncMock) as process,
        patch.object(worker_service.asyncio, "create_task", side_effect=record_task),
        patch.object(
            worker_service.asyncio, "sleep",
            AsyncMock(side_effect=asyncio.CancelledError),
        ),
    ):
        with pytest.raises(asyncio.CancelledError):
            await worker_service._poll_export_jobs()

    assert process.call_count == 1
    assert process.call_args.args[0]["id"] == US_JOB["id"]
    assert len(created) == 1
