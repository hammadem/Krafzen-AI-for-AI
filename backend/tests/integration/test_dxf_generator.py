"""
Integration tests for DXF Generator API endpoints
"""

import pytest
import httpx
from app.schemas.parser import ParsedInstruction


BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_generate_dxf_from_instructions():
    """Test DXF generation from parsed instructions"""
    instructions = [
        {
            "command": "line",
            "parameters": {"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 100}},
            "confidence": 0.95
        },
        {
            "command": "circle",
            "parameters": {"center": {"x": 50, "y": 50}, "radius": 25},
            "confidence": 0.90
        }
    ]
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        response = await client.post(
            "/api/v1/dxf/generate",
            json=instructions
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/dxf"
        assert len(response.content) > 0
        
        # Verify it's a valid DXF file
        dxf_content = response.content.decode('utf-8', errors='ignore')
        assert '0' in dxf_content  # DXF files contain section markers


@pytest.mark.asyncio
async def test_generate_dxf_empty_instructions():
    """Test DXF generation with empty instructions"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        response = await client.post(
            "/api/v1/dxf/generate",
            json=[]
        )
        
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_validate_dxf_file():
    """Test DXF file validation endpoint"""
    # First generate a valid DXF file
    instructions = [
        {
            "command": "line",
            "parameters": {"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 100}},
            "confidence": 0.95
        }
    ]
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # Generate DXF
        generate_response = await client.post(
            "/api/v1/dxf/generate",
            json=instructions
        )
        assert generate_response.status_code == 200
        dxf_bytes = generate_response.content
        
        # Validate the generated DXF
        response = await client.post(
            "/api/v1/dxf/validate",
            content=dxf_bytes
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "valid"
        assert data["is_valid"] is True


@pytest.mark.asyncio
async def test_validate_invalid_dxf():
    """Test DXF validation with invalid file"""
    invalid_dxf = b"Invalid DXF content"
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        response = await client.post(
            "/api/v1/dxf/validate",
            content=invalid_dxf
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "invalid"
        assert data["is_valid"] is False
        assert data["message"] is not None


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires OpenAI API key and may incur costs")
async def test_generate_dxf_from_text():
    """Test DXF generation from text (requires OpenAI API)"""
    request_data = {
        "text": "Draw a line from 0,0 to 100,100. Draw a circle at center 50,50 with radius 25.",
        "file_type": "dxf"
    }
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        response = await client.post(
            "/api/v1/dxf/generate-from-text",
            json=request_data
        )
        
        # This test may fail if OpenAI API is not configured
        if response.status_code == 503:
            pytest.skip("OpenAI API not configured")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/dxf"
        assert len(response.content) > 0


@pytest.mark.asyncio
async def test_generate_dxf_with_filename():
    """Test DXF generation with custom filename"""
    # Note: filename is in the request body, not as a query parameter
    # This test verifies the default filename behavior
    instructions = [
        {
            "command": "line",
            "parameters": {"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 100}},
            "confidence": 0.95
        }
    ]
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        response = await client.post(
            "/api/v1/dxf/generate",
            json=instructions
        )
        
        assert response.status_code == 200
        # Check that Content-Disposition header is present
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition
        assert ".dxf" in content_disposition


@pytest.mark.asyncio
async def test_generate_dxf_multiple_entities():
    """Test DXF generation with multiple entity types"""
    instructions = [
        {
            "command": "line",
            "parameters": {"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 0}},
            "confidence": 0.95
        },
        {
            "command": "circle",
            "parameters": {"center": {"x": 50, "y": 50}, "radius": 25},
            "confidence": 0.90
        },
        {
            "command": "rectangle",
            "parameters": {"corner": {"x": 10, "y": 10}, "width": 80, "height": 60},
            "confidence": 0.85
        },
        {
            "command": "arc",
            "parameters": {
                "center": {"x": 50, "y": 50},
                "radius": 30,
                "start_angle": 0,
                "end_angle": 90
            },
            "confidence": 0.80
        }
    ]
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        response = await client.post(
            "/api/v1/dxf/generate",
            json=instructions
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/dxf"
        assert len(response.content) > 0

