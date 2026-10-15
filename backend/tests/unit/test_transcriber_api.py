from unittest.mock import AsyncMock, patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_transcribe_audio_success():
    service = AsyncMock()
    service.transcribe_file.return_value = ("draw a wall", "en", 1.5)

    with patch("app.api.transcriber.gemini_transcription_service", service):
        response = client.post(
            "/api/v1/transcribe",
            files={"file": ("command.wav", b"audio", "audio/wav")},
        )

    assert response.status_code == 200
    assert response.json()["text"] == "draw a wall"


def test_transcribe_audio_validation_error():
    service = AsyncMock()
    service.transcribe_file.side_effect = ValueError("invalid audio")

    with patch("app.api.transcriber.gemini_transcription_service", service):
        response = client.post(
            "/api/v1/transcribe",
            files={"file": ("command.wav", b"audio", "audio/wav")},
        )

    assert response.status_code == 400


def test_transcribe_url_is_explicitly_disabled():
    response = client.post(
        "/api/v1/transcribe-url",
        params={"audio_url": "https://example.com/audio.wav"},
    )

    assert response.status_code == 501
