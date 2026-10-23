from unittest.mock import MagicMock, patch

import pytest
from app.services.chat_history_service import chat_history_service


@pytest.mark.asyncio
async def test_get_session_messages_pagination():
    """Test get_session_messages pagination limits and next_cursor generation."""
    # Generate 35 mock messages (descending by created_at)
    mock_raw_messages = [
        {
            "id": f"msg_{i:02d}",
            "session_id": "test-session-123",
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message content {i}",
            "created_at": f"2026-09-02T10:{i:02d}:00Z",
        }
        for i in range(35, 0, -1)
    ]

    mock_db = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_order = MagicMock()
    mock_limit = MagicMock()
    mock_execute = MagicMock()

    # Query chain: db.table().select().eq().order().limit().execute()
    mock_db.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.order.return_value = mock_order
    mock_order.limit.return_value = mock_limit
    
    # Return first 31 messages (since limit is 30, fetch_limit is 31)
    mock_limit.execute.return_value = MagicMock(data=mock_raw_messages[:31])

    with patch("app.services.chat_history_service.db", mock_db), \
         patch.object(chat_history_service, "_get_feedback_for_message_ids", return_value={}):

        result = await chat_history_service.get_session_messages("test-session-123", limit=30)

        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) == 30
        assert result["has_more"] is True
        assert result["next_cursor"] is not None
        assert "metrics" in result
        assert "db_query_ms" in result["metrics"]
        assert "total_ms" in result["metrics"]
