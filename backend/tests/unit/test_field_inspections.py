"""Field inspection persisted-record and ownership tests."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException
from app.routes import field_routes

PROJECT = "00000000-0000-0000-0000-000000000002"
INSPECTION = "00000000-0000-0000-0000-000000000003"
USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


@pytest.mark.asyncio
async def test_field_observation_persists_actual_notes_and_project_owner():
    query = MagicMock()
    query.insert.return_value = query
    query.execute.return_value = SimpleNamespace(data=[{"id": INSPECTION, "status": "open"}])
    db = MagicMock()
    db.table.return_value = query
    async def inline(fn):
        return fn()
    with (
        patch.object(field_routes, "_owned_project", AsyncMock(return_value={"id": PROJECT})),
        patch.object(field_routes, "db", db),
        patch.object(field_routes, "run_in_threadpool", inline),
    ):
        result = await field_routes.create_field_inspection(
            field_routes.NewFieldInspection(
                project_id=UUID(PROJECT), title="Main entrance barrier",
                description="Observed a blocked accessible path on site",
                discipline="architecture", severity="high",
                location_label="North lobby",
            ),
            user=USER,
        )
    assert result["id"] == INSPECTION
    row = query.insert.call_args.args[0]
    assert row["created_by"] == USER["user_id"]
    assert row["project_id"] == PROJECT
    assert row["status"] == "open"
    assert row["description"] == "Observed a blocked accessible path on site"
    assert row["severity"] == "high"


@pytest.mark.asyncio
async def test_field_observation_refuses_unowned_project():
    db = MagicMock()
    with (
        patch.object(field_routes, "_owned_project", AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Project not found")
        )),
        patch.object(field_routes, "db", db),
    ):
        with pytest.raises(HTTPException) as error:
            await field_routes.create_field_inspection(
                field_routes.NewFieldInspection(
                    project_id=UUID(PROJECT), title="Test inspection",
                    description="Real observation",
                ),
                user=USER,
            )
    assert error.value.status_code == 404
    db.table.assert_not_called()


@pytest.mark.asyncio
async def test_field_status_does_not_skip_human_resolution():
    read = MagicMock()
    read.select.return_value = read
    read.eq.return_value = read
    read.maybe_single.return_value = read
    read.execute.return_value = SimpleNamespace(data={
        "id": INSPECTION, "project_id": PROJECT, "status": "open"
    })
    db = MagicMock()
    db.table.return_value = read
    async def inline(fn):
        return fn()
    with (
        patch.object(field_routes, "db", db),
        patch.object(field_routes, "run_in_threadpool", inline),
        patch.object(field_routes, "_owned_project", AsyncMock(return_value={"id": PROJECT})),
    ):
        with pytest.raises(HTTPException) as error:
            await field_routes.update_field_inspection(
                UUID(INSPECTION), field_routes.FieldStatusChange(status="verified"), user=USER
            )
    assert error.value.status_code == 409
    read.update.assert_not_called()


@pytest.mark.asyncio
async def test_field_resolve_compares_old_state_before_update():
    query = MagicMock()
    query.select.return_value = query
    query.eq.return_value = query
    query.maybe_single.return_value = query
    query.update.return_value = query
    query.execute.side_effect = [
        SimpleNamespace(data={"id": INSPECTION, "project_id": PROJECT, "status": "open"}),
        SimpleNamespace(data=[{"id": INSPECTION, "status": "resolved"}]),
    ]
    db = MagicMock()
    db.table.return_value = query
    async def inline(fn):
        return fn()
    with (
        patch.object(field_routes, "db", db),
        patch.object(field_routes, "run_in_threadpool", inline),
        patch.object(field_routes, "_owned_project", AsyncMock(return_value={"id": PROJECT})),
    ):
        result = await field_routes.update_field_inspection(
            UUID(INSPECTION), field_routes.FieldStatusChange(status="resolved"), user=USER
        )
    assert result["status"] == "resolved"
    assert any(c.args == ("status", "open") for c in query.eq.call_args_list)
    assert any(c.args == ("created_by", USER["user_id"]) for c in query.eq.call_args_list)


def test_field_routes_registered_and_reject_bad_payload(client):
    response = client.post("/api/v1/field/inspections", json={
        "project_id": PROJECT, "title": "ok", "description": "",
        "severity": "critical",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_field_list_is_owner_scoped():
    query = MagicMock()
    for method in ("select", "eq", "order", "limit"):
        getattr(query, method).return_value = query
    query.execute.return_value = SimpleNamespace(data=[{
        "id": INSPECTION, "created_by": USER["user_id"]
    }])
    db = MagicMock()
    db.table.return_value = query
    async def inline(fn):
        return fn()
    with (
        patch.object(field_routes, "_owned_project", AsyncMock(return_value={"id": PROJECT})),
        patch.object(field_routes, "db", db),
        patch.object(field_routes, "run_in_threadpool", inline),
    ):
        result = await field_routes.list_field_inspections(UUID(PROJECT), user=USER)
    assert len(result) == 1
    assert any(c.args == ("created_by", USER["user_id"]) for c in query.eq.call_args_list)
