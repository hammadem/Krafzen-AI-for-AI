"""The streaming transport must not bypass shared paid generation or session ACL."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.routes import chat_routes


@pytest.mark.asyncio
async def test_stream_rejects_foreign_session_before_any_write():
    request=SimpleNamespace(session_id="other-session",message="QA")
    with patch.object(chat_routes.subscription_service,"check_request_balance",new=AsyncMock(return_value={"can_make_request":True})), patch.object(chat_routes.chat_history_service,"get_user_sessions",new=AsyncMock(return_value=[])), patch.object(chat_routes.chat_history_service,"add_message",new=AsyncMock()) as write, patch.object(chat_routes,"generate_chat_response",new=AsyncMock()) as generate:
        with pytest.raises(HTTPException) as err:
            await chat_routes.generate_chat_response_stream(request,{"user_id":"owner"})
        assert err.value.status_code==404
        write.assert_not_awaited()
        generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_stream_uses_shared_pipeline_exactly_once_and_frames_saved_result():
    request=SimpleNamespace(session_id="own",message="QA")
    payload={"session_id":"own","message_id":"saved","validated_response":"actual provider output","image_url":"https://example.test/file"}
    result=SimpleNamespace(model_dump=lambda **kw:payload)
    with patch.object(chat_routes.subscription_service,"check_request_balance",new=AsyncMock(return_value={"can_make_request":True})), patch.object(chat_routes.chat_history_service,"get_user_sessions",new=AsyncMock(return_value=[{"id":"own"}])), patch.object(chat_routes,"generate_chat_response",new=AsyncMock(return_value=result)) as generate:
        response=await chat_routes.generate_chat_response_stream(request,{"user_id":"owner"})
        chunks=[c async for c in response.body_iterator]
        assert all(c.endswith("\n\n") for c in chunks)
        events=[json.loads(c.removeprefix("data: ").strip()) for c in chunks]
        assert [e["type"] for e in events]==["progress","init","token","complete"]
        assert events[-1]["message_id"]=="saved"
        generate.assert_awaited_once_with(request,{"user_id":"owner"})


@pytest.mark.asyncio
async def test_failed_provider_never_emits_complete_or_raw_internal_error():
    request=SimpleNamespace(session_id=None,message="QA")
    with patch.object(chat_routes.subscription_service,"check_request_balance",new=AsyncMock(return_value={"can_make_request":True})), patch.object(chat_routes,"generate_chat_response",new=AsyncMock(side_effect=RuntimeError("internal-secret-fixture"))):
        response=await chat_routes.generate_chat_response_stream(request,{"user_id":"owner"})
        chunks=[c async for c in response.body_iterator]
        joined="".join(chunks)
        assert '"type": "error"' in joined
        assert '"type": "complete"' not in joined
        assert "internal-secret-fixture" not in joined
