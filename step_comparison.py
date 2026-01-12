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

        print(f"Loading model '{MODEL_ID}'...")
        pipe = AutoPipelineForText2Image.from_pretrained(MODEL_ID, torch_dtype=torch.float16, variant="fp16")
        if torch.backends.mps.is_available():
            pipe.to("mps")

        prompt = "flashcard of a single colorful rainbow, pixel art, minimalist, centered on a plain white background, educational style"
        
        # The Ladder of Truth
        steps_to_test = [1, 4, 8, 50]

        for steps in steps_to_test:
            print(f"\n--- Generating with {steps} STEPS ---")
            
            start_time = time.time()
            image = pipe(prompt=prompt, num_inference_steps=steps, guidance_scale=0.0, width=512, height=512).images[0]
            gen_time = time.time() - start_time
            print(f"Time: {gen_time:.2f}s")

            # Process
            processed = image.resize((64, 64), Image.Resampling.NEAREST)
            draw = ImageDraw.Draw(processed)
            draw.rectangle([0, 52, 63, 63], fill="black")
            draw.text((10, 54), f"STEPS: {steps}", fill="white")

            # Display
            pixoo.send_image(processed)
            
            # Save
            filename = f"generated_images/test_steps_{steps}.png"
            processed.save(filename)
            
            print(f"Displayed and saved: {filename}")
            
            # Pause so you can look at it
            time.sleep(3)

        print("\nTest Complete!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
