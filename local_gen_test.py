import torch
from diffusers import AutoPipelineForText2Image
import time
from pixoo1664 import Pixoo
from PIL import Image, ImageDraw
import sys
import os
from datetime import datetime

PIXOO_IP = "192.168.100.45"
MODEL_ID = "stabilityai/sdxl-turbo"

def main():
    try:
        print(f"Connecting to Pixoo at {PIXOO_IP}...")
        pixoo = Pixoo(PIXOO_IP)

        print(f"Loading model '{MODEL_ID}' onto M4 Max (Metal/MPS)...")
        # Initialize the pipeline
        pipe = AutoPipelineForText2Image.from_pretrained(MODEL_ID, torch_dtype=torch.float16, variant="fp16")
        
        # Check for Apple Silicon (MPS)
        if torch.backends.mps.is_available():
            pipe.to("mps")
            print("Using MPS acceleration.")
        else:
            print("MPS not available, using CPU (slow).")
            pipe.to("cpu")

        # Check for command line argument
        if len(sys.argv) > 1:
            subject = " ".join(sys.argv[1:])
        else:
            subject = "red apple" # Default

        # Flashcard Prompt Template
        prompt = f"flashcard of a single {subject}, pixel art, minimalist, centered on a plain white background, educational style"
        
        print(f"Generating image for prompt: '{prompt}' (Ultra Quality Mode - 8 Steps)...")
        
        # 8 Steps is the sweet spot for the best quality/speed balance on M4 Max
        start_time = time.time()
        image = pipe(prompt=prompt, num_inference_steps=8, guidance_scale=0.0, width=512, height=512).images[0]
        gen_time = time.time() - start_time
        
        print(f"Generation Complete! Time: {gen_time:.2f} seconds")

        # Process for Pixoo (64x64)
        print("Resizing and composing...")
        
        # Target Dimensions
        TOTAL_W, TOTAL_H = 64, 64
        LABEL_H = 12
        ART_H = TOTAL_H - LABEL_H # 52 pixels
        
        # Resize AI image to fit the top area (64x52)
        # We stretch it slightly vertically, but at this resolution it's unnoticeable
        # and better than cropping.
        art_layer = image.resize((TOTAL_W, ART_H), Image.Resampling.NEAREST)
        
        # Create final canvas
        final_image = Image.new("RGB", (TOTAL_W, TOTAL_H), "black")
        
        # Paste Art at Top
        final_image.paste(art_layer, (0, 0))
        
        # Draw Label at Bottom
        draw = ImageDraw.Draw(final_image)
        # (Background is already black from new image creation)
        
        try:
            # Use the subject name as label (uppercase)
            label_text = subject.split()[-1].upper() 
            if len(label_text) > 8: label_text = label_text[:8] 
            
            # Basic centering
            start_x = 32 - (len(label_text) * 3)
            # Text Y position: 52 (start of bar) + 2 (padding) = 54
            draw.text((start_x, 54), label_text, fill="white")
        except:
            pass

        pixoo.send_image(final_image)
        
        # Save locally
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = subject.replace(" ", "_")
        filename = f"generated_images/{safe_name}_{timestamp}.png"
        final_image.save(filename)
        print(f"Saved generated image to: {filename}")
        
        print("Success!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
