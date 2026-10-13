import base64
import logging
import os
import subprocess
import uuid
from io import BytesIO

import httpx
from PIL import Image, ImageOps, ImageStat

logger = logging.getLogger(__name__)

# Raster tracing targets (Gemini floor plans are often ~1–2k px; thin strokes need more pixels for Potrace.)
_TRACE_LONG_SIDE_MIN_PX = 2560
_TRACE_LONG_SIDE_MAX_PX = 8192


def _otsu_threshold_u8(hist_256: list) -> int:
    """Classic Otsu threshold from a 256-bin grayscale histogram (PIL-compatible)."""
    total = sum(hist_256)
    if total <= 0:
        return 128
    sum_all = sum(i * hist_256[i] for i in range(256))
    sum_b = 0
    w_b = 0
    best_var = 0.0
    threshold = 128
    for t in range(256):
        w_b += hist_256[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist_256[t]
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        var_between = float(w_b) * float(w_f) * (m_b - m_f) ** 2
        if var_between > best_var:
            best_var = var_between
            threshold = t
    return threshold


class LocalDxfService:
    def __init__(self, output_dir: str = "temp"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    async def convert_to_dxf(self, image_url: str) -> str:
        """
        Converts an image (URL or Data URI) to DXF using local Potrace.
        Returns the local file path of the generated DXF.
        """
        # 1. Get Image Data
        try:
            image = await self._get_image_data(image_url)
        except Exception as e:
            logger.error(f"Failed to load image data: {e}")
            raise Exception(f"Failed to load image for local conversion: {e}")
        
        # 2. Convert to BMP (1-bit monochrome) for Potrace
        bmp_path = self._save_as_bmp(image)
        
        try:
            # 3. Run Potrace
            dxf_filename = f"local_plan_{uuid.uuid4().hex}.dxf"
            dxf_path = os.path.join(self.output_dir, dxf_filename)
            
            # 3. Prepare Environment
            env = os.environ.copy()
            # Look in project-local bin directory (where render_build_native.sh installs it)
            # We are in app/services/local_dxf_service.py -> ../../.. -> backend/
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            local_bin = os.path.join(base_dir, "bin", "bin") # Make usually adds another /bin/ subdirectory
            
            # Platform-specific executable name
            is_windows = os.name == 'nt'
            potrace_exe = 'potrace.exe' if is_windows else 'potrace'
            path_sep = os.pathsep  # ';' on Windows, ':' on Unix
            
            # Helper function to check if potrace exists at a path
            def check_potrace(path_dir):
                potrace_path = os.path.join(path_dir, potrace_exe)
                if os.path.exists(potrace_path):
                    return potrace_path
                # Also check without .exe extension (for Unix-style installs on Windows)
                if is_windows:
                    potrace_path_no_ext = os.path.join(path_dir, 'potrace')
                    if os.path.exists(potrace_path_no_ext):
                        return potrace_path_no_ext
                return None

            # Explicitly add to path
            if os.path.isdir(local_bin):
                env["PATH"] = f"{local_bin}{path_sep}{env.get('PATH', '')}"

            # DEBUG LOGGING 2.0
            logger.info(f"Base Dir: {base_dir}")
            logger.info(f"Platform: {'Windows' if is_windows else 'Unix-like'}")
            logger.info(f"Checking for potrace at: {os.path.join(local_bin, potrace_exe)}")
            potrace_found = False
            potrace_path = check_potrace(local_bin)
            if potrace_path:
                 logger.info(f"✅ Potrace binary FOUND at expected location: {potrace_path}")
                 potrace_found = True
            else:
                 logger.warning("❌ Potrace binary NOT found at expected location.")
            
            # Fallback checks for standard install locations
            if not potrace_found:
                 # Check $HOME/.local/bin (Unix) or %LOCALAPPDATA% (Windows)
                 if is_windows:
                     home_bin = os.path.join(os.environ.get("LOCALAPPDATA", ""), "bin")
                 else:
                     home_bin = os.path.join(os.environ.get("HOME", ""), ".local", "bin")
                 
                 potrace_path = check_potrace(home_bin)
                 if potrace_path:
                      logger.info(f"✅ Potrace binary FOUND at HOME location (fallback): {potrace_path}")
                      env["PATH"] = f"{home_bin}{path_sep}{env.get('PATH', '')}"
                      potrace_found = True
                 
                 # Check platform-specific package manager locations
                 if not potrace_found:
                     if is_windows:
                         # Windows: Check common installation paths
                         windows_paths = [
                             os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "potrace", "bin"),
                             os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "potrace", "bin"),
                             os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "potrace", "bin"),
                             # Chocolatey
                             os.path.join(os.environ.get("ChocolateyInstall", "C:\\ProgramData\\chocolatey"), "bin"),
                             # Scoop
                             os.path.join(os.environ.get("USERPROFILE", ""), "scoop", "apps", "potrace", "current", "bin"),
                         ]
                         for win_path in windows_paths:
                             potrace_path = check_potrace(win_path)
                             if potrace_path:
                                 logger.info(f"✅ Potrace binary FOUND at Windows location: {potrace_path}")
                                 env["PATH"] = f"{win_path}{path_sep}{env.get('PATH', '')}"
                                 potrace_found = True
                                 break
                     else:
                         # macOS/Linux: Check Homebrew installation paths
                         # Apple Silicon Homebrew
                         homebrew_arm = "/opt/homebrew/bin"
                         potrace_path = check_potrace(homebrew_arm)
                         if potrace_path:
                             logger.info(f"✅ Potrace binary FOUND at Homebrew (Apple Silicon) location: {potrace_path}")
                             env["PATH"] = f"{homebrew_arm}{path_sep}{env.get('PATH', '')}"
                             potrace_found = True
                         else:
                             # Intel Homebrew
                             homebrew_intel = "/usr/local/bin"
                             potrace_path = check_potrace(homebrew_intel)
                             if potrace_path:
                                 logger.info(f"✅ Potrace binary FOUND at Homebrew (Intel) location: {potrace_path}")
                                 env["PATH"] = f"{homebrew_intel}{path_sep}{env.get('PATH', '')}"
                                 potrace_found = True
                             # Linux: Check /usr/bin and /usr/local/bin
                             linux_paths = ["/usr/bin", "/usr/local/bin"]
                             for linux_path in linux_paths:
                                 potrace_path = check_potrace(linux_path)
                                 if potrace_path:
                                     logger.info(f"✅ Potrace binary FOUND at Linux location: {potrace_path}")
                                     env["PATH"] = f"{linux_path}{path_sep}{env.get('PATH', '')}"
                                     potrace_found = True
                                     break
                 
                 # If still not found, log that we'll rely on system PATH
                 if not potrace_found:
                     logger.info("ℹ️  Potrace not found in common locations, relying on system PATH")
            
            # Potrace: finer coordinate quantization (-u) and tighter optimization (-O) track thin CAD strokes better.
            cmd = [
                "potrace",
                bmp_path,
                "-b",
                "dxf",
                "-o",
                dxf_path,
                "-u",
                "25",
                "-t",
                "2",
                "-O",
                "0.12",
            ]
            
            logger.info(f"Executing potrace: {' '.join(cmd)}")
            
            try:
                # Pass the updated env with local bin path
                result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
            except FileNotFoundError:
                install_instructions = (
                    "Windows: Download from http://potrace.sourceforge.net/ or use Chocolatey: choco install potrace"
                    if is_windows
                    else "macOS: brew install potrace | Linux: apt-get install potrace or yum install potrace"
                )
                logger.error(f"Potrace executable not found. Please install potrace. {install_instructions}")
                raise Exception(f"Potrace executable not found on the system. Local DXF generation requires 'potrace' to be installed. {install_instructions}")

            if result.returncode != 0:
                logger.error(f"Potrace execution failed: {result.stderr}")
                raise Exception(f"Potrace failed with exit code {result.returncode}: {result.stderr}")
                
            if not os.path.exists(dxf_path):
                 raise Exception("Potrace finished successfully but no DXF output file was created.")
            
            file_size = os.path.getsize(dxf_path)
            logger.info(f"Potrace conversion successful. Created {dxf_path} ({file_size} bytes).")
            
            return dxf_path
            
        finally:
            # Cleanup BMP
            if os.path.exists(bmp_path):
                try:
                    os.unlink(bmp_path)
                except:
                    pass

    async def _get_image_data(self, image_url: str) -> Image.Image:
        if image_url.startswith("data:"):
            # Format: "data:image/png;base64,..."
            try:
                header, encoded = image_url.split(",", 1)
                file_bytes = base64.b64decode(encoded)
                return Image.open(BytesIO(file_bytes))
            except Exception as e:
                raise Exception(f"Invalid Base64 image data: {e}")
        else:
            # Download from converted URL
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))

    def _save_as_bmp(self, image: Image.Image) -> str:
        # Potrace needs a BMP bitmap (black linework on white). PNG previews often look sharper than DXF
        # because Potrace vectorizes a thresholded raster — preprocessing reduces broken strokes / missing text.

        filename = f"temp_{uuid.uuid4().hex}.bmp"
        path = os.path.join(self.output_dir, filename)

        try:
            # If image has alpha channel, paste it on white background
            if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                alpha = image.convert('RGBA').split()[-1]
                bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
                bg.paste(image, mask=alpha)
                image = bg.convert('RGB')

            # Convert to grayscale
            gray = image.convert("L")

            # Gemini sometimes returns white-on-black "CAD viewport" style; Potrace expects black strokes on white.
            mean_lum = ImageStat.Stat(gray).mean[0]
            if mean_lum < 105:
                logger.info(
                    "Raster looks dark-first (mean luminance %.1f); inverting before Potrace trace",
                    mean_lum,
                )
                gray = ImageOps.invert(gray)

            # Upscale small rasters so thin dimensions / door swings survive threshold + tracing.
            w, h = gray.size
            long_side = max(w, h)
            if long_side > 0 and long_side < _TRACE_LONG_SIDE_MIN_PX:
                scale = _TRACE_LONG_SIDE_MIN_PX / float(long_side)
                nw = min(_TRACE_LONG_SIDE_MAX_PX, max(1, int(round(w * scale))))
                nh = min(_TRACE_LONG_SIDE_MAX_PX, max(1, int(round(h * scale))))
                if nw != w or nh != h:
                    logger.info(
                        "Scaling raster for Potrace: %sx%s → %sx%s",
                        w,
                        h,
                        nw,
                        nh,
                    )
                    gray = gray.resize((nw, nh), Image.Resampling.LANCZOS)

            hist = gray.histogram()
            th = _otsu_threshold_u8(hist)
            # Avoid pathological thresholds on flat noise (fallback toward mid-gray).
            if th < 60 or th > 200:
                th = max(70, min(180, int(mean_lum)))

            bw = gray.point(lambda x: 0 if x < th else 255, mode="1")

            bw.save(path, format="BMP")
            return path
        except Exception as e:
            logger.error(f"Failed to convert image to BMP: {e}")
            # Try saving raw if conversion fails, though likely to fail in potrace if not BMP
            try: 
                image.save(path, format="BMP")
                return path
            except:
                raise Exception(f"Could not save intermediate BMP file: {e}")

# Global instance
local_dxf_service = LocalDxfService()
