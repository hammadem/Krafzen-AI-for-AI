from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.routes import chat_routes

USER_ID = "00000000-0000-0000-0000-000000000001"
MESSAGE_ID = "00000000-0000-0000-0000-000000000002"
SESSION_ID = "00000000-0000-0000-0000-000000000003"
PROJECT_ID = "00000000-0000-0000-0000-000000000004"


@pytest.mark.asyncio
async def test_suggestion_decision_audits_references_without_content():
    with (
        patch.object(
            chat_routes.chat_history_service,
            "get_assistant_message_context",
            AsyncMock(
                return_value={
                    "message_id": MESSAGE_ID,
                    "session_id": SESSION_ID,
                    "project_id": PROJECT_ID,
                }
            ),
        ),
        patch.object(
            chat_routes, "record_audit_event", AsyncMock(return_value={})
        ) as record_event,
    ):
        result = await chat_routes.record_suggestion_decision(
            MESSAGE_ID,
            chat_routes.SuggestionDecisionRequest(decision="accepted"),
            {"user_id": USER_ID},
        )

    assert result == {
        "status": "success",
        "suggestion_id": MESSAGE_ID,
        "decision": "accepted",
    }
    event = record_event.await_args.kwargs
    assert event["action"] == "ai.suggestion_accepted"
    assert event["entity_type"] == "ai_suggestion"
    assert event["entity_id"] == MESSAGE_ID
    assert event["project_id"] == PROJECT_ID
    assert event["metadata"] == {
        "suggestion_id": MESSAGE_ID,
        "message_id": MESSAGE_ID,
        "session_id": SESSION_ID,
        "decision": "accepted",
    }
    assert "content" not in event["metadata"]
    assert "prompt" not in event["metadata"]


@pytest.mark.asyncio
async def test_suggestion_decision_rejects_messages_outside_user_scope():
    with (
        patch.object(
            chat_routes.chat_history_service,
            "get_assistant_message_context",
            AsyncMock(return_value=None),
        ),
        patch.object(chat_routes, "record_audit_event", AsyncMock()) as record_event,
        pytest.raises(HTTPException) as exc_info,
    ):
        await chat_routes.record_suggestion_decision(
            MESSAGE_ID,
            chat_routes.SuggestionDecisionRequest(decision="rejected"),
            {"user_id": USER_ID},
        )

    assert exc_info.value.status_code == 404
    record_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_generation_failure_audit_records_stage_not_exception_message():
    with patch.object(
        chat_routes, "record_audit_event", AsyncMock(return_value={})
    ) as record_event:
        await chat_routes._record_generation_failure(
            "00000000-0000-0000-0000-000000000005",
            SESSION_ID,
            USER_ID,
            PROJECT_ID,
            "image_generation",
            "RuntimeError",
        )

    event = record_event.await_args.kwargs
    assert event["action"] == "ai.generation_failed"
    assert event["project_id"] == PROJECT_ID
    assert event["metadata"]["stage"] == "image_generation"
    assert event["metadata"]["error_type"] == "RuntimeError"
    assert "error" not in event["metadata"]
    assert "prompt" not in event["metadata"]


@pytest.mark.asyncio
async def test_generation_start_audit_failure_returns_original_error_without_unbound_state():
    audit_error = RuntimeError("audit schema is not migrated")
    with (
        patch.object(
            chat_routes.subscription_service,
            "check_request_balance",
            AsyncMock(return_value={"can_make_request": True}),
        ),
        patch.object(
            chat_routes.chat_history_service,
            "create_session",
            AsyncMock(return_value=SESSION_ID),
        ),
        patch.object(chat_routes.chat_history_service, "add_message", AsyncMock()),
        patch.object(
            chat_routes.chat_history_service,
            "ensure_project_for_session",
            AsyncMock(return_value=PROJECT_ID),
        ),
        patch.object(
            chat_routes, "record_audit_event", AsyncMock(side_effect=audit_error)
        ),
        patch.object(
            chat_routes, "_record_generation_failure", AsyncMock()
        ) as record_failure,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await chat_routes.generate_chat_response(
                chat_routes.ChatRequest(message="Draw a floor plan"),
                {"user_id": USER_ID},
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == str(audit_error)
    record_failure.assert_awaited_once()
    assert record_failure.await_args.args[1:] == (
        SESSION_ID,
        USER_ID,
        PROJECT_ID,
        "generation_started_audit",
        "RuntimeError",
    )


@pytest.mark.asyncio
async def test_image_generation_placeholder_fails_without_deducting_request():
    with (
        patch.object(
            chat_routes.subscription_service,
            "check_request_balance",
            AsyncMock(return_value={"can_make_request": True}),
        ),
        patch.object(
            chat_routes.subscription_service, "deduct_request", AsyncMock()
        ) as deduct_request,
        patch.object(
            chat_routes.chat_history_service,
            "create_session",
            AsyncMock(return_value=SESSION_ID),
        ),
        patch.object(
            chat_routes.chat_history_service, "add_message", AsyncMock()
        ) as add_message,
        patch.object(
            chat_routes.chat_history_service,
            "ensure_project_for_session",
            AsyncMock(return_value=PROJECT_ID),
        ),
        patch.object(
            chat_routes.chat_history_service,
            "get_session_messages",
            AsyncMock(return_value={"messages": []}),
        ),
        patch.object(
            chat_routes,
            "cadllm_service",
            SimpleNamespace(enhance_prompt=AsyncMock(return_value="CAD plan")),
        ),
        patch.object(
            chat_routes,
            "gemini_service",
            SimpleNamespace(
                generate_image=AsyncMock(
                    return_value="https://placehold.co/600x400?text=Image+Generation+Failed"
                )
            ),
        ),
        patch.object(
            chat_routes, "record_audit_event", AsyncMock(return_value={})
        ) as record_event,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await chat_routes.generate_chat_response(
                chat_routes.ChatRequest(message="Draw a kitchen"),
                {"user_id": USER_ID},
            )

    assert exc_info.value.status_code == 502
    assert "Image generation failed" in exc_info.value.detail
    assert add_message.await_count == 1
    deduct_request.assert_not_awaited()
    assert record_event.await_args.kwargs["action"] == "ai.generation_failed"
