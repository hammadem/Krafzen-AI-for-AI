"""Staging/API processes must not consume export jobs on startup by default."""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app import main as main_module


@pytest.mark.asyncio
async def test_http_api_does_not_start_worker_when_database_is_configured():
    with (
        patch.dict("os.environ", {}, clear=False),
        patch.object(main_module.settings, "SUPABASE_URL", "https://db.invalid"),
        patch.object(main_module.settings, "SUPABASE_SERVICE_ROLE_KEY", "staging-secret"),
        patch.object(main_module, "_poll_export_jobs", new_callable=AsyncMock) as poll,
        patch.object(main_module.threading.Thread, "start"),
        patch("os.getenv", side_effect=lambda key, default="": (
            "" if key == "KRAFZEN_EXPORT_WORKER_ENABLED" else default
        )),
    ):
        async with main_module.lifespan(main_module.app):
            pass

    poll.assert_not_called()


@pytest.mark.asyncio
async def test_dedicated_worker_requires_explicit_flag_and_credentials():
    entered = asyncio.Event()

    async def idle_worker():
        entered.set()
        await asyncio.Event().wait()

    with (
        patch.dict("os.environ", {"KRAFZEN_EXPORT_WORKER_ENABLED": "true"}),
        patch.object(main_module.settings, "SUPABASE_URL", "https://db.invalid"),
        patch.object(main_module.settings, "SUPABASE_SERVICE_ROLE_KEY", "staging-secret"),
        patch.object(main_module, "_poll_export_jobs", side_effect=idle_worker) as poll,
        patch.object(main_module.threading.Thread, "start"),
    ):
        async with main_module.lifespan(main_module.app):
            await asyncio.wait_for(entered.wait(), timeout=1)

    poll.assert_called_once()


@pytest.mark.asyncio
async def test_opted_in_worker_does_not_start_without_database_keys():
    with (
        patch.dict("os.environ", {"KRAFZEN_EXPORT_WORKER_ENABLED": "1"}),
        patch.object(main_module.settings, "SUPABASE_URL", ""),
        patch.object(main_module.settings, "SUPABASE_SERVICE_ROLE_KEY", ""),
        patch.object(main_module, "_poll_export_jobs", new_callable=AsyncMock) as poll,
        patch.object(main_module.threading.Thread, "start"),
    ):
        async with main_module.lifespan(main_module.app):
            pass

    poll.assert_not_called()
