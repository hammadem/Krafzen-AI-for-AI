from hashlib import sha256
from io import BytesIO
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile

from app.services import import_service as service

@pytest.mark.asyncio
async def test_bridge_scans_rvt_and_delegates_ifc_to_existing_scanned_import():
    raw=bytes.fromhex("D0CF11E0A1B11AE1")+bytes(600)
    source=UploadFile(file=BytesIO(raw),filename="model.rvt")
    ifc=UploadFile(file=BytesIO(b"IFC fixture"),filename="model.ifc")
    uid,pid,jid=map(str,(uuid4(),uuid4(),uuid4()))
    user={"user_id":uid}
    scanned=[]
    def scan(path): scanned.append(path.read_bytes())
    with patch.object(service,"get_job",AsyncMock(return_value={"project_id":pid})), patch.object(service,"get_project",AsyncMock(return_value={"id":pid})), patch.object(service,"_scan_file",side_effect=scan), patch.object(service,"import_ifc_for_job",AsyncMock(return_value={"id":"saved"})) as imported:
        result=await service.import_revit_bridge_for_job(job_id=jid,source=source,upload=ifc,user=user)
    assert result=={"id":"saved"}
    assert scanned==[raw]
    provenance=imported.await_args.kwargs["revit_provenance"]
    assert provenance["source_sha256"]==sha256(raw).hexdigest()
    assert provenance["native_rvt_parsed"] is False
    assert provenance["source_relationship_independently_verified"] is False

@pytest.mark.asyncio
async def test_bridge_rejects_renamed_noncompound_source():
    with patch.object(service,"get_job",AsyncMock(return_value={"project_id":"p"})), patch.object(service,"get_project",AsyncMock(return_value={"id":"p"})), patch.object(service,"import_ifc_for_job",AsyncMock()) as imported:
        with pytest.raises(HTTPException) as error:
            await service.import_revit_bridge_for_job(job_id=str(uuid4()),source=UploadFile(file=BytesIO(b"fake"*200),filename="model.rvt"),upload=UploadFile(file=BytesIO(b""),filename="model.ifc"),user={"user_id":"u"})
    assert error.value.status_code==422
    imported.assert_not_awaited()
