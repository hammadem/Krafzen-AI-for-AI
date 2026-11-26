import logging
import re
import subprocess
from pathlib import Path
from threading import Lock
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass

import ezdxf

from app.core.config import settings
from app.services.oda_bundle import (
    backend_root,
    get_last_oda_error,
    resolve_bundled_oda,
    run_oda_subprocess,
)

logger = logging.getLogger(__name__)
_conversion_slot = Lock()

def validate_dwg_header(raw: bytes) -> None:
    if len(raw) < 64 or not re.fullmatch(rb'AC10[0-9]{2}', raw[:6]):
        raise ValueError('Not a supported DWG binary header')



@dataclass(frozen=True)
class DwgConvertResult:
    dwg_path: str
    input_dxf_path: str
    work_dir: str


class DwgConverterService:
    """
    Convert DXF → DWG using an external converter.

    Notes:
    - Native DWG writing is not supported by common Python DXF libs.
    - This service shells out to a locally installed converter (recommended: ODA File Converter).
    """

    def __init__(self) -> None:
        self._converter_cmd = (getattr(settings, "DWG_CONVERTER_CMD", None) or "").strip()
        self._converter_type = (getattr(settings, "DWG_CONVERTER_TYPE", None) or "LIBREDWG").strip().upper()

    @property
    def converter_type(self) -> str:
        return self._converter_type

    def _libredwg_tools(self) -> tuple[str | None, str | None]:
        def resolve(command: str, name: str) -> str | None:
            found = shutil.which(command)
            if found:
                return found
            bundled = backend_root() / "bin" / "libredwg" / "bin" / name
            return str(bundled) if command == name and os.access(bundled, os.X_OK) else None
        return (resolve(settings.DWG_LIBREDWG_DWG2DXF, "dwg2dxf"), resolve(settings.DWG_LIBREDWG_DXF2DWG, "dxf2dwg"))

    def _resolve_converter_cmd_and_ld(self) -> tuple[str | None, str | None]:
        """
        Resolve ODA executable and optional LD_LIBRARY_PATH prefix (bundled .deb on Render).
        """
        if self._converter_type != "ODA" or not settings.DWG_ODA_USE_AUTHORIZED:
            return None, None
        if self._converter_cmd:
            raw = self._converter_cmd
            if os.path.basename(raw) != raw:
                if os.path.isfile(raw) and os.access(raw, os.X_OK):
                    return raw, None
            else:
                resolved = shutil.which(raw)
                if resolved:
                    return resolved, None

        bundle_bin, bundle_ld = resolve_bundled_oda()
        if bundle_bin:
            return bundle_bin, bundle_ld

        for p in ("/usr/bin/ODAFileConverter", "/usr/local/bin/ODAFileConverter"):
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p, None

        mac_app_bin = "/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter"
        if os.path.exists(mac_app_bin):
            return mac_app_bin, None
        return None, None

    def is_configured(self) -> bool:
        if self._converter_type == "LIBREDWG":
            return all(self._libredwg_tools())
        return bool(self._resolve_converter_cmd_and_ld()[0])

    def convert_dxf_path_to_dwg(self, dxf_path: str, *, output_filename: str | None = None) -> DwgConvertResult:
        if self._converter_type == "LIBREDWG":
            return self._libredwg_export(dxf_path, output_filename=output_filename)
        if not self.is_configured():
            detail = get_last_oda_error()
            msg = (
                "DWG converter is not configured. On Render, set DWG_ODA_DEB_URL to a valid HTTPS URL "
                "for the Linux x64 ODA .deb (R2 presign: use --expires-in 604800 max, not 30 days)."
            )
            if detail:
                msg = f"{msg} Details: {detail}"
            raise RuntimeError(msg)
        if not os.path.exists(dxf_path):
            raise RuntimeError("DXF input file does not exist")

        if self._converter_type != "ODA":
            raise RuntimeError(f"Unsupported DWG converter type: {self._converter_type}")

        # ODA File Converter works on directories (input_dir -> output_dir).
        work_dir = tempfile.mkdtemp(prefix="krafzen_dwg_")
        in_dir = os.path.join(work_dir, "in")
        out_dir = os.path.join(work_dir, "out")
        os.makedirs(in_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)

        input_name = f"input_{uuid.uuid4().hex}.dxf"
        input_dxf_path = os.path.join(in_dir, input_name)
        shutil.copyfile(dxf_path, input_dxf_path)
        self._normalize_dxf_visibility(input_dxf_path)

        dwg_name = os.path.basename(output_filename) if output_filename else os.path.splitext(os.path.basename(dxf_path))[0] + ".dwg"
        if not dwg_name.lower().endswith(".dwg"):
            dwg_name += ".dwg"

        # ODA args (typical):
        # ODAFileConverter <inputFolder> <outputFolder> <outputVersion> <outputType> <recurse> <audit> [<inputFilter>]
        # We keep it conservative: 2018 DWG, DWG output, no recursion, no audit.
        converter_cmd, _ld_extra = self._resolve_converter_cmd_and_ld()
        if not converter_cmd:
            raise RuntimeError(
                "DWG converter executable not found. Install ODA File Converter and set DWG_CONVERTER_CMD "
                "or install to /Applications/ODAFileConverter.app."
            )

        cmd = [
            converter_cmd,
            in_dir,
            out_dir,
            "ACAD2018",
            "DWG",
            "0",
            "0",
        ]

        run_env = os.environ.copy()

        logger.info("Converting DXF → DWG via ODA", extra={"cmd": " ".join(cmd)})
        result = run_oda_subprocess(cmd, run_env, backend_root())
        if result.returncode != 0:
            raise RuntimeError(
                "DWG conversion failed. "
                f"exit_code={result.returncode} stderr={result.stderr.strip() or '(empty)'}"
            )

        # ODA typically preserves basename but may also output nested dirs; we only wrote one file.
        candidates: list[str] = []
        for root, _, files in os.walk(out_dir):
            for f in files:
                if f.lower().endswith(".dwg"):
                    candidates.append(os.path.join(root, f))
        if not candidates:
            raise RuntimeError("DWG conversion finished but no .dwg output was produced.")

        # Pick largest DWG (safest when multiple candidates appear).
        dwg_path = max(candidates, key=lambda p: os.path.getsize(p))
        with open(dwg_path, "rb") as converted:
            validate_dwg_header(converted.read(64))

        # Normalize output name if desired.
        final_dwg_path = os.path.join(work_dir, dwg_name)
        try:
            shutil.copyfile(dwg_path, final_dwg_path)
            dwg_path = final_dwg_path
        except OSError as exc:
            # Keep original path if copy fails.
            logger.warning("Unable to normalize DWG output filename: %s", exc)

        return DwgConvertResult(dwg_path=dwg_path, input_dxf_path=input_dxf_path, work_dir=work_dir)

    def _libredwg_export(self, dxf_path: str, *, output_filename: str | None = None) -> DwgConvertResult:
        reader, writer = self._libredwg_tools()
        if not reader or not writer:
            raise RuntimeError("LibreDWG CLI tools are not installed")
        if not os.path.isfile(dxf_path) or not 0 < os.path.getsize(dxf_path) <= 25*1024*1024:
            raise ValueError("DXF input missing or oversized")
        if not _conversion_slot.acquire(blocking=False):
            raise RuntimeError("DWG converter busy")
        work_dir = tempfile.mkdtemp(prefix="krafzen-libredwg-")
        try:
            original = Path(work_dir)/"source.dxf"
            shutil.copyfile(dxf_path, original)
            name = os.path.basename(output_filename or "drawing.dwg")
            if not name.lower().endswith(".dwg"):
                name += ".dwg"
            output = Path(work_dir)/name
            # Stable documented write target; do not promise DWG 2018 output.
            result = subprocess.run([writer, "--as=r2000", "-o", str(output), str(original)],
                                    capture_output=True, check=False, timeout=180)
            if result.returncode or not output.is_file() or output.is_symlink() or not 64<=output.stat().st_size<=25*1024*1024:
                raise RuntimeError("LibreDWG did not produce a bounded DWG")
            with output.open("rb") as f:
                header=f.read(64)
                validate_dwg_header(header)
                if header[:6]!=b"AC1015":
                    raise RuntimeError("LibreDWG output is not the requested R2000 format")
            return DwgConvertResult(str(output), str(original), work_dir)
        except Exception:
            shutil.rmtree(work_dir, ignore_errors=True)
            raise
        finally:
            _conversion_slot.release()

    def convert_dwg_bytes_to_dxf(self, raw: bytes) -> bytes:
        """Convert a scanned DWG using the existing ODA runtime, never rename."""
        validate_dwg_header(raw)
        if len(raw) > 25 * 1024 * 1024:
            raise ValueError("DWG exceeds 25 MB")
        if self._converter_type == "LIBREDWG":
            executable, _ = self._libredwg_tools()
        else:
            executable, _ = self._resolve_converter_cmd_and_ld()
        if not executable:
            raise RuntimeError("Selected DWG converter runtime unavailable")
        if not _conversion_slot.acquire(blocking=False):
            raise RuntimeError("DWG converter busy")
        try:
            with tempfile.TemporaryDirectory(prefix="krafzen-dwg-import-") as folder:
                input_dir, output_dir = Path(folder)/"in", Path(folder)/"out"
                input_dir.mkdir(); output_dir.mkdir()
                (input_dir/"source.dwg").write_bytes(raw)
                output = output_dir/"source.dxf"
                if self._converter_type == "LIBREDWG":
                    result = subprocess.run([executable,"-o",str(output),str(input_dir/"source.dwg")],
                                            capture_output=True,check=False,timeout=180)
                else:
                    result = run_oda_subprocess([executable,str(input_dir),str(output_dir),
                        "ACAD2018","DXF","0","0"],os.environ.copy(),backend_root())
                if result.returncode or not output.is_file() or output.is_symlink():
                    raise RuntimeError("Converter did not produce the expected DXF")
                if not 0 < output.stat().st_size <= 25*1024*1024:
                    raise RuntimeError("Converted DXF exceeds supported size")
                return output.read_bytes()
        finally:
            _conversion_slot.release()

    def _normalize_dxf_visibility(self, dxf_path: str) -> None:
        """
        Normalize entity visibility before DWG conversion.

        Some viewers can hide/faint entities after conversion when entities have
        odd inherited attributes (true_color/transparency/byblock combinations).
        This pass keeps entities explicit and visible.
        """
        try:
            doc = ezdxf.readfile(dxf_path)

            # Ensure default layer color uses AutoCAD index 7 (adaptive black/white).
            try:
                if "0" in doc.layers:
                    doc.layers.get("0").dxf.color = 7
            except ezdxf.DXFError as exc:
                logger.debug("Unable to normalize the default DXF layer: %s", exc)

            def _normalize_layout(layout) -> None:
                for entity in layout:
                    try:
                        # Force clear explicit true color/transparency so viewers
                        # use ACI color resolution more predictably.
                        if entity.dxf.hasattr("true_color"):
                            entity.dxf.discard("true_color")
                        if entity.dxf.hasattr("transparency"):
                            entity.dxf.discard("transparency")

                        # Prefer ByLayer for portability.
                        if entity.dxf.hasattr("color"):
                            entity.dxf.color = 256  # BYLAYER
                    except ezdxf.DXFError as exc:
                        logger.debug("Skipping unsupported DXF entity during normalization: %s", exc)
                        continue

            _normalize_layout(doc.modelspace())
            for layout in doc.layouts:
                if layout.name.lower() != "model":
                    _normalize_layout(layout)

            doc.saveas(dxf_path)
        except (AttributeError, OSError, TypeError, ValueError, ezdxf.DXFError) as e:
            # Non-fatal: fall back to original DXF if normalization fails.
            logger.warning("DXF visibility normalization skipped: %s", e)


dwg_converter_service = DwgConverterService()
