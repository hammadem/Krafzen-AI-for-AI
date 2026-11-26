from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from app.services import dwg_converter_service as service

def test_invalid_header_rejected():
    with pytest.raises(ValueError):
        service.validate_dwg_header(b"renamed dxf"*20)

def test_dwg_conversion_requires_actual_expected_output():
    converter=service.DwgConverterService()
    raw=b"AC1032"+bytes(100)
    def run(cmd,env,root):
        assert cmd[4]=="DXF"
        assert (Path(cmd[1])/"source.dwg").read_bytes()==raw
        (Path(cmd[2])/"source.dxf").write_bytes(b"test-only-dxf")
        return SimpleNamespace(returncode=0)
    with patch.object(converter,"_resolve_converter_cmd_and_ld",return_value=("/oda",None)), patch.object(service,"run_oda_subprocess",side_effect=run):
        assert converter.convert_dwg_bytes_to_dxf(raw)==b"test-only-dxf"
    with patch.object(converter,"_resolve_converter_cmd_and_ld",return_value=("/oda",None)), patch.object(service,"run_oda_subprocess",return_value=SimpleNamespace(returncode=0)):
        with pytest.raises(RuntimeError): converter.convert_dwg_bytes_to_dxf(raw)
