"""Document requirement: no client-forged engineering output and no cross-project CAD."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.db.queries import project_queries
from app.api import dxf_generator
from app.models.project_model import ProjectUpdate

USER = {"user_id": "00000000-0000-0000-0000-000000000001"}
PROJECT_ID = "00000000-0000-0000-0000-000000000011"
OWNED = {"id": PROJECT_ID, "user_id": USER["user_id"], "input_text": "Office drawing", "archived_at": None}


@pytest.mark.parametrize("body", [
    {"dxf_url": "https://attacker.example/fake.dxf"},
    {"dwg_url": "https://attacker.example/fake.dwg"},
    {"image_url": "https://attacker.example/screenshot.png"},
    {"parsed_json": {"approved": True}},
    {"input_text": "New name", "dxf_url": "https://attacker.example/fake.dxf"},
    {"archived_at": None},
])
def test_browser_cannot_write_generated_cad_or_archive_fields(client, body):
    with patch("app.routes.project_routes.update_project", AsyncMock()) as update:
        result = client.patch(f"/api/v1/projects/{PROJECT_ID}", json=body)
    assert result.status_code == 422
    update.assert_not_awaited()


@pytest.mark.asyncio
async def test_public_project_update_restricts_database_fields_and_owner():
    chain = MagicMock()
    for name in ("update", "eq", "is_"):
        getattr(chain, name).return_value = chain
    chain.execute.return_value = SimpleNamespace(data=[{**OWNED, "input_text": "New description"}])
    fake_db = MagicMock()
    fake_db.table.return_value = chain
    with (
        patch.object(project_queries, "get_project", AsyncMock(return_value=OWNED)),
        patch.dict(project_queries.__dict__, {"db": fake_db}),
        patch.object(project_queries, "run_in_threadpool", AsyncMock(side_effect=lambda fn: fn())),
    ):
        result = await project_queries.update_project(
            PROJECT_ID, ProjectUpdate(input_text="New description"), USER
        )
    assert result["input_text"] == "New description"
    fields = chain.update.call_args.args[0]
    assert set(fields) == {"input_text", "updated_at"}
    chain.eq.assert_any_call("user_id", USER["user_id"])
    chain.is_.assert_called_once_with("archived_at", "null")


@pytest.mark.asyncio
async def test_archived_project_is_immutable_until_restored():
    with (
        patch.object(project_queries, "get_project", AsyncMock(return_value={**OWNED, "archived_at": "2026-01-01T00:00:00Z"})),
        patch.object(project_queries, "run_in_threadpool", AsyncMock()) as pool,
    ):
        with pytest.raises(HTTPException) as error:
            await project_queries.update_project(
                PROJECT_ID, ProjectUpdate(input_text="Modified"), USER
            )
    assert error.value.status_code == 409
    pool.assert_not_awaited()


@pytest.mark.asyncio
async def test_generated_assets_persist_only_to_owned_active_project():
    chain = MagicMock()
    for name in ("update", "eq", "is_"):
        getattr(chain, name).return_value = chain
    chain.execute.return_value = SimpleNamespace(data=[{**OWNED, "dxf_url": "https://verified.storage/plan.dxf"}])
    fake_db = MagicMock()
    fake_db.table.return_value = chain
    with (
        patch.object(project_queries, "get_project", AsyncMock(return_value=OWNED)),
        patch.dict(project_queries.__dict__, {"db": fake_db}),
        patch.object(project_queries, "run_in_threadpool", AsyncMock(side_effect=lambda fn: fn())),
    ):
        await project_queries.update_generated_project_assets(
            PROJECT_ID, user=USER,
            image_url=None, dxf_url="https://verified.storage/plan.dxf", dwg_url=None,
        )
    fields = chain.update.call_args.args[0]
    assert set(fields) == {"dxf_url", "updated_at"}
    chain.eq.assert_any_call("user_id", USER["user_id"])
    chain.is_.assert_called_once_with("archived_at", "null")


@pytest.mark.asyncio
async def test_asset_update_denies_foreign_project_before_database_mutation():
    with (
        patch.object(project_queries, "get_project", AsyncMock(return_value=None)),
        patch.object(project_queries, "run_in_threadpool", AsyncMock()) as pool,
    ):
        with pytest.raises(HTTPException) as error:
            await project_queries.update_generated_project_assets(
                PROJECT_ID, user=USER, image_url=None, dxf_url="fake", dwg_url=None
            )
    assert error.value.status_code == 404
    pool.assert_not_awaited()


@pytest.mark.asyncio
async def test_dxf_generator_denies_foreign_project_before_ai_generation():
    from app.schemas.parser import ParsingRequest
    with (
        patch.object(dxf_generator, "get_project", AsyncMock(return_value=None)),
        patch.object(dxf_generator.cadllm_service, "enhance_prompt", AsyncMock()) as llm,
    ):
        with pytest.raises(HTTPException) as error:
            await dxf_generator.generate_and_store_dxf(
                request=ParsingRequest(text="Office floor plan"),
                project_id=PROJECT_ID, user=USER,
            )
    assert error.value.status_code == 404
    llm.assert_not_awaited()


@pytest.mark.asyncio
async def test_dxf_download_denies_foreign_project_before_storage():
    with (
        patch.object(dxf_generator, "get_project", AsyncMock(return_value=None)),
        patch.object(dxf_generator.storage_service, "download_cad_file", AsyncMock()) as download,
    ):
        from app.schemas.parser import CADFileType
        with pytest.raises(HTTPException) as error:
            await dxf_generator.download_project_dxf(
                project_id=PROJECT_ID,
                file_type=CADFileType.DXF, user=USER
            )
    assert error.value.status_code == 404
    download.assert_not_awaited()
