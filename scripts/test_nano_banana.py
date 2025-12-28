import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio

load_dotenv("backend/.env")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No GEMINI_API_KEY found")
    exit(1)

genai.configure(api_key=api_key)

model_name = "models/nano-banana-pro-preview"

dsl_input = """UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=4150 h=3950 center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
WINDOW: rect w=786 h=132 center=(622,474) layer=OPENINGS closed=true anchor_wall=none
BED: rect w=1910 h=2157 center=(0,-846) layer=FURNITURE closed=true anchor_wall=south
DESK: rect w=1304 h=692 center=(0,1579) layer=FURNITURE closed=true anchor_wall=north
NIGHTSTAND: rect w=514 h=388 center=(-622,474) layer=FURNITURE closed=true anchor_wall=none
WARDROBE: rect w=1013 h=432 center=(1518,0) layer=FURNITURE closed=true anchor_wall=east"""

async def test_generation():
    print(f"Testing model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        # We want it to generate an image. 
        # Standard generic models don't just "generate image" from text in generate_content unless it's multimodal output.
        # Let's see what happens.
        prompt = f"Generate a CAD image (SVG or PNG) based on this specification:\n{dsl_input}"
        
        response = await model.generate_content_async(prompt)
        
        print("\nResponse Parts:")
        for part in response.parts:
            print(f"Part object: {part}")
            # Try to check if text is present
            try:
                if part.text:
                    print(f"  Text found: {part.text[:200]}...")
            except:
                pass
            
            # Check for inline_data
            if hasattr(part, 'inline_data'):
                print(f"  Inline Data found: {part.inline_data}")

        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_generation())
