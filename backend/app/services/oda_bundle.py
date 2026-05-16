"""
Bundle ODA File Converter from a .deb URL into backend/.oda_bundle/ for Render/native deploys.

Build-time extraction (render_build_native.sh) may not survive the deploy artifact; this module
can download and extract at runtime when DWG_ODA_DEB_URL is set.
"""
from __future__ import annotations

import io
import logging
import os
import re
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
_QT_PLUGIN_PATH_FILE = "qt_plugin_path.txt"
# Cloudflare R2 presigned URLs: max expiry is 7 days (604800 seconds), not 30 days.
_R2_PRESIGN_MAX_SECONDS = 604_800
_last_oda_error: Optional[str] = None


def get_last_oda_error() -> Optional[str]:
    """Human-readable reason the last bundle download/install failed (for API errors)."""
    return _last_oda_error


def _sanitize_deb_url(url: str) -> str:
    u = url.strip().strip('"').strip("'")
    return u.replace("\r", "").replace("\n", "").replace(" ", "")


def backend_root() -> Path:
    """Resolve backend/ whether cwd is repo root or backend/."""
    here = Path(__file__).resolve().parent.parent.parent
    for candidate in (here, Path.cwd(), Path.cwd() / "backend"):
        if (candidate / "app" / "services").is_dir():
            return candidate
    return here


def bundle_dir(root: Optional[Path] = None) -> Path:
    return (root or backend_root()) / _BUNDLE_DIR_NAME


def _find_qt_platforms_dir(bdir: Path) -> Optional[str]:
    """Directory containing libq*.so platform plugins (e.g. .../plugins/platforms)."""
    saved = bdir / _QT_PLUGIN_PATH_FILE
    if saved.is_file():
        p = saved.read_text(encoding="utf-8").strip()
        if p and Path(p).is_dir():
            return p
    candidates: list[Path] = []
    for platforms in bdir.rglob("platforms"):
        if platforms.is_dir() and any(platforms.glob("libq*.so")):
            candidates.append(platforms)
    if not candidates:
        return None
    for d in candidates:
        if (d / "libqoffscreen.so").exists():
            return str(d.resolve())
    return str(candidates[0].resolve())


def _read_bundle(root: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    rel_file = bundle_dir(root) / _MANIFEST
    ld_file = bundle_dir(root) / _LD_PATH_FILE
    if not rel_file.is_file():
        return None, None, None
    rel = rel_file.read_text(encoding="utf-8").strip()
    if not rel:
        return None, None, None
    exe = (root / rel).resolve()
    if not exe.is_file():
        logger.warning("ODA manifest points to missing file: %s", exe)
        return None, None, None
    ld_extra = ld_file.read_text(encoding="utf-8").strip() if ld_file.is_file() else ""
    qt_plugins = _find_qt_platforms_dir(bundle_dir(root))
    return str(exe), ld_extra or None, qt_plugins


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
    qt_dir = _find_qt_platforms_dir(bdir)
    if qt_dir:
        (bdir / _QT_PLUGIN_PATH_FILE).write_text(qt_dir + "\n", encoding="utf-8")
        off = Path(qt_dir) / "libqoffscreen.so"
        logger.info(
            "ODA bundle manifest written: exe=%s lib_dirs=%s qt_plugins=%s offscreen=%s",
            rel,
            len(lib_dirs),
            qt_dir,
            off.is_file(),
        )
    else:
        logger.warning("ODA bundle: no Qt platforms/ directory found under %s", bdir)


def _is_elf_executable(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(4) == b"\x7fELF"
    except OSError:
        return False


def _find_oda_binary(extract_root: Path) -> Optional[Path]:
    """
    Return the real ODA ELF binary, not usr/bin/ODAFileConverter (a shell wrapper
  that execs hardcoded /usr/bin/ODAFileConverter_* paths).
    """
    # Prefer versioned directory from .deb: usr/bin/ODAFileConverter_27.1.0.0/ODAFileConverter
    bin_dir = extract_root / "usr" / "bin"
    if bin_dir.is_dir():
        for sub in sorted(bin_dir.glob("ODAFileConverter_*")):
            if sub.is_dir():
                inner = sub / "ODAFileConverter"
                if inner.is_file() and _is_elf_executable(inner):
                    return inner

    elf_candidates: list[Path] = []
    for path in extract_root.rglob("ODAFileConverter"):
        if not path.is_file():
            continue
        if _is_elf_executable(path):
            elf_candidates.append(path)

    if elf_candidates:
        # Prefer nested versioned binary over any stray matches
        return sorted(elf_candidates, key=lambda p: len(p.parts), reverse=True)[0]
    return None


def _repair_bundle_manifest(root: Path) -> None:
    """Fix manifest if it points at the wrapper script instead of the ELF binary."""
    bdir = bundle_dir(root)
    if not bdir.is_dir():
        return
    rel_file = bdir / _MANIFEST
    if rel_file.is_file():
        rel = rel_file.read_text(encoding="utf-8").strip()
        if rel:
            current = (root / rel).resolve()
            if current.is_file() and _is_elf_executable(current):
                return
    real = _find_oda_binary(bdir)
    if real:
        logger.info("Repairing ODA bundle manifest -> %s", real.relative_to(root))
        _write_manifest(root, real)


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


def _hint_for_download_failure(status_code: int, body: str, url: str) -> str:
    if "X-Amz-Expires=2592000" in url or "expires=2592000" in url.lower():
        return (
            "R2/S3 presigned URL uses 30-day expiry (2592000s); Cloudflare R2 allows at most 7 days. "
            f"Regenerate with: aws s3 presign ... --expires-in {_R2_PRESIGN_MAX_SECONDS}"
        )
    if status_code == 400:
        return (
            "Storage returned HTTP 400 (invalid presigned URL). Regenerate DWG_ODA_DEB_URL: "
            f"use --expires-in {_R2_PRESIGN_MAX_SECONDS} or less, paste the full URL with no quotes/newlines."
        )
    if status_code in (403, 404):
        return "Presigned URL expired or object missing — generate a new R2 presigned URL and update Render."
    snippet = (body or "").strip()[:200]
    if snippet:
        return f"HTTP {status_code}: {snippet}"
    return f"HTTP {status_code} downloading .deb"


def _r2_download_config() -> Optional[dict[str, str]]:
    """R2 S3 API settings (preferred over presigned URL on Render)."""
    access = (
        (getattr(settings, "R2_ACCESS_KEY_ID", None) or "")
        or os.environ.get("R2_ACCESS_KEY_ID", "")
        or os.environ.get("AWS_ACCESS_KEY_ID", "")
    ).strip()
    secret = (
        (getattr(settings, "R2_SECRET_ACCESS_KEY", None) or "")
        or os.environ.get("R2_SECRET_ACCESS_KEY", "")
        or os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    ).strip()
    endpoint = (
        (getattr(settings, "R2_ENDPOINT_URL", None) or "") or os.environ.get("R2_ENDPOINT_URL", "")
    ).strip().rstrip("/")
    bucket = (
        (getattr(settings, "R2_ODA_BUCKET", None) or "")
        or os.environ.get("R2_ODA_BUCKET", "")
        or "krafzen-build-private"
    ).strip()
    key = (
        (getattr(settings, "R2_ODA_OBJECT_KEY", None) or "")
        or os.environ.get("R2_ODA_OBJECT_KEY", "")
        or "ODAFileConverter_QT6_lnxX64_8.3dll_27.1.deb"
    ).strip()
    if access and secret and endpoint and bucket and key:
        return {
            "access": access,
            "secret": secret,
            "endpoint": endpoint,
            "bucket": bucket,
            "key": key,
        }
    return None


def _download_deb_from_r2(dest: Path, r2: dict[str, str]) -> None:
    import boto3
    from botocore.config import Config

    client = boto3.client(
        "s3",
        endpoint_url=r2["endpoint"],
        aws_access_key_id=r2["access"],
        aws_secret_access_key=r2["secret"],
        region_name="auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    client.download_file(r2["bucket"], r2["key"], str(dest))


def _download_oda_deb(dest: Path, url: str) -> None:
    """Download ODA .deb via R2 API (preferred) or presigned HTTPS URL."""
    r2 = _r2_download_config()
    if r2:
        try:
            logger.info(
                "Downloading ODA .deb from R2 API s3://%s/%s",
                r2["bucket"],
                r2["key"],
            )
            _download_deb_from_r2(dest, r2)
            return
        except Exception as exc:
            logger.warning("R2 API download failed, trying presigned URL if set: %s", exc)

    if not url:
        raise RuntimeError(
            "Cannot download ODA .deb: set R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT_URL "
            "(and optionally R2_ODA_BUCKET / R2_ODA_OBJECT_KEY) on Render, or set DWG_ODA_DEB_URL."
        )

    expires = "?"
    m = re.search(r"X-Amz-Expires=(\d+)", url)
    if m:
        expires = m.group(1)
    logger.info("Downloading ODA .deb via presigned URL (X-Amz-Expires=%s)", expires)
    _download_deb(url, dest)


def _download_deb(url: str, dest: Path) -> None:
    """Download .deb with minimal headers (compatible with S3/R2 presigned GET)."""
    headers = {"Accept": "*/*"}
    timeout = httpx.Timeout(600.0, connect=60.0)
    with httpx.Client(timeout=timeout, follow_redirects=True, http2=False) as client:
        with client.stream("GET", url, headers=headers) as resp:
            if resp.status_code >= 400:
                body = resp.read().decode("utf-8", errors="replace")
                raise httpx.HTTPStatusError(
                    _hint_for_download_failure(resp.status_code, body, url),
                    request=resp.request,
                    response=resp,
                )
            with dest.open("wb") as out:
                for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                    out.write(chunk)


def _ensure_oda_bundle_locked(force: bool = False) -> bool:
    global _last_oda_error
    root = backend_root()
    raw = getattr(settings, "DWG_ODA_DEB_URL", None) or os.environ.get("DWG_ODA_DEB_URL") or ""
    url = _sanitize_deb_url(raw)

    if not force:
        exe, _, _ = _read_bundle(root)
        if exe:
            return True

    r2 = _r2_download_config()
    if not url and not r2:
        _last_oda_error = (
            "Neither R2 API credentials nor DWG_ODA_DEB_URL is configured. "
            "Set R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT_URL on Render (recommended), "
            "or a valid presigned DWG_ODA_DEB_URL."
        )
        logger.warning(_last_oda_error)
        return bool(_read_bundle(root)[0])

    if url and url != raw.strip():
        logger.warning("DWG_ODA_DEB_URL had extra whitespace or quotes; sanitized before download.")

    bdir = bundle_dir(root)
    deb_local = root / ".oda_download.deb"

    try:
        _last_oda_error = None
        bdir.mkdir(parents=True, exist_ok=True)
        # Another worker may have finished while we waited
        if not force:
            exe, _, _ = _read_bundle(root)
            if exe:
                return True

        logger.info("Fetching ODA .deb into %s ...", bdir)
        _download_oda_deb(deb_local, url)

        if deb_local.stat().st_size < 1_000_000:
            raise RuntimeError(
                f"Downloaded .deb is too small ({deb_local.stat().st_size} bytes); "
                "check DWG_ODA_DEB_URL (presigned URL may be invalid or expired)."
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
        exe, _, _ = _read_bundle(root)
        if exe:
            logger.info("ODA bundle ready at %s", exe)
            return True
        raise RuntimeError("ODA bundle install finished but manifest is invalid")

    except httpx.HTTPStatusError as e:
        _last_oda_error = str(e) or _hint_for_download_failure(
            e.response.status_code if e.response else 0,
            e.response.text if e.response else "",
            url,
        )
        logger.error("Failed to ensure ODA bundle: %s", _last_oda_error, exc_info=True)
        return bool(_read_bundle(root)[0])
    except Exception as e:
        _last_oda_error = str(e)
        logger.error("Failed to ensure ODA bundle: %s", e, exc_info=True)
        return bool(_read_bundle(root)[0])
    finally:
        deb_local.unlink(missing_ok=True)


def apply_oda_runtime_env(run_env: dict[str, str], root: Optional[Path] = None) -> None:
    """Set LD_LIBRARY_PATH and Qt platform env for headless ODA on Linux."""
    import sys

    root = root or backend_root()
    _, ld_extra, qt_plugins = _read_bundle(root)
    if ld_extra:
        sep = os.pathsep
        prev = run_env.get("LD_LIBRARY_PATH", "")
        run_env["LD_LIBRARY_PATH"] = f"{ld_extra}{sep}{prev}" if prev else ld_extra
    if qt_plugins:
        run_env["QT_PLUGIN_PATH"] = qt_plugins
        run_env["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_plugins
        p = Path(qt_plugins)
        if (p / "libqoffscreen.so").exists():
            run_env["QT_QPA_PLATFORM"] = "offscreen"
        elif (p / "libqminimal.so").exists():
            run_env["QT_QPA_PLATFORM"] = "minimal"
        elif (p / "libqxcb.so").exists():
            # xcb needs a display; use xvfb-run if bundled or on PATH
            run_env["QT_QPA_PLATFORM"] = "xcb"
    elif sys.platform.startswith("linux"):
        run_env.setdefault("QT_QPA_PLATFORM", "offscreen")
    run_env.setdefault("QT_LOGGING_RULES", "qt.qpa.plugin=false")


def wrap_oda_command(cmd: list[str], root: Optional[Path] = None) -> list[str]:
    """Prefix with bundled/system xvfb-run when only the xcb Qt plugin is available."""
    root = root or backend_root()
    _, _, qt_plugins = _read_bundle(root)
    if not qt_plugins:
        return cmd
    p = Path(qt_plugins)
    if (p / "libqoffscreen.so").exists() or (p / "libqminimal.so").exists():
        return cmd
    if not (p / "libqxcb.so").exists():
        return cmd
    bdir = bundle_dir(root)
    for candidate in (
        bdir / "xvfb" / "usr" / "bin" / "xvfb-run",
        bdir / "usr" / "bin" / "xvfb-run",
    ):
        if candidate.is_file():
            return [str(candidate), "-a", "-s", "-screen 0 1280x1024x24", *cmd]
    xvfb = shutil.which("xvfb-run")
    if xvfb:
        return [xvfb, "-a", "-s", "-screen 0 1280x1024x24", *cmd]
    return cmd


def resolve_bundled_oda() -> Tuple[Optional[str], Optional[str]]:
    """Return (converter_path, ld_library_path_prefix) from .oda_bundle if present."""
    root = backend_root()
    ensure_oda_bundle()
    _repair_bundle_manifest(root)
    exe, ld, _qt = _read_bundle(root)
    return exe, ld
