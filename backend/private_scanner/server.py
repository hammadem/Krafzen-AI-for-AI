"""Private operator-controlled scanner; no storage or customer file logging."""
import asyncio
import hashlib
import hmac
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import UTC, datetime

from fastapi import FastAPI, Header, HTTPException, Request

TOKEN=os.environ.get("PRIVATE_SCANNER_TOKEN","")
if len(TOKEN)<32:
    raise RuntimeError("PRIVATE_SCANNER_TOKEN must be at least 32 characters")
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
slot=asyncio.Lock()
LIMIT=40*1024*1024

def authorize(value):
    if not hmac.compare_digest(value or "", "Bearer "+TOKEN):
        raise HTTPException(status_code=401,detail="Unauthorized")

def run_scan(path):
    env={**os.environ,"LC_ALL":"C","TZ":"UTC"}
    version=subprocess.run(["clamscan","--version"],capture_output=True,text=True,timeout=5,check=True,env=env).stdout.strip()
    parts=version.split("/",2)
    if len(parts)!=3 or not parts[0].startswith("ClamAV ") or not parts[1].isdigit():
        raise RuntimeError("Signature metadata absent")
    published=datetime.strptime(parts[2].strip(),"%a %b %d %H:%M:%S %Y").replace(tzinfo=UTC)
    if not -86400<=(datetime.now(UTC)-published).total_seconds()<=3*86400:
        raise RuntimeError("Signature metadata stale")
    result=subprocess.run(["clamscan","--no-summary","--official-db-only=yes","--fail-if-cvd-older-than=3",
        "--max-filesize=50M","--max-scansize=150M","--alert-exceeds-max=yes","--alert-encrypted=yes",str(path)],
        capture_output=True,timeout=60,check=False,env=env)
    if result.returncode not in (0,1):
        raise RuntimeError("Scanner failure")
    return ("clean" if result.returncode==0 else "rejected"),version

@app.get("/health")
async def health(authorization:str|None=Header(default=None)):
    authorize(authorization)
    if slot.locked():
        raise HTTPException(status_code=429,detail="Scanner busy")
    async with slot:
        try:
            with tempfile.TemporaryDirectory(prefix="scanner-check-") as directory:
                path=Path(directory)/"benign"
                path.write_bytes(b"KRAFZEN synthetic scanner health check")
                clean,version=await asyncio.to_thread(run_scan,path)
                # Official benign EICAR test signature, not executable malware.
                path.write_bytes(b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*")
                rejected,_=await asyncio.to_thread(run_scan,path)
                if clean!="clean" or rejected!="rejected":
                    raise RuntimeError("Scanner self-test failed")
            return {"status":"verified","benign":"clean","eicar":"rejected","signature_version":version}
        except Exception as exc:
            raise HTTPException(status_code=503,detail="Scanner self-test failed") from exc

@app.post("/scan")
async def scan(request:Request,authorization:str|None=Header(default=None)):
    authorize(authorization)
    if request.headers.get("content-type")!="application/octet-stream":
        raise HTTPException(status_code=415,detail="Binary body required")
    try: size=int(request.headers.get("content-length",""))
    except ValueError: raise HTTPException(status_code=411,detail="Content length required")
    if not 0<size<=LIMIT:
        raise HTTPException(status_code=413,detail="File size unsupported")
    if slot.locked():
        raise HTTPException(status_code=429,detail="Scanner busy")
    async with slot:
        with tempfile.TemporaryDirectory(prefix="scanner-input-") as directory:
            path=Path(directory)/"upload"
            digest=hashlib.sha256(); actual=0
            with path.open("wb") as f:
                async for chunk in request.stream():
                    actual+=len(chunk)
                    if actual>size or actual>LIMIT:
                        raise HTTPException(status_code=413,detail="Body too large")
                    digest.update(chunk);f.write(chunk)
            if actual!=size:
                raise HTTPException(status_code=422,detail="Incomplete body")
            try: verdict,version=await asyncio.to_thread(run_scan,path)
            except Exception as exc:
                raise HTTPException(status_code=503,detail="Scanner unavailable") from exc
            return {"verdict":verdict,"bytes":actual,"sha256":digest.hexdigest(),"signature_version":version}
