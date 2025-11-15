"""
Unit tests for GPTParserService
Tests use mocks to avoid actual API calls
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from app.services.gpt_parser_service import GPTParserService
from app.schemas.parser import CADFileType, ParsedInstruction


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    with patch('app.services.gpt_parser_service.OpenAI') as mock_openai:
        client_instance = Mock()
        mock_openai.return_value = client_instance
        yield client_instance


@pytest.fixture
def gpt_parser_service(mock_openai_client):
    """Create GPTParserService instance with mocked OpenAI client"""
    with patch('app.services.gpt_parser_service.settings') as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-api-key"
        mock_settings.GPT_MODEL = "gpt-4-turbo-preview"
        mock_settings.GPT_MAX_TOKENS = 2000
        mock_settings.GPT_TEMPERATURE = 0.3
        service = GPTParserService()
        service.client = mock_openai_client
        return service


class TestGPTParserService:
    """Test GPTParserService methods"""
    
    def test_init_without_api_key(self):
        """Test that service raises error when API key is missing"""
        with patch('app.services.gpt_parser_service.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            with pytest.raises(ValueError, match="OPENAI_API_KEY is not configured"):
                GPTParserService()
    
    def test_is_configured(self, gpt_parser_service):
        """Test is_configured method"""
        with patch('app.services.gpt_parser_service.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            assert gpt_parser_service.is_configured() is True
            
            mock_settings.OPENAI_API_KEY = None
            assert gpt_parser_service.is_configured() is False
    
    def test_get_system_prompt_dxf(self, gpt_parser_service):
        """Test system prompt for DXF file type"""
        prompt = gpt_parser_service._get_system_prompt(CADFileType.DXF)
        assert "DXF-compatible" in prompt
        assert "ezdxf" in prompt
    
    def test_get_system_prompt_dwg(self, gpt_parser_service):
        """Test system prompt for DWG file type"""
        prompt = gpt_parser_service._get_system_prompt(CADFileType.DWG)
        assert "DWG-compatible" in prompt
    
    def test_get_system_prompt_revit(self, gpt_parser_service):
        """Test system prompt for Revit file type"""
        prompt = gpt_parser_service._get_system_prompt(CADFileType.REVIT)
        assert "Revit-compatible" in prompt
        assert "BIM" in prompt
    
    @pytest.mark.asyncio
    async def test_parse_text_success(self, gpt_parser_service, mock_openai_client):
        """Test successful text parsing"""
        # Mock GPT-4 response
        mock_response_data = {
            "instructions": [
                {
                    "command": "circle",
                    "parameters": {"center": {"x": 50, "y": 50}, "radius": 25},
                    "confidence": 0.95
                },
                {
                    "command": "line",
                    "parameters": {"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 100}},
                    "confidence": 0.90
                }
            ]
        }
        
        mock_message = Mock()
        mock_message.content = json.dumps(mock_response_data)
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Call parse_text
        instructions, raw_response = await gpt_parser_service.parse_text(
            text="Draw a circle with radius 25 at center 50, 50. Draw a line from 0,0 to 100,100.",
            file_type=CADFileType.DXF
        )
        
        # Verify results
        assert len(instructions) == 2
        assert instructions[0].command == "circle"
        assert instructions[0].parameters["center"]["x"] == 50
        assert instructions[0].confidence == 0.95
        assert instructions[1].command == "line"
        assert instructions[1].confidence == 0.90
        
        # Verify OpenAI was called correctly
        assert mock_openai_client.chat.completions.create.called
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4-turbo-preview"
        assert call_args.kwargs["max_tokens"] == 2000
        assert call_args.kwargs["temperature"] == 0.3
        assert call_args.kwargs["response_format"] == {"type": "json_object"}
        
        # Verify messages
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Draw a circle" in messages[1]["content"]
    
    @pytest.mark.asyncio
    async def test_parse_text_with_additional_context(self, gpt_parser_service, mock_openai_client):
        """Test parsing with additional context"""
        mock_response_data = {"instructions": [{"command": "rectangle", "parameters": {}, "confidence": 1.0}]}
        mock_message = Mock()
        mock_message.content = json.dumps(mock_response_data)
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        instructions, _ = await gpt_parser_service.parse_text(
            text="Create a rectangle",
            file_type=CADFileType.DXF,
            additional_context="Previous drawing had a circle"
        )
        
        assert len(instructions) == 1
        # Verify context was included in prompt
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert "Previous drawing had a circle" in messages[1]["content"]
    
    @pytest.mark.asyncio
    async def test_parse_text_list_response_format(self, gpt_parser_service, mock_openai_client):
        """Test parsing when GPT returns a list instead of object with instructions"""
        # Some GPT responses might return a list directly
        mock_response_data = [
            {"command": "circle", "parameters": {"radius": 10}, "confidence": 0.9}
        ]
        
        mock_message = Mock()
        mock_message.content = json.dumps(mock_response_data)
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        instructions, _ = await gpt_parser_service.parse_text(
            text="Draw a circle",
            file_type=CADFileType.DXF
        )
        
        assert len(instructions) == 1
        assert instructions[0].command == "circle"
    
    @pytest.mark.asyncio
    async def test_parse_text_single_instruction_response(self, gpt_parser_service, mock_openai_client):
        """Test parsing when GPT returns a single instruction object"""
        mock_response_data = {"command": "line", "parameters": {}, "confidence": 1.0}
        
        mock_message = Mock()
        mock_message.content = json.dumps(mock_response_data)
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        instructions, _ = await gpt_parser_service.parse_text(
            text="Draw a line",
            file_type=CADFileType.DXF
        )
        
        assert len(instructions) == 1
        assert instructions[0].command == "line"
    
    @pytest.mark.asyncio
    async def test_parse_text_invalid_json(self, gpt_parser_service, mock_openai_client):
        """Test handling of invalid JSON response"""
        mock_message = Mock()
        mock_message.content = "This is not valid JSON {"
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(ValueError, match="Invalid JSON response"):
            await gpt_parser_service.parse_text(
                text="Draw something",
                file_type=CADFileType.DXF
            )
    
    @pytest.mark.asyncio
    async def test_parse_text_no_instructions(self, gpt_parser_service, mock_openai_client):
        """Test handling when no valid instructions are parsed"""
        mock_response_data = {"instructions": []}
        
        mock_message = Mock()
        mock_message.content = json.dumps(mock_response_data)
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(ValueError, match="No valid instructions parsed"):
            await gpt_parser_service.parse_text(
                text="Draw something",
                file_type=CADFileType.DXF
            )
    
    @pytest.mark.asyncio
    async def test_parse_text_invalid_instruction_skipped(self, gpt_parser_service, mock_openai_client):
        """Test that invalid instructions are handled (may use defaults)"""
        mock_response_data = {
            "instructions": [
                {"command": "valid", "parameters": {}, "confidence": 1.0},
                {"invalid": "instruction"},  # Missing required fields - will use defaults
                {"command": "another", "parameters": {}, "confidence": 0.8}
            ]
        }
        
        mock_message = Mock()
        mock_message.content = json.dumps(mock_response_data)
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        instructions, _ = await gpt_parser_service.parse_text(
            text="Draw multiple things",
            file_type=CADFileType.DXF
        )
        
        # Should have 3 instructions (invalid one uses defaults: empty command, default confidence)
        assert len(instructions) == 3
        assert instructions[0].command == "valid"
        assert instructions[1].command == ""  # Default for missing command
        assert instructions[2].command == "another"
    
    @pytest.mark.asyncio
    async def test_parse_text_api_error(self, gpt_parser_service, mock_openai_client):
        """Test handling of API errors"""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await gpt_parser_service.parse_text(
                text="Draw something",
                file_type=CADFileType.DXF
            )
    
    @pytest.mark.asyncio
    async def test_parse_text_default_confidence(self, gpt_parser_service, mock_openai_client):
        """Test that missing confidence defaults to 0.8"""
        mock_response_data = {
            "instructions": [
                {"command": "circle", "parameters": {}}  # No confidence field
            ]
        }
        
        mock_message = Mock()
        mock_message.content = json.dumps(mock_response_data)
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        instructions, _ = await gpt_parser_service.parse_text(
            text="Draw a circle",
            file_type=CADFileType.DXF
        )
        
        assert instructions[0].confidence == 0.8  # Default value

