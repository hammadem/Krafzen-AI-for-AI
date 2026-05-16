"""
Bundle ODA File Converter from a .deb URL into backend/.oda_bundle/ for Render/native deploys.

Build-time extraction (render_build_native.sh) may not survive the deploy artifact; this module
can download and extract at runtime when DWG_ODA_DEB_URL is set.
"""
from __future__ import annotations

import io
import logging
import os
import shutil
import subprocess
import tarfile
import threading
from pathlib import Path
from typing import Optional, Tuple

_bundle_lock = threading.Lock()

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BUNDLE_DIR_NAME = ".oda_bundle"
_MANIFEST = "converter_relpath.txt"
_LD_PATH_FILE = "ld_library_path.txt"


def backend_root() -> Path:
    """Resolve backend/ whether cwd is repo root or backend/."""
    here = Path(__file__).resolve().parent.parent.parent
    for candidate in (here, Path.cwd(), Path.cwd() / "backend"):
        if (candidate / "app" / "services").is_dir():
            return candidate
    return here


def bundle_dir(root: Optional[Path] = None) -> Path:
    return (root or backend_root()) / _BUNDLE_DIR_NAME


def _read_bundle(root: Path) -> Tuple[Optional[str], Optional[str]]:
    rel_file = bundle_dir(root) / _MANIFEST
    ld_file = bundle_dir(root) / _LD_PATH_FILE
    if not rel_file.is_file():
        return None, None
    rel = rel_file.read_text(encoding="utf-8").strip()
    if not rel:
        return None, None
    exe = (root / rel).resolve()
    if not exe.is_file():
        logger.warning("ODA manifest points to missing file: %s", exe)
        return None, None
    ld_extra = ld_file.read_text(encoding="utf-8").strip() if ld_file.is_file() else ""
    return str(exe), ld_extra or None


def _write_manifest(root: Path, oda_bin: Path) -> None:
    bdir = bundle_dir(root)
    bdir.mkdir(parents=True, exist_ok=True)
    rel = oda_bin.relative_to(root).as_posix()
    (bdir / _MANIFEST).write_text(rel + "\n", encoding="utf-8")

    lib_dirs: list[str] = []
    for so in bdir.rglob("*.so*"):
        if so.is_file() or so.is_symlink():
            lib_dirs.append(str(so.parent.resolve()))
    ld_extra = ":".join(dict.fromkeys(lib_dirs))
    (bdir / _LD_PATH_FILE).write_text(ld_extra + "\n", encoding="utf-8")
    logger.info("ODA bundle manifest written: exe=%s lib_dirs=%s", rel, len(lib_dirs))


def _find_oda_binary(extract_root: Path) -> Optional[Path]:
    direct = extract_root / "usr" / "bin" / "ODAFileConverter"
    if direct.is_file():
        return direct
    for path in extract_root.rglob("ODAFileConverter*"):
        if path.is_file() and not path.name.endswith(".deb"):
            return path
    return None


def _extract_deb_dpkg(deb_path: Path, dest: Path) -> bool:
    if not shutil.which("dpkg-deb"):
        return False
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["dpkg-deb", "-x", str(deb_path), str(dest)],
        check=True,
        capture_output=True,
    )
    return True


def _extract_deb_ar_tar(deb_path: Path, dest: Path) -> bool:
    if not shutil.which("ar") or not shutil.which("tar"):
        return False
    import tempfile

    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        subprocess.run(["ar", "x", str(deb_path)], cwd=tmp, check=True, capture_output=True)
        data_tars = sorted(tmp_path.glob("data.tar*"))
        if not data_tars:
            return False
        data_tar = data_tars[0]
        name = data_tar.name
        if name.endswith(".xz") or name.endswith(".tar.xz"):
            flag = "-xJf"
        elif name.endswith(".gz") or name.endswith(".tar.gz"):
            flag = "-xzf"
        else:
            flag = "-xf"
        subprocess.run(["tar", flag, str(data_tar), "-C", str(dest)], check=True, capture_output=True)
    return True


def _extract_deb_python(deb_path: Path, dest: Path) -> None:
    """Extract data.tar.* from a .deb using stdlib only (ar + tar/lzma)."""
    dest.mkdir(parents=True, exist_ok=True)
    data_blob: Optional[bytes] = None

    with deb_path.open("rb") as f:
        magic = f.read(8)
        if magic != b"!<arch>\n":
            raise RuntimeError("Not a valid .deb (ar) archive")

        while True:
            header = f.read(60)
            if len(header) < 60:
                break
            name = header[0:16].decode("latin-1").strip()
            try:
                size = int(header[48:58].decode("latin-1").strip() or "0")
            except ValueError:
                break
            payload = f.read(size)
            if size % 2:
                f.read(1)
            if name.startswith("data.tar"):
                data_blob = payload
                break

    if not data_blob:
        raise RuntimeError("No data.tar member found in .deb")

    bio = io.BytesIO(data_blob)
    # tar.xz / tar.gz / plain tar
    for mode in ("r:*", "r:xz", "r:gz", "r:"):
        try:
            bio.seek(0)
            with tarfile.open(fileobj=bio, mode=mode) as tar:
                try:
                    tar.extractall(dest, filter="data")
                except TypeError:
                    tar.extractall(dest)
            return
        except tarfile.TarError:
            continue
    raise RuntimeError("Could not extract data.tar from .deb")


def _extract_deb(deb_path: Path, dest: Path) -> None:
    if _extract_deb_dpkg(deb_path, dest):
        return
    if _extract_deb_ar_tar(deb_path, dest):
        return
    _extract_deb_python(deb_path, dest)


def ensure_oda_bundle(force: bool = False) -> bool:
    """
    Ensure backend/.oda_bundle exists with ODAFileConverter when DWG_ODA_DEB_URL is set.
    Returns True if a converter binary is available after this call.
    """
    with _bundle_lock:
        return _ensure_oda_bundle_locked(force)


def _ensure_oda_bundle_locked(force: bool = False) -> bool:
    root = backend_root()
    url = (getattr(settings, "DWG_ODA_DEB_URL", None) or os.environ.get("DWG_ODA_DEB_URL") or "").strip()

    if not force:
        exe, _ = _read_bundle(root)
        if exe:
            return True

    if not url:
        logger.warning(
            "DWG_ODA_DEB_URL is not set; ODA bundle will not be downloaded. "
            "Set it on Render to a direct HTTPS URL of the Linux x64 .deb."
        )
        return bool(_read_bundle(root)[0])

    bdir = bundle_dir(root)
    deb_local = root / ".oda_download.deb"

    try:
        bdir.mkdir(parents=True, exist_ok=True)
        # Another worker may have finished while we waited
        if not force:
            exe, _ = _read_bundle(root)
            if exe:
                return True

        logger.info("Downloading ODA .deb from DWG_ODA_DEB_URL into %s ...", bdir)
        with httpx.Client(timeout=httpx.Timeout(600.0, connect=60.0), follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with deb_local.open("wb") as out:
                    for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                        out.write(chunk)

        if deb_local.stat().st_size < 1_000_000:
            raise RuntimeError(
                f"Downloaded .deb is too small ({deb_local.stat().st_size} bytes); "
                "check DWG_ODA_DEB_URL (presigned URL may have expired)."
            )

        extract_dest = bdir / "_extract"
        if extract_dest.exists():
            shutil.rmtree(extract_dest)
        extract_dest.mkdir(parents=True)

        _extract_deb(deb_local, extract_dest)
        deb_local.unlink(missing_ok=True)

        oda_bin = _find_oda_binary(extract_dest)
        if not oda_bin:
            raise RuntimeError("ODAFileConverter not found inside extracted .deb")

        oda_bin.chmod(oda_bin.stat().st_mode | 0o111)

        # Merge extract tree into bundle dir (keep manifest at bundle root)
        for item in extract_dest.iterdir():
            target = bdir / item.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(item), str(target))
        shutil.rmtree(extract_dest, ignore_errors=True)

        _write_manifest(root, _find_oda_binary(bdir) or oda_bin)
        exe, _ = _read_bundle(root)
        if exe:
            logger.info("ODA bundle ready at %s", exe)
            return True
        raise RuntimeError("ODA bundle install finished but manifest is invalid")

    except Exception as e:
        logger.error("Failed to ensure ODA bundle: %s", e, exc_info=True)
        return bool(_read_bundle(root)[0])
    finally:
        deb_local.unlink(missing_ok=True)


def resolve_bundled_oda() -> Tuple[Optional[str], Optional[str]]:
    """Return (converter_path, ld_library_path_prefix) from .oda_bundle if present."""
    ensure_oda_bundle()
    return _read_bundle(backend_root())
