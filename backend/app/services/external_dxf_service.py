import httpx
import logging
import asyncio
from app.core.config import settings
import os
import uuid

logger = logging.getLogger(__name__)

class ExternalDxfService:
    def __init__(self, output_dir: str = "temp"):
        self.api_key = settings.API_2_CONVERT_KEY
        self.base_url = "https://api.api2convert.com/v2"
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if not self.api_key:
            logger.warning("API_2_CONVERT_KEY is not set. External DXF conversion will fail.")

    async def convert_to_dxf(self, image_url: str) -> str:
        """
        Converts an image (URL or Data URI) to DXF using Api2Convert.
        Returns the local file path of the downloaded DXF.
        """
        if not self.api_key:
             raise Exception("External DXF Service Provider API Key is missing")

        # 1. Create Job
        job_id = await self._create_job(image_url)
        logger.info(f"Created Conversion Job: {job_id}")

        # 2. Poll for Completion
        result_url = await self._wait_for_job(job_id)
        logger.info(f"Conversion Complete. Result URL: {result_url}")

        # 3. Download File
        file_path = await self._download_file(result_url)
        return file_path

    async def _create_job(self, source_url: str) -> str:
        async with httpx.AsyncClient() as client:
            headers = {
                "X-Oc-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Determine logic based on input type
            is_base64 = source_url.startswith("data:")
            
            payload = {
                "input": [] if is_base64 else [{
                    "type": "remote",
                    "source": source_url
                }],
                "conversion": [{
                    "target": "dxf"
                }],
                "process": False if is_base64 else True 
            }
            
            # 1. Initiate Job
            response = await client.post(f"{self.base_url}/jobs", json=payload, headers=headers)
            
            if response.status_code != 201:
                logger.error(f"Api2Convert Job Creation Failed ({response.status_code}): {response.text}")
                try:
                    error_details = response.json()
                    raise Exception(f"Api2Convert Error: {error_details.get('message') or error_details}")
                except:
                    response.raise_for_status()
            
            data = response.json()
            logger.info(f"API JOB CREATION RESPONSE: {data}")
            job_id = data['id']
            
            # 2. Upload File if needed
            if is_base64:
                # Extract upload server
                server = data.get('server')
                if not server and data.get('input'):
                     # Fallback to input specific server
                     server = data['input'][0].get('server')
                
                if not server:
                     logger.error(f"No upload server found: {data}")
                     raise Exception("API did not provide upload server.")

                # Decode Base64
                import base64
                header, encoded = source_url.split(",", 1)
                file_bytes = base64.b64decode(encoded)
                logger.info(f"Decoded {len(file_bytes)} bytes from Data URI.")
                
                # Detect Extension/MIME
                # header e.g. "data:image/jpeg;base64"
                mime_type = "image/png"
                ext = "png"
                if "image/jpeg" in header:
                    mime_type = "image/jpeg"
                    ext = "jpg"
                elif "image/webp" in header:
                    mime_type = "image/webp"
                    ext = "webp"
                
                logger.info(f"Detected MIME: {mime_type}, Extension: {ext}")

                # Upload
                # Revert to standard URL: /upload-file/{job_id}
                upload_url = f"{server}/upload-file/{job_id}"
                
                # Use Token from response if available, else API Key
                job_token = data.get('token')
                
                files = {'file': (f'floorplan.{ext}', file_bytes, mime_type)}
                
                upload_headers = {}
                if job_token:
                    upload_headers["X-Oc-Token"] = job_token
                else:
                    upload_headers["X-Oc-Api-Key"] = self.api_key
                
                logger.info(f"Uploading file to {upload_url} with headers keys: {list(upload_headers.keys())}...")
                upload_resp = await client.post(upload_url, files=files, headers=upload_headers)
                
                logger.info(f"Upload Response: {upload_resp.status_code} - {upload_resp.text}")
                
                if upload_resp.status_code != 200 and upload_resp.status_code != 201:
                     logger.error(f"Upload Failed ({upload_resp.status_code}): {upload_resp.text}")
                     upload_resp.raise_for_status()
                     
                logger.info("Upload complete. Starting Job...")
                
                # 3. Start Job (Process: True)
                patch_payload = {"process": True}
                patch_resp = await client.patch(f"{self.base_url}/jobs/{job_id}", json=patch_payload, headers=headers)
                if patch_resp.status_code != 200:
                    logger.error(f"Failed to start job ({patch_resp.status_code}): {patch_resp.text}")
                    patch_resp.raise_for_status()
            
            return job_id
            
            return job_id

    async def _wait_for_job(self, job_id: str) -> str:
        async with httpx.AsyncClient() as client:
            headers = {"X-Oc-Api-Key": self.api_key}
            
            start_time = asyncio.get_event_loop().time()
            timeout = 120 # 2 minutes timeout
            
            while True:
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > timeout:
                     raise Exception("Conversion job timed out.")

                response = await client.get(f"{self.base_url}/jobs/{job_id}", headers=headers)
                data = response.json()
                status = data['status']['code']
                
                logger.info(f"Job Status: {status} (Info: {data['status'].get('info')})")
                
                if status == 'completed':
                    logger.info(f"JOB COMPLETED DATA: {data}")
                    # Find output
                    # Robust parsing: Look for any output with URI
                    if data.get('output'):
                        # Try to find specific DXF target if possible
                        for output in data['output']:
                            # Check if conversion target matches or just return first
                            # output['conversion'] might be an object or ID.
                            # Let's just return the first valid URI for now.
                            return output['uri']
                    
                    raise Exception("Job completed but no output URI found.")
                
                if status == 'failed':
                    raise Exception(f"Job failed: {data.get('status', {}).get('info')}")
                
                await asyncio.sleep(2)

    async def _download_file(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            
            filename = f"extern_plan_{uuid.uuid4().hex}.dxf"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(resp.content)
            
            return filepath
