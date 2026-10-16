from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from app.db.queries import invite_queries, workspace_queries
from app.main import app
from app.middlewares.auth import require_auth
from app.services import activity_service
from fastapi import HTTPException
from httpx import AsyncClient

ACTOR_ID = "00000000-0000-0000-0000-000000000001"
TARGET_ID = "00000000-0000-0000-0000-000000000002"
WORKSPACE_ID = "00000000-0000-0000-0000-000000000003"
INVITE_ID = "00000000-0000-0000-0000-000000000004"
INVITE_TOKEN = "00000000-0000-0000-0000-000000000005"


class FakeQuery:
    def __init__(self, database, table):
        self.database = database
        self.table_name = table
        self.operation = "select"
        self.payload = None
        self.selected_columns = None
        self.ordering = None
        self.filters = {}
        self.single = False

    def select(self, *args, **kwargs):
        self.operation = "select"
        self.selected_columns = args[0] if args else None
        self.count_option = kwargs.get("count")
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def maybe_single(self):
        self.single = True
        return self

    def order(self, *args, **kwargs):
        self.ordering = (args, kwargs)
        return self

    def execute(self):
        rows = self.database.tables.setdefault(self.table_name, [])
        matches = [row for row in rows if all(row.get(k) == v for k, v in self.filters.items())]

        if self.operation == "select":
            data = matches[0] if self.single and matches else None if self.single else matches
        elif self.operation == "insert":
            inserted = dict(self.payload)
            if self.table_name in {"activity_events", "workspace_invites"}:
                inserted["id"] = f"event-{len(rows) + 1}"
            rows.append(inserted)
            data = [inserted]
        elif self.operation == "update":
            for row in matches:
                row.update(self.payload)
            data = [dict(row) for row in matches]
        else:
            self.database.tables[self.table_name] = [row for row in rows if row not in matches]
            data = [dict(row) for row in matches]
        return SimpleNamespace(data=data)


class FakeDatabase:
    def __init__(self, tables=None, user_email="invitee@example.com"):
        self.tables = tables or {}
        self.auth = SimpleNamespace(
            admin=SimpleNamespace(
                get_user_by_id=lambda user_id: SimpleNamespace(
                    user=SimpleNamespace(id=user_id, email=user_email)
                )
            )
        )

    def table(self, table_name):
        return FakeQuery(self, table_name)


async def run_inline(operation):
    return operation()


def make_invite(*, email="invitee@example.com", status="pending", expires_at=None):
    return {
        "id": INVITE_ID,
        "token": INVITE_TOKEN,
        "workspace_id": WORKSPACE_ID,
        "email": email,
        "invited_by": ACTOR_ID,
        "role": "member",
        "status": status,
        "expires_at": expires_at or (datetime.now(UTC) + timedelta(days=1)).isoformat(),
    }


@pytest.mark.asyncio
async def test_role_change_route_uses_authenticated_actor_not_request_target(monkeypatch):
    monkeypatch.setitem(app.dependency_overrides, require_auth, lambda: {"user_id": ACTOR_ID})
    update_role = AsyncMock(
        return_value={
            "id": "00000000-0000-0000-0000-000000000006",
            "workspace_id": WORKSPACE_ID,
            "user_id": TARGET_ID,
            "role": "admin",
        }
    )

    with patch("app.routes.workspace_routes.update_role_member", new=update_role):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/workspaces/{WORKSPACE_ID}/members/{TARGET_ID}",
                json={"role": "admin", "actor_user_id": TARGET_ID},
            )

    assert response.status_code == 200
    update_role.assert_awaited_once_with(WORKSPACE_ID, TARGET_ID, "admin", ACTOR_ID)


@pytest.mark.asyncio
async def test_accept_invite_route_uses_authenticated_actor(monkeypatch):
    monkeypatch.setitem(app.dependency_overrides, require_auth, lambda: {"user_id": ACTOR_ID})
    accept = AsyncMock(return_value={"message": "Invite accepted"})

    with patch("app.routes.invite_routes.accept_invite", new=accept):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workspaces/invites/accept",
                json={"token": INVITE_TOKEN, "actor_user_id": TARGET_ID},
            )

    assert response.status_code == 200
    accept.assert_awaited_once_with(INVITE_TOKEN, ACTOR_ID)


@pytest.mark.asyncio
async def test_role_change_emits_team_and_permission_events_with_actual_actor():
    database = FakeDatabase(
        {"workspace_members": [{
            "workspace_id": WORKSPACE_ID,
            "user_id": TARGET_ID,
            "role": "member",
        }]}
    )
    record_event = AsyncMock()

    with patch.object(workspace_queries, "db", database), \
         patch.object(workspace_queries, "get_workspace", new=AsyncMock(return_value={"owner_id": ACTOR_ID})), \
         patch.object(workspace_queries, "run_in_threadpool", new=AsyncMock(side_effect=run_inline)), \
         patch.object(workspace_queries, "record_workspace_event", new=record_event):
        result = await workspace_queries.update_role_member(
            WORKSPACE_ID, TARGET_ID, "admin", ACTOR_ID
        )

    assert result["role"] == "admin"
    assert [call.kwargs["event_name"] for call in record_event.await_args_list] == [
        "team.role_changed",
        "permissions.permission_changed",
    ]
    assert all(call.kwargs["actor_user_id"] == ACTOR_ID for call in record_event.await_args_list)
    assert record_event.await_args_list[0].kwargs["metadata"] == {
        "target_user_id": TARGET_ID,
        "from_role": "member",
        "to_role": "admin",
    }


@pytest.mark.asyncio
async def test_noop_role_update_does_not_emit_audit_event():
    database = FakeDatabase(
        {"workspace_members": [{
            "workspace_id": WORKSPACE_ID,
            "user_id": TARGET_ID,
            "role": "member",
        }]}
    )
    record_event = AsyncMock()

    with patch.object(workspace_queries, "db", database), \
         patch.object(workspace_queries, "get_workspace", new=AsyncMock(return_value={"owner_id": ACTOR_ID})), \
         patch.object(workspace_queries, "run_in_threadpool", new=AsyncMock(side_effect=run_inline)), \
         patch.object(workspace_queries, "record_workspace_event", new=record_event):
        result = await workspace_queries.update_role_member(
            WORKSPACE_ID, TARGET_ID, "member", ACTOR_ID
        )

    assert result["role"] == "member"
    record_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_member_removal_emits_removal_and_access_revoked_events():
    database = FakeDatabase(
        {"workspace_members": [{
            "workspace_id": WORKSPACE_ID,
            "user_id": TARGET_ID,
            "role": "viewer",
        }]}
    )
    record_event = AsyncMock()

    with patch.object(workspace_queries, "db", database), \
         patch.object(workspace_queries, "get_workspace", new=AsyncMock(return_value={"owner_id": ACTOR_ID})), \
         patch.object(workspace_queries, "run_in_threadpool", new=AsyncMock(side_effect=run_inline)), \
         patch.object(workspace_queries, "record_workspace_event", new=record_event):
        removed = await workspace_queries.remove_member(WORKSPACE_ID, TARGET_ID, ACTOR_ID)

    assert removed is True
    assert [call.kwargs["event_name"] for call in record_event.await_args_list] == [
        "team.member_removed",
        "permissions.access_revoked",
    ]
    assert all(call.kwargs["actor_user_id"] == ACTOR_ID for call in record_event.await_args_list)
    assert database.tables["workspace_members"] == []


@pytest.mark.asyncio
async def test_invite_creation_records_inviter_as_actor():
    database = FakeDatabase()
    record_event = AsyncMock()

    with patch.object(invite_queries, "db", database), \
         patch.object(invite_queries, "get_workspace", new=AsyncMock(return_value={"owner_id": ACTOR_ID})), \
         patch.object(invite_queries, "run_in_threadpool", new=AsyncMock(side_effect=run_inline)), \
         patch.object(invite_queries, "record_workspace_event", new=record_event):
        invite = await invite_queries.create_invite(
            WORKSPACE_ID, "invitee@example.com", "admin", ACTOR_ID
        )

    assert invite["email"] == "invitee@example.com"
    record_event.assert_awaited_once()
    assert record_event.await_args.kwargs["event_name"] == "team.member_invited"
    assert record_event.await_args.kwargs["actor_user_id"] == ACTOR_ID
    assert record_event.await_args.kwargs["metadata"]["role"] == "admin"


@pytest.mark.asyncio
async def test_invite_revocation_records_inviter_as_actor():
    database = FakeDatabase({"workspace_invites": [make_invite()]})
    record_event = AsyncMock()

    with patch.object(invite_queries, "db", database), \
         patch.object(invite_queries, "run_in_threadpool", new=AsyncMock(side_effect=run_inline)), \
         patch.object(invite_queries, "record_workspace_event", new=record_event):
        revoked = await invite_queries.revoke_invite(INVITE_ID, ACTOR_ID)

    assert revoked is True
    record_event.assert_awaited_once()
    assert record_event.await_args.kwargs["event_name"] == "permissions.access_revoked"
    assert record_event.await_args.kwargs["actor_user_id"] == ACTOR_ID
    assert record_event.await_args.kwargs["metadata"]["access_scope"] == "pending_invitation"


@pytest.mark.asyncio
async def test_accept_invite_creates_membership_and_records_authenticated_user():
    database = FakeDatabase({"workspace_invites": [make_invite()]})
    record_event = AsyncMock()

    with patch.object(invite_queries, "db", database), \
         patch.object(invite_queries, "run_in_threadpool", new=AsyncMock(side_effect=run_inline)), \
         patch.object(invite_queries, "record_workspace_event", new=record_event):
        result = await invite_queries.accept_invite(INVITE_TOKEN, TARGET_ID)

    assert result["workspace_id"] == WORKSPACE_ID
    assert result["role"] == "member"
    assert database.tables["workspace_invites"][0]["status"] == "accepted"
    assert database.tables["workspace_members"] == [{
        "workspace_id": WORKSPACE_ID,
        "user_id": TARGET_ID,
        "role": "member",
    }]
    assert [call.kwargs["event_name"] for call in record_event.await_args_list] == [
        "team.member_joined",
        "permissions.access_granted",
    ]
    assert all(call.kwargs["actor_user_id"] == TARGET_ID for call in record_event.await_args_list)


@pytest.mark.asyncio
async def test_accept_invite_rejects_authenticated_user_with_different_email():
    database = FakeDatabase(
        {"workspace_invites": [make_invite(email="another@example.com")]},
        user_email="invitee@example.com",
    )
    record_event = AsyncMock()

    with patch.object(invite_queries, "db", database), \
         patch.object(invite_queries, "run_in_threadpool", new=AsyncMock(side_effect=run_inline)), \
         patch.object(invite_queries, "record_workspace_event", new=record_event):
        with pytest.raises(HTTPException) as error:
            await invite_queries.accept_invite(INVITE_TOKEN, TARGET_ID)

    assert error.value.status_code == 403
    assert database.tables["workspace_invites"][0]["status"] == "pending"
    assert database.tables.get("workspace_members", []) == []
    record_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_expired_invite_is_not_accepted_or_audited():
    expired_at = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    database = FakeDatabase({"workspace_invites": [make_invite(expires_at=expired_at)]})
    record_event = AsyncMock()

    with patch.object(invite_queries, "db", database), \
         patch.object(invite_queries, "run_in_threadpool", new=AsyncMock(side_effect=run_inline)), \
         patch.object(invite_queries, "record_workspace_event", new=record_event):
        with pytest.raises(HTTPException) as error:
            await invite_queries.accept_invite(INVITE_TOKEN, TARGET_ID)

    assert error.value.status_code == 410
    assert database.tables["workspace_invites"][0]["status"] == "expired"
    assert database.tables.get("workspace_members", []) == []
    record_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_workspace_event_requires_actor_and_persists_scope():
    database = FakeDatabase()

    with patch.object(activity_service, "db", database), \
         patch.object(activity_service, "run_in_threadpool", new=AsyncMock(side_effect=run_inline)):
        event = await activity_service.record_workspace_event(
            event_name="team.role_changed",
            workspace_id=WORKSPACE_ID,
            actor_user_id=ACTOR_ID,
            metadata={"target_user_id": TARGET_ID},
        )

    assert event["workspace_id"] == WORKSPACE_ID
    assert event["actor_user_id"] == ACTOR_ID
    assert database.tables["activity_events"][0]["metadata"]["target_user_id"] == TARGET_ID

    with pytest.raises(ValueError, match="authenticated actor_user_id"):
        await activity_service.record_workspace_event(
            event_name="team.role_changed",
            workspace_id=WORKSPACE_ID,
            actor_user_id="",
        )
