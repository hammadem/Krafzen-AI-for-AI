"""No customer data leaves the API unless a specific approved scanner is configured."""
import hashlib
import hmac
import os
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException


def remote_requested():
    return bool(os.getenv("PRIVATE_SCANNER_URL") or os.getenv("PRIVATE_SCANNER_TOKEN"))


def _config():
    url = os.getenv("PRIVATE_SCANNER_URL", "").strip()
    token = os.getenv("PRIVATE_SCANNER_TOKEN", "")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in ("", "/")
            or len(token) < 32 or os.getenv("PRIVATE_SCANNER_US_PROCESSING_APPROVED") != "true"):
        raise HTTPException(status_code=503, detail="Approved private scanner is not configured")
    return url.rstrip("/"), token


def scan_remote(path: Path):
    url, token = _config()
    size = path.stat().st_size
    if not 0 < size <= 40*1024*1024:
        raise HTTPException(status_code=422,detail="Scanner input exceeds supported limits")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        with path.open("rb") as source, httpx.Client(timeout=httpx.Timeout(90,connect=5),
                follow_redirects=False,trust_env=False) as client:
            with client.stream("POST",url+"/scan",headers={"Authorization":"Bearer "+token,
                "Content-Type":"application/octet-stream","Content-Length":str(size)},
                content=source) as response:
                if response.status_code!=200:
                    raise ValueError("Scanner unavailable")
                payload=bytearray()
                for block in response.iter_bytes():
                    payload.extend(block)
                    if len(payload)>4096: raise ValueError("Oversized scanner response")
        import json
        verdict=json.loads(payload)
        from app.services.scanner_readiness import signature_metadata_current
        if (not isinstance(verdict,dict) or not isinstance(verdict.get("sha256"),str)
                or not hmac.compare_digest(digest,verdict["sha256"])
                or verdict.get("bytes")!=size or not signature_metadata_current(verdict.get("signature_version"))
                or verdict.get("verdict") not in ("clean","rejected")):
            raise ValueError("Invalid scanner response")
    except Exception as exc:
        raise HTTPException(status_code=503,detail="Approved private scanner could not validate the file") from exc
    if verdict["verdict"]!="clean":
        raise HTTPException(status_code=422,detail="Upload rejected by malware scanner or scan safety limits")
