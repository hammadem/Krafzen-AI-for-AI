"""
Unit tests for WhisperService
Tests use mocks to avoid actual API calls
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from io import BytesIO
import tempfile
import os

from app.services.whisper_service import WhisperService
from app.core.config import settings


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    with patch('app.services.whisper_service.OpenAI') as mock_openai:
        client_instance = Mock()
        mock_openai.return_value = client_instance
        yield client_instance


@pytest.fixture
def whisper_service(mock_openai_client):
    """Create WhisperService instance with mocked OpenAI client"""
    with patch('app.services.whisper_service.settings') as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-api-key"
        mock_settings.ALLOWED_AUDIO_FORMATS_LIST = ["mp3", "wav", "m4a", "ogg", "flac", "webm"]
        mock_settings.MAX_FILE_SIZE_MB = 25.0
        service = WhisperService()
        service.client = mock_openai_client
        return service


class TestWhisperService:
    """Test WhisperService methods"""
    
    def test_init_without_api_key(self):
        """Test that service raises error when API key is missing"""
        with patch('app.services.whisper_service.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            with pytest.raises(ValueError, match="OPENAI_API_KEY is not configured"):
                WhisperService()
    
    def test_is_configured(self, whisper_service):
        """Test is_configured method"""
        with patch('app.services.whisper_service.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            assert whisper_service.is_configured() is True
            
            mock_settings.OPENAI_API_KEY = None
            assert whisper_service.is_configured() is False
    
    @pytest.mark.asyncio
    async def test_transcribe_file_success(self, whisper_service, mock_openai_client):
        """Test successful file transcription"""
        # Mock OpenAI response
        mock_transcript = Mock()
        mock_transcript.text = "This is a test transcription"
        mock_transcript.language = "en"
        mock_transcript.duration = 10.5
        
        mock_openai_client.audio.transcriptions.create.return_value = mock_transcript
        
        # Create test audio content
        audio_content = b"fake audio content"
        filename = "test.mp3"
        
        # Call transcribe_file
        text, language, duration = await whisper_service.transcribe_file(
            file_content=audio_content,
            filename=filename,
            language="en"
        )
        
        # Verify results
        assert text == "This is a test transcription"
        assert language == "en"
        assert duration == 10.5
        
        # Verify OpenAI was called correctly
        assert mock_openai_client.audio.transcriptions.create.called
        call_args = mock_openai_client.audio.transcriptions.create.call_args
        assert call_args.kwargs["model"] == "whisper-1"
        assert call_args.kwargs["language"] == "en"
        assert call_args.kwargs["response_format"] == "verbose_json"
    
    @pytest.mark.asyncio
    async def test_transcribe_file_auto_detect_language(self, whisper_service, mock_openai_client):
        """Test file transcription with auto language detection"""
        mock_transcript = Mock()
        mock_transcript.text = "Test"
        mock_transcript.language = "es"
        mock_transcript.duration = None
        
        mock_openai_client.audio.transcriptions.create.return_value = mock_transcript
        
        text, language, duration = await whisper_service.transcribe_file(
            file_content=b"audio",
            filename="test.mp3",
            language=None
        )
        
        assert text == "Test"
        assert language == "es"
        # Verify language was None (auto-detect)
        call_args = mock_openai_client.audio.transcriptions.create.call_args
        assert call_args.kwargs["language"] is None
    
    @pytest.mark.asyncio
    async def test_transcribe_file_unsupported_format(self, whisper_service):
        """Test that unsupported file format raises ValueError"""
        with pytest.raises(ValueError, match="Unsupported file format"):
            await whisper_service.transcribe_file(
                file_content=b"audio",
                filename="test.xyz",
                language="en"
            )
    
    @pytest.mark.asyncio
    async def test_transcribe_file_size_exceeded(self, whisper_service):
        """Test that file size validation works"""
        # Create large file content (26MB)
        large_content = b"x" * (26 * 1024 * 1024)
        
        with pytest.raises(ValueError, match="exceeds maximum"):
            await whisper_service.transcribe_file(
                file_content=large_content,
                filename="test.mp3",
                language="en"
            )
    
    @pytest.mark.asyncio
    async def test_transcribe_file_api_error(self, whisper_service, mock_openai_client):
        """Test handling of API errors"""
        mock_openai_client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await whisper_service.transcribe_file(
                file_content=b"audio",
                filename="test.mp3",
                language="en"
            )
    
    @pytest.mark.asyncio
    async def test_transcribe_file_cleanup_temp_file(self, whisper_service, mock_openai_client):
        """Test that temporary files are cleaned up"""
        mock_transcript = Mock()
        mock_transcript.text = "Test"
        mock_transcript.language = "en"
        mock_transcript.duration = None
        mock_openai_client.audio.transcriptions.create.return_value = mock_transcript
        
        # Mock file operations
        with patch('os.fdopen') as mock_fdopen, \
             patch('os.path.exists') as mock_exists, \
             patch('os.unlink') as mock_unlink, \
             patch('builtins.open', create=True) as mock_open:
            # Setup mocks
            mock_file = Mock()
            mock_fdopen.return_value.__enter__.return_value = mock_file
            mock_open.return_value.__enter__.return_value = BytesIO(b"audio")
            mock_exists.return_value = True
            
            await whisper_service.transcribe_file(
                file_content=b"audio",
                filename="test.mp3",
                language="en"
            )
            
            # Verify cleanup was attempted (unlink should be called)
            assert mock_unlink.called
    
    @pytest.mark.asyncio
    async def test_transcribe_from_url_success(self, whisper_service, mock_openai_client):
        """Test successful URL transcription"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = b"audio content"
        mock_response.headers = {
            "Content-Disposition": 'attachment; filename="audio.mp3"',
            "Content-Type": "audio/mpeg"
        }
        mock_response.raise_for_status = Mock()
        
        # Mock OpenAI response
        mock_transcript = Mock()
        mock_transcript.text = "Transcribed from URL"
        mock_transcript.language = "en"
        mock_transcript.duration = 5.0
        mock_openai_client.audio.transcriptions.create.return_value = mock_transcript
        
        # Mock httpx - patch at the import location
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_async_client.return_value = mock_client
            
            text, language, duration = await whisper_service.transcribe_from_url(
                audio_url="https://example.com/audio.mp3",
                language="en"
            )
            
            assert text == "Transcribed from URL"
            assert language == "en"
            assert duration == 5.0
    
    @pytest.mark.asyncio
    async def test_transcribe_from_url_filename_detection(self, whisper_service, mock_openai_client):
        """Test filename detection from URL and headers"""
        mock_response = Mock()
        mock_response.content = b"audio"
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        
        mock_transcript = Mock()
        mock_transcript.text = "Test"
        mock_transcript.language = "en"
        mock_transcript.duration = None
        mock_openai_client.audio.transcriptions.create.return_value = mock_transcript
        
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_async_client.return_value = mock_client
            
            # Test URL with filename
            await whisper_service.transcribe_from_url(
                audio_url="https://example.com/audio.wav?param=value",
                language="en"
            )
            
            # Verify the file was transcribed (should use .wav from URL)
            assert mock_openai_client.audio.transcriptions.create.called
    
    @pytest.mark.asyncio
    async def test_transcribe_from_url_content_type_detection(self, whisper_service, mock_openai_client):
        """Test MIME type to extension mapping"""
        mock_response = Mock()
        mock_response.content = b"audio"
        mock_response.headers = {
            "Content-Type": "audio/mp4"  # Should map to .m4a
        }
        mock_response.raise_for_status = Mock()
        
        mock_transcript = Mock()
        mock_transcript.text = "Test"
        mock_transcript.language = "en"
        mock_transcript.duration = None
        mock_openai_client.audio.transcriptions.create.return_value = mock_transcript
        
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_async_client.return_value = mock_client
            
            await whisper_service.transcribe_from_url(
                audio_url="https://example.com/audio",
                language="en"
            )
            
            # Verify transcription was called
            assert mock_openai_client.audio.transcriptions.create.called
    
    @pytest.mark.asyncio
    async def test_transcribe_from_url_http_error(self, whisper_service):
        """Test handling of HTTP errors"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_async_client.return_value = mock_client
            
            with pytest.raises(Exception, match="HTTP 404"):
                await whisper_service.transcribe_from_url(
                    audio_url="https://example.com/notfound.mp3",
                    language="en"
                )

