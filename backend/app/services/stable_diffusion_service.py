
from gradio_client import Client
from app.core.config import settings
import logging
import base64
import os

logger = logging.getLogger(__name__)

class StableDiffusionService:
    def __init__(self):
        self.hf_token = settings.HF_TOKEN
        self.client = None
        if self.hf_token:
            try:
                self.client = Client("stabilityai/stable-diffusion-3.5-large", hf_token=self.hf_token)
            except Exception as e:
                logger.error(f"Failed to initialize Stable Diffusion Client: {e}")
        else:
             logger.warning("HF_TOKEN not set. Stable Diffusion service may default to public/anonymous quotas or fail.")
             # Attempt init without token, might fail for this specific space if private, but it's public.
             try:
                self.client = Client("stabilityai/stable-diffusion-3.5-large")
             except Exception as e:
                logger.error(f"Failed to initialize Stable Diffusion Client (no token): {e}")

    async def generate_image(self, prompt: str) -> str:
        """
        Generates an image using Stable Diffusion 3.5 Large via HF Spaces.
        Returns a base64 encoded data URL string.
        """
        if not self.client:
             raise Exception("Stable Diffusion Client not initialized - check HF_TOKEN or connection.")

        logger.info(f"Generating image with Stable Diffusion (HF Space)... Prompt: {prompt[:50]}...")
        
        try:
            # The stable-diffusion-3.5-large space API typically takes:
            # param_0: prompt (str)
            # param_1: negative_prompt (str)
            # param_2: seed (float)
            # param_3: randomized_seed (bool)
            # param_4: width (float)
            # param_5: height (float)
            # param_6: guidance_scale (float)
            # param_7: num_inference_steps (float)
            # etc... 
            # We need to be careful with the API signature.
            # Best way used to be .predict().
            
            # Enhanced Prompt Construction for CAD Style (Matching Gemini's logic)
            # Enhanced Prompt Construction for CAD Style (Matching Gemini's logic)
            enhanced_prompt = f"""
            (masterpiece), (best quality), professional 2D CAD technical drawing, floor plan, top-down view, orthographic projection.
            Blueprint style, dark blue background, white lines, engineering grid.
            Architectural schematic, precise geometry, high contrast.
            
            SPECIFICATIONS:
            {prompt}
            """
            
            # Strict Negative Prompts to prevent 3D/Photorealism
            negative_prompt = "3d, perspective, isometric, photorealistic, render, photography, shadow, depth, room interior view, ceiling, windows view, realistic furniture, gradient, blur, noisy, distorted, messy, sloppy, sketch, hand-drawn"

            # API inspection shows "infer" function:
            # infer(prompt, negative_prompt, seed, randomize_seed, width, height, guidance_scale, num_inference_steps)
            result_path = self.client.predict(
				prompt=enhanced_prompt,
				negative_prompt=negative_prompt,
				seed=0,
				randomize_seed=True,
				width=1024,
				height=1024,
				guidance_scale=7.5, # Increased consistency
				num_inference_steps=40, # Higher steps for detail
				api_name="/infer"
            )
            
            # Result is a tuple or path. Usually for images it returns a temporary file path string 
            # or a tuple with filepath as first element.
            
            # Check result type
            image_path = result_path
            if isinstance(result_path, (list, tuple)):
                image_path = result_path[0]
            
            if not image_path or not os.path.exists(image_path):
                 raise Exception(f"Invalid result path from Gradio: {result_path}")
            
            # Read and convert to base64
            with open(image_path, "rb") as img_file:
                b64_data = base64.b64encode(img_file.read()).decode('utf-8')
                
            # Guess mime type (usually webp or png from this space)
            mime_type = "image/png" 
            if image_path.endswith(".webp"):
                mime_type = "image/webp"
            elif image_path.endswith(".jpg") or image_path.endswith(".jpeg"):
                mime_type = "image/jpeg"
                
            return f"data:{mime_type};base64,{b64_data}"

        except Exception as e:
            logger.error(f"Stable Diffusion generation error: {e}")
            raise e
