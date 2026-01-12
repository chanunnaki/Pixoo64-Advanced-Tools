import torch
from diffusers import AutoPipelineForText2Image
import time
from pixoo1664 import Pixoo
from PIL import Image, ImageDraw
import sys
import os

PIXOO_IP = "192.168.100.45"
MODEL_ID = "stabilityai/sdxl-turbo" 

def main():
    try:
        print(f"Connecting to Pixoo at {PIXOO_IP}...")
        pixoo = Pixoo(PIXOO_IP)

        print(f"Loading SDXL-TURBO onto Mac Mini M4 (MPS)...")
        pipe = AutoPipelineForText2Image.from_pretrained(MODEL_ID, torch_dtype=torch.float16, variant="fp16")
        if torch.backends.mps.is_available():
            pipe.to("mps")

        prompt = "flashcard of a cute baby penguin, pixel art, minimalist, white background"
        
        print(f"Generating image (SDXL Quality - 1 Step)...")
        
        start_time = time.time()
        # Using 1 step to balance speed on the 16GB Mini
        image = pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0, width=512, height=512).images[0]
        gen_time = time.time() - start_time
        
        print(f"Generation Complete! Time: {gen_time:.2f} seconds")

        # Process Layout (64x52 + Bar)
        TOTAL_W, TOTAL_H = 64, 64
        art_layer = image.resize((TOTAL_W, 52), Image.Resampling.NEAREST)
        final_image = Image.new("RGB", (TOTAL_W, TOTAL_H), "black")
        final_image.paste(art_layer, (0, 0))
        draw = ImageDraw.Draw(final_image)
        draw.text((15, 54), "PENGUIN", fill="white")

        pixoo.send_image(final_image)
        print("Success!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
