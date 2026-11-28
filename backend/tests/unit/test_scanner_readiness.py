from datetime import UTC,datetime
from unittest.mock import patch
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.services.scanner_readiness import signature_metadata_current
from app.services import import_service

def test_signature_metadata_age_and_missing():
    now=datetime(2026,11,25,0,0,tzinfo=UTC)
    assert signature_metadata_current("ClamAV 1.4.7/12345/Tue Nov 24 12:00:00 2026",now)
    assert not signature_metadata_current("ClamAV 1.4.7/12345/Fri Nov 20 12:00:00 2026",now)
    assert not signature_metadata_current("ClamAV 1.4.7",now)

def test_scan_is_bounded_and_rejects_unavailable(tmp_path):
    path=tmp_path/"test.dxf";path.write_bytes(b"test")
    with patch.object(import_service.shutil,"which",return_value="/usr/bin/clamscan"),patch.object(import_service.subprocess,"run",return_value=SimpleNamespace(returncode=2)) as run:
        with pytest.raises(HTTPException) as exc: import_service._scan_file(path)
        assert exc.value.status_code==503
        assert "--fail-if-cvd-older-than=3" in run.call_args.args[0]
        assert "--alert-exceeds-max=yes" in run.call_args.args[0]
    assert import_service._scan_slot.acquire(blocking=False)
    try:
        with patch.object(import_service.shutil,"which",return_value="/usr/bin/clamscan"):
            with pytest.raises(HTTPException) as exc: import_service._scan_file(path)
        assert exc.value.status_code==429
    finally: import_service._scan_slot.release()
