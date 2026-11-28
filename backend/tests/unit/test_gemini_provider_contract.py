"""Provider contract tests use local fixtures; never bill a Gemini account."""
import base64
import io
from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image

from app.core.config import settings
from app.services import gemini_service as module
from app.services.gemini_service import GeminiService, _image_result, _reference_part


def png():
    buffer=io.BytesIO()
    Image.new("RGB",(8,8),"white").save(buffer,format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def response():
    return {"candidates":[{"finishReason":"STOP","content":{"parts":[{"inlineData":{"mimeType":"image/png","data":png()}}]}}]}


def test_image_response_is_real_raster_and_not_placeholder():
    data=_image_result(response())
    assert data.startswith("data:image/png;base64,")
    assert _reference_part(data)["inlineData"]["mimeType"]=="image/png"


@pytest.mark.parametrize("payload", [{},{"candidates":[{"finishReason":"SAFETY","content":{"parts":[]}}]},{"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":"not an image"}]}}]}])
def test_no_candidate_or_refusal_is_not_success(payload):
    with pytest.raises(RuntimeError):
        _image_result(payload)


def test_reference_images_are_validated_and_remote_url_never_fetched():
    with pytest.raises(ValueError):
        _reference_part("http://127.0.0.1:54321/private")
    with pytest.raises(ValueError):
        _reference_part("data:image/png;base64,not-a-png")
    with pytest.raises(ValueError):
        _reference_part("data:image/jpeg;base64,"+png())


@pytest.mark.asyncio
async def test_free_tier_never_calls_paid_image_provider(monkeypatch):
    monkeypatch.setattr(settings,"GEMINI_API_KEY","test-key")
    monkeypatch.setattr(settings,"GEMINI_ALLOW_PAID_IMAGE_GENERATION",False)
    with patch("app.services.gemini_service._generate_content",new=AsyncMock()) as call:
        with pytest.raises(RuntimeError,match="paid-provider authorization"):
            await GeminiService().generate_image("test")
        call.assert_not_awaited()


@pytest.mark.asyncio
async def test_authorized_image_contract_is_explicit(monkeypatch):
    monkeypatch.setattr(settings,"GEMINI_API_KEY","test-key")
    monkeypatch.setattr(settings,"GEMINI_ALLOW_PAID_IMAGE_GENERATION",True)
    monkeypatch.setattr(settings,"GEMINI_IMAGE_MODEL","gemini-3.1-flash-lite-image")
    with patch("app.services.gemini_service._generate_content",new=AsyncMock(return_value=response())) as call:
        result=await GeminiService().generate_image("test fixture",previous_image_url="data:image/png;base64,"+png())
        assert result.startswith("data:image/png;base64,")
        model, parts, config=call.await_args.args
        assert model=="gemini-3.1-flash-lite-image"
        assert config=={"responseModalities":["IMAGE"],"candidateCount":1}
        assert parts[1]["inlineData"]["mimeType"]=="image/png"
