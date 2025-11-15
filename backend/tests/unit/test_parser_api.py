"""
Unit tests for parser API endpoints
Tests use mocks to avoid actual API calls
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from app.main import app
from app.schemas.parser import CADFileType, ParsedInstruction


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def mock_gpt_parser_service():
    """Mock GPT parser service"""
    with patch('app.api.parser.gpt_parser_service') as mock_service:
        yield mock_service


class TestParserAPI:
    """Test parser API endpoints"""
    
    def test_parse_text_success(self, client, mock_gpt_parser_service):
        """Test successful text parsing"""
        # Mock parser service response
        mock_instructions = [
            ParsedInstruction(
                command="circle",
                parameters={"center": {"x": 50, "y": 50}, "radius": 25},
                confidence=0.95
            )
        ]
        mock_gpt_parser_service.parse_text = AsyncMock(
            return_value=(mock_instructions, '{"instructions": [...]}')
        )
        
        request_data = {
            "text": "Draw a circle with radius 25 at center 50, 50",
            "file_type": "dxf"
        }
        
        response = client.post("/api/v1/parse", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["instructions"]) == 1
        assert data["instructions"][0]["command"] == "circle"
        assert data["file_type"] == "dxf"
        assert "raw_gpt_response" in data
        
        # Verify service was called
        mock_gpt_parser_service.parse_text.assert_called_once()
        call_args = mock_gpt_parser_service.parse_text.call_args
        assert call_args.kwargs["text"] == request_data["text"]
        assert call_args.kwargs["file_type"] == CADFileType.DXF
    
    def test_parse_text_default_file_type(self, client, mock_gpt_parser_service):
        """Test parsing with default file type (DXF)"""
        mock_instructions = [
            ParsedInstruction(command="line", parameters={}, confidence=1.0)
        ]
        mock_gpt_parser_service.parse_text = AsyncMock(
            return_value=(mock_instructions, '{}')
        )
        
        request_data = {"text": "Draw a line"}  # No file_type specified
        
        response = client.post("/api/v1/parse", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["file_type"] == "dxf"  # Default
        
        # Verify default was used
        call_args = mock_gpt_parser_service.parse_text.call_args
        assert call_args.kwargs["file_type"] == CADFileType.DXF
    
    def test_parse_text_with_additional_context(self, client, mock_gpt_parser_service):
        """Test parsing with additional context"""
        mock_instructions = [
            ParsedInstruction(command="rectangle", parameters={}, confidence=1.0)
        ]
        mock_gpt_parser_service.parse_text = AsyncMock(
            return_value=(mock_instructions, '{}')
        )
        
        request_data = {
            "text": "Create a rectangle",
            "file_type": "dwg",
            "additional_context": "Previous drawing had a circle"
        }
        
        response = client.post("/api/v1/parse", json=request_data)
        
        assert response.status_code == 200
        
        # Verify context was passed
        call_args = mock_gpt_parser_service.parse_text.call_args
        assert call_args.kwargs["additional_context"] == "Previous drawing had a circle"
        assert call_args.kwargs["file_type"] == CADFileType.DWG
    
    def test_parse_text_all_file_types(self, client, mock_gpt_parser_service):
        """Test parsing with different file types"""
        mock_instructions = [
            ParsedInstruction(command="test", parameters={}, confidence=1.0)
        ]
        mock_gpt_parser_service.parse_text = AsyncMock(
            return_value=(mock_instructions, '{}')
        )
        
        file_types = ["dxf", "dwg", "revit"]
        for file_type in file_types:
            request_data = {"text": "Test", "file_type": file_type}
            response = client.post("/api/v1/parse", json=request_data)
            assert response.status_code == 200
            assert response.json()["file_type"] == file_type
    
    def test_parse_text_service_not_configured(self, client):
        """Test error when GPT parser service is not configured"""
        with patch('app.api.parser.gpt_parser_service', None):
            request_data = {"text": "Draw something"}
            response = client.post("/api/v1/parse", json=request_data)
            
            assert response.status_code == 503
            response_data = response.json()
            assert "not configured" in (response_data.get("detail") or response_data.get("message", "")).lower()
    
    def test_parse_text_validation_error(self, client, mock_gpt_parser_service):
        """Test handling of validation errors from service"""
        mock_gpt_parser_service.parse_text = AsyncMock(
            side_effect=ValueError("Invalid text format")
        )
        
        request_data = {"text": ""}  # Empty text might cause validation error
        response = client.post("/api/v1/parse", json=request_data)
        
        # Validation errors can return 400 or 422
        assert response.status_code in [400, 422, 500]
    
    def test_parse_text_service_error(self, client, mock_gpt_parser_service):
        """Test handling of service errors"""
        mock_gpt_parser_service.parse_text = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        request_data = {"text": "Draw something"}
        response = client.post("/api/v1/parse", json=request_data)
        
        assert response.status_code == 500
        response_data = response.json()
        assert "failed" in (response_data.get("detail") or response_data.get("message", "")).lower()
    
    def test_parse_text_missing_text(self, client):
        """Test error when text is missing"""
        request_data = {"file_type": "dxf"}  # Missing text
        response = client.post("/api/v1/parse", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_parse_transcription_endpoint(self, client, mock_gpt_parser_service):
        """Test parse-transcription convenience endpoint"""
        mock_instructions = [
            ParsedInstruction(command="circle", parameters={}, confidence=1.0)
        ]
        mock_gpt_parser_service.parse_text = AsyncMock(
            return_value=(mock_instructions, '{}')
        )
        
        request_data = {
            "transcription_text": "Draw a circle",
            "file_type": "dxf"
        }
        
        response = client.post("/api/v1/parse-transcription", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify service was called with transcription text
        call_args = mock_gpt_parser_service.parse_text.call_args
        assert call_args.kwargs["text"] == "Draw a circle"
    
    def test_parse_transcription_defaults(self, client, mock_gpt_parser_service):
        """Test parse-transcription with default values"""
        mock_instructions = [
            ParsedInstruction(command="line", parameters={}, confidence=1.0)
        ]
        mock_gpt_parser_service.parse_text = AsyncMock(
            return_value=(mock_instructions, '{}')
        )
        
        # Only provide transcription_text, use defaults for others
        request_data = {"transcription_text": "Draw a line"}
        
        response = client.post("/api/v1/parse-transcription", json=request_data)
        
        assert response.status_code == 200
        
        # Verify defaults were used
        call_args = mock_gpt_parser_service.parse_text.call_args
        assert call_args.kwargs["file_type"] == CADFileType.DXF
        assert call_args.kwargs["additional_context"] is None

