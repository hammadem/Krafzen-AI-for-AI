import subprocess
import os
import uuid
import base64
import logging
import httpx
from PIL import Image
from io import BytesIO
from app.core.config import settings

logger = logging.getLogger(__name__)

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
            
            # Potrace command: potrace input.bmp -b dxf -o output.dxf
            # We can add parameters for optimization if needed (e.g., -u for unit 10)
            cmd = ["potrace", bmp_path, "-b", "dxf", "-o", dxf_path]
            
            logger.info(f"Executing potrace: {' '.join(cmd)}")
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            except FileNotFoundError:
                logger.error("Potrace executable not found. Please install potrace (e.g. 'brew install potrace').")
                raise Exception("Potrace executable not found on the system. Local DXF generation requires 'potrace' to be installed.")

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
        # Potrace needs a bitmap (BMP). 
        # Convert to 'L' (grayscale) then point operation or threshold to '1' if not already.
        
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
            
            # Threshold to black and white (1-bit)
            # Adjust threshold as needed, 128 is standard mid-point
            bw = gray.point(lambda x: 0 if x < 128 else 255, '1')
            
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
