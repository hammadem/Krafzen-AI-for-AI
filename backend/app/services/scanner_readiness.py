"""Lightweight signature age diagnostic; never loads the scanner engine on public health requests."""
import os
import shutil
import subprocess
from datetime import UTC,datetime
from threading import Lock
from time import monotonic

_lock=Lock()
_cache=None

def signature_metadata_current(text,now=None):
    try:
        # ClamAV --version emits engine/version/signature date.
        engine,serial,date=text.strip().split("/",2)
        if not engine.startswith("ClamAV ") or not serial.isdigit(): return False
        published=datetime.strptime(date.strip(),"%a %b %d %H:%M:%S %Y").replace(tzinfo=UTC)
        age=((now or datetime.now(UTC))-published).total_seconds()
        return -86400<=age<=3*86400
    except (TypeError,AttributeError,ValueError):
        return False

def scanner_status():
    global _cache
    with _lock:
        now=monotonic()
        if _cache and now-_cache[0]<60: return dict(_cache[1])
        from app.services.private_scanner_client import remote_requested, _config
        if remote_requested():
            result={"scanner_binary_detected":False,"scanner_signature_metadata_current":False,"private_scanner_verified":False}
            try:
                import httpx
                url,token=_config()
                with httpx.Client(timeout=90,follow_redirects=False,trust_env=False) as client:
                    response=client.get(url+"/health",headers={"Authorization":"Bearer "+token})
                    response.raise_for_status()
                    evidence=response.json()
                valid=(evidence.get("status")=="verified" and evidence.get("benign")=="clean" and evidence.get("eicar")=="rejected" and signature_metadata_current(evidence.get("signature_version")))
                result.update(scanner_binary_detected=valid,scanner_signature_metadata_current=valid,private_scanner_verified=valid)
            except Exception:
                pass
            _cache=(now,result)
            return dict(result)
        binary=shutil.which(os.getenv("CLAMSCAN_CMD","clamscan"))
        result={"scanner_binary_detected":bool(binary),"scanner_signature_metadata_current":False}
        if binary:
            try:
                version=subprocess.run([binary,"--version"],capture_output=True,text=True,timeout=3,check=False,
                    env={**os.environ,"LC_ALL":"C","TZ":"UTC"})
                result["scanner_signature_metadata_current"]=version.returncode==0 and signature_metadata_current(version.stdout)
            except (OSError,subprocess.TimeoutExpired): pass
        _cache=(now,result)
        return dict(result)
