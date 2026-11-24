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
