"""
Unit tests for transcriber API endpoints
Tests use mocks to avoid actual API calls
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
from io import BytesIO

from app.main import app


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def mock_whisper_service():
    """Mock whisper service"""
    with patch('app.api.transcriber.whisper_service') as mock_service:
        yield mock_service


class TestTranscriberAPI:
    """Test transcriber API endpoints"""
    
    def test_transcribe_audio_success(self, client, mock_whisper_service):
        """Test successful audio transcription"""
        # Mock whisper service response
        mock_whisper_service.transcribe_file = AsyncMock(
            return_value=("This is transcribed text", "en", 10.5)
        )
        
        # Create test file
        audio_content = b"fake audio content"
        files = {"file": ("test.mp3", BytesIO(audio_content), "audio/mpeg")}
        
        response = client.post("/api/v1/transcribe?language=en", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["text"] == "This is transcribed text"
        assert data["language"] == "en"
        assert data["duration"] == 10.5
        assert data["filename"] == "test.mp3"
        
        # Verify service was called
        mock_whisper_service.transcribe_file.assert_called_once()
        call_args = mock_whisper_service.transcribe_file.call_args
        assert call_args.kwargs["language"] == "en"
        assert call_args.kwargs["filename"] == "test.mp3"
    
    def test_transcribe_audio_auto_language(self, client, mock_whisper_service):
        """Test transcription with auto language detection"""
        mock_whisper_service.transcribe_file = AsyncMock(
            return_value=("Texto transcrito", "es", None)
        )
        
        files = {"file": ("test.mp3", BytesIO(b"audio"), "audio/mpeg")}
        response = client.post("/api/v1/transcribe?language=auto", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "es"
    
    def test_transcribe_audio_service_not_configured(self, client):
        """Test error when whisper service is not configured"""
        with patch('app.api.transcriber.whisper_service', None):
            files = {"file": ("test.mp3", BytesIO(b"audio"), "audio/mpeg")}
            response = client.post("/api/v1/transcribe", files=files)
            
            assert response.status_code == 503
            response_data = response.json()
            assert "not configured" in (response_data.get("detail") or response_data.get("message", "")).lower()
    
    def test_transcribe_audio_empty_file(self, client, mock_whisper_service):
        """Test error when empty file is provided"""
        files = {"file": ("empty.mp3", BytesIO(b""), "audio/mpeg")}
        response = client.post("/api/v1/transcribe", files=files)
        
        # Empty file may return 400 or 500 depending on error handling
        assert response.status_code in [400, 500]
        response_data = response.json()
        assert "empty" in (response_data.get("detail") or response_data.get("message", "")).lower()
    
    def test_transcribe_audio_validation_error(self, client, mock_whisper_service):
        """Test handling of validation errors from service"""
        mock_whisper_service.transcribe_file = AsyncMock(
            side_effect=ValueError("Unsupported file format: xyz")
        )
        
        files = {"file": ("test.xyz", BytesIO(b"audio"), "audio/xyz")}
        response = client.post("/api/v1/transcribe", files=files)
        
        assert response.status_code == 400
        response_data = response.json()
        assert "unsupported" in (response_data.get("detail") or response_data.get("message", "")).lower()
    
    def test_transcribe_audio_service_error(self, client, mock_whisper_service):
        """Test handling of service errors"""
        mock_whisper_service.transcribe_file = AsyncMock(
            side_effect=Exception("Transcription failed")
        )
        
        files = {"file": ("test.mp3", BytesIO(b"audio"), "audio/mpeg")}
        response = client.post("/api/v1/transcribe", files=files)
        
        assert response.status_code == 500
        response_data = response.json()
        assert "failed" in (response_data.get("detail") or response_data.get("message", "")).lower()
    
    def test_transcribe_from_url_success(self, client, mock_whisper_service):
        """Test successful URL transcription"""
        mock_whisper_service.transcribe_from_url = AsyncMock(
            return_value=("Transcribed from URL", "en", 5.0)
        )
        
        response = client.post(
            "/api/v1/transcribe-url?audio_url=https://example.com/audio.mp3&language=en"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["text"] == "Transcribed from URL"
        assert data["language"] == "en"
        assert data["duration"] == 5.0
        assert data["filename"] is None
        
        # Verify service was called
        mock_whisper_service.transcribe_from_url.assert_called_once()
        call_args = mock_whisper_service.transcribe_from_url.call_args
        assert call_args.kwargs["audio_url"] == "https://example.com/audio.mp3"
        assert call_args.kwargs["language"] == "en"
    
    def test_transcribe_from_url_missing_url(self, client):
        """Test error when URL parameter is missing"""
        response = client.post("/api/v1/transcribe-url")
        
        assert response.status_code == 422  # Validation error
    
    def test_transcribe_from_url_service_not_configured(self, client):
        """Test error when whisper service is not configured"""
        with patch('app.api.transcriber.whisper_service', None):
            response = client.post(
                "/api/v1/transcribe-url?audio_url=https://example.com/audio.mp3"
            )
            
            assert response.status_code == 503
            response_data = response.json()
            assert "not configured" in (response_data.get("detail") or response_data.get("message", "")).lower()
    
    def test_transcribe_from_url_validation_error(self, client, mock_whisper_service):
        """Test handling of validation errors from service"""
        mock_whisper_service.transcribe_from_url = AsyncMock(
            side_effect=ValueError("Invalid URL")
        )
        
        response = client.post(
            "/api/v1/transcribe-url?audio_url=invalid-url"
        )
        
        assert response.status_code == 400
    
    def test_transcribe_from_url_service_error(self, client, mock_whisper_service):
        """Test handling of service errors"""
        mock_whisper_service.transcribe_from_url = AsyncMock(
            side_effect=Exception("Network error")
        )
        
        response = client.post(
            "/api/v1/transcribe-url?audio_url=https://example.com/audio.mp3"
        )
        
        assert response.status_code == 500
        response_data = response.json()
        assert "failed" in (response_data.get("detail") or response_data.get("message", "")).lower()

