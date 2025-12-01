"""
Unit tests for DXF Generator Service
"""

import pytest
import io
from app.services.dxf_generator_service import DXFGeneratorService
from app.schemas.parser import ParsedInstruction, CADFileType


@pytest.fixture
def dxf_generator_service():
    """Create DXF generator service instance"""
    return DXFGeneratorService()


@pytest.fixture
def sample_instructions():
    """Sample parsed instructions for testing"""
    return [
        ParsedInstruction(
            command="line",
            parameters={"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 100}},
            confidence=0.95
        ),
        ParsedInstruction(
            command="circle",
            parameters={"center": {"x": 50, "y": 50}, "radius": 25},
            confidence=0.90
        ),
        ParsedInstruction(
            command="rectangle",
            parameters={"corner": {"x": 10, "y": 10}, "width": 80, "height": 60},
            confidence=0.85
        ),
    ]


class TestDXFGeneratorService:
    """Test DXFGeneratorService methods"""
    
    def test_init(self, dxf_generator_service):
        """Test service initialization"""
        from ezdxf import units
        assert dxf_generator_service is not None
        assert dxf_generator_service.dxf_version == 'R2010'
        assert dxf_generator_service.units == units.MM  # MM
    
    def test_is_configured(self, dxf_generator_service):
        """Test service configuration check"""
        assert dxf_generator_service.is_configured() is True
    
    def test_generate_dxf_success(self, dxf_generator_service, sample_instructions):
        """Test successful DXF generation"""
        dxf_bytes = dxf_generator_service.generate_dxf(sample_instructions)
        
        assert dxf_bytes is not None
        assert isinstance(dxf_bytes, bytes)
        assert len(dxf_bytes) > 0
        
        # Verify it's a valid DXF file (should start with DXF header)
        dxf_content = dxf_bytes.decode('utf-8', errors='ignore')
        assert '0' in dxf_content  # DXF files contain section markers
    
    def test_generate_dxf_empty_instructions(self, dxf_generator_service):
        """Test DXF generation with empty instructions"""
        with pytest.raises(ValueError, match="No instructions provided"):
            dxf_generator_service.generate_dxf([])
    
    def test_generate_dxf_single_line(self, dxf_generator_service):
        """Test DXF generation with single line"""
        instructions = [
            ParsedInstruction(
                command="line",
                parameters={"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 100}},
                confidence=0.95
            )
        ]
        
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        assert dxf_bytes is not None
        assert len(dxf_bytes) > 0
    
    def test_generate_dxf_single_circle(self, dxf_generator_service):
        """Test DXF generation with single circle"""
        instructions = [
            ParsedInstruction(
                command="circle",
                parameters={"center": {"x": 50, "y": 50}, "radius": 25},
                confidence=0.90
            )
        ]
        
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        assert dxf_bytes is not None
        assert len(dxf_bytes) > 0
    
    def test_generate_dxf_rectangle(self, dxf_generator_service):
        """Test DXF generation with rectangle"""
        instructions = [
            ParsedInstruction(
                command="rectangle",
                parameters={"corner": {"x": 10, "y": 10}, "width": 80, "height": 60},
                confidence=0.85
            )
        ]
        
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        assert dxf_bytes is not None
        assert len(dxf_bytes) > 0
    
    def test_generate_dxf_arc(self, dxf_generator_service):
        """Test DXF generation with arc"""
        instructions = [
            ParsedInstruction(
                command="arc",
                parameters={
                    "center": {"x": 50, "y": 50},
                    "radius": 30,
                    "start_angle": 0,
                    "end_angle": 90
                },
                confidence=0.80
            )
        ]
        
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        assert dxf_bytes is not None
        assert len(dxf_bytes) > 0
    
    def test_generate_dxf_polyline(self, dxf_generator_service):
        """Test DXF generation with polyline"""
        instructions = [
            ParsedInstruction(
                command="polyline",
                parameters={
                    "points": [
                        {"x": 0, "y": 0},
                        {"x": 50, "y": 0},
                        {"x": 50, "y": 50},
                        {"x": 0, "y": 50}
                    ],
                    "close": True
                },
                confidence=0.85
            )
        ]
        
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        assert dxf_bytes is not None
        assert len(dxf_bytes) > 0
    
    def test_generate_dxf_unsupported_command(self, dxf_generator_service):
        """Test DXF generation with unsupported command"""
        instructions = [
            ParsedInstruction(
                command="unsupported_command",
                parameters={},
                confidence=0.50
            ),
            ParsedInstruction(
                command="line",
                parameters={"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 100}},
                confidence=0.95
            )
        ]
        
        # Should still generate DXF with supported commands
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        assert dxf_bytes is not None
        assert len(dxf_bytes) > 0
    
    def test_validate_dxf_valid(self, dxf_generator_service, sample_instructions):
        """Test DXF validation with valid file"""
        dxf_bytes = dxf_generator_service.generate_dxf(sample_instructions)
        is_valid, error_msg = dxf_generator_service.validate_dxf(dxf_bytes)
        
        assert is_valid is True
        assert error_msg is None
    
    def test_validate_dxf_invalid(self, dxf_generator_service):
        """Test DXF validation with invalid file"""
        invalid_bytes = b"Invalid DXF content"
        is_valid, error_msg = dxf_generator_service.validate_dxf(invalid_bytes)
        
        assert is_valid is False
        assert error_msg is not None
    
    def test_extract_point_from_dict(self, dxf_generator_service):
        """Test point extraction from dictionary"""
        params = {"start": {"x": 10, "y": 20}}
        point = dxf_generator_service._extract_point(params, "start")
        assert point == (10.0, 20.0)
    
    def test_extract_point_from_list(self, dxf_generator_service):
        """Test point extraction from list"""
        params = {"start": [10, 20]}
        point = dxf_generator_service._extract_point(params, "start")
        assert point == (10.0, 20.0)
    
    def test_extract_point_default(self, dxf_generator_service):
        """Test point extraction with default value"""
        params = {}
        point = dxf_generator_service._extract_point(params, "start", (5.0, 5.0))
        assert point == (5.0, 5.0)
    
    def test_extract_number(self, dxf_generator_service):
        """Test number extraction"""
        params = {"radius": 25.5}
        radius = dxf_generator_service._extract_number(params, "radius")
        assert radius == 25.5
    
    def test_extract_number_string(self, dxf_generator_service):
        """Test number extraction from string"""
        params = {"radius": "25.5"}
        radius = dxf_generator_service._extract_number(params, "radius")
        assert radius == 25.5
    
    def test_extract_number_default(self, dxf_generator_service):
        """Test number extraction with default value"""
        params = {}
        radius = dxf_generator_service._extract_number(params, "radius", 10.0)
        assert radius == 10.0
    
    def test_circle_invalid_radius(self, dxf_generator_service):
        """Test circle with invalid radius (should use default)"""
        instructions = [
            ParsedInstruction(
                command="circle",
                parameters={"center": {"x": 50, "y": 50}, "radius": -10},
                confidence=0.90
            )
        ]
        
        # Should still generate DXF (with default radius)
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        assert dxf_bytes is not None
        assert len(dxf_bytes) > 0
    
    def test_polyline_insufficient_points(self, dxf_generator_service):
        """Test polyline with insufficient points"""
        instructions = [
            ParsedInstruction(
                command="polyline",
                parameters={"points": [{"x": 0, "y": 0}]},  # Only one point
                confidence=0.85
            ),
            ParsedInstruction(
                command="line",
                parameters={"start": {"x": 0, "y": 0}, "end": {"x": 100, "y": 100}},
                confidence=0.95
            )
        ]
        
        # Should still generate DXF (skip invalid polyline, process line)
        dxf_bytes = dxf_generator_service.generate_dxf(instructions)
        assert dxf_bytes is not None
        assert len(dxf_bytes) > 0

