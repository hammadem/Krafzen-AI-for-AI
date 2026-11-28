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
    converter._converter_type="ODA"
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


def test_libredwg_real_cli_contract_and_output_format(tmp_path):
    converter=service.DwgConverterService()
    converter._converter_type="LIBREDWG"
    original=tmp_path/"source.dxf";original.write_bytes(b"test input")
    raw=b"AC1015"+bytes(100)
    def run(cmd,**kwargs):
        output=Path(cmd[cmd.index("-o")+1])
        if cmd[0]=="/dxf2dwg":
            assert "--as=r2000" in cmd
            output.write_bytes(raw)
        else:
            output.write_bytes(b"test-only-dxf")
        return SimpleNamespace(returncode=0)
    import shutil
    with patch.object(converter,"_libredwg_tools",return_value=("/dwg2dxf","/dxf2dwg")), patch.object(service.subprocess,"run",side_effect=run):
        result=converter.convert_dxf_path_to_dwg(str(original))
        try:
            assert Path(result.dwg_path).read_bytes()==raw
            assert converter.convert_dwg_bytes_to_dxf(raw)==b"test-only-dxf"
        finally:
            shutil.rmtree(result.work_dir)
