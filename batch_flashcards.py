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

# The Playlist v2 (20 Words)
FLASHCARDS = [
    "BALL", "CAT", "DOG", "FISH", "DUCK",
    "HOUSE", "TREE", "FLOWER", "SUN", "MOON",
    "BIRD", "SHOE", "KEY", "CHAIR", "SPOON",
    "CLOCK", "CAKE", "PIZZA", "TRUCK", "TRAIN"
]
DELAY_SECONDS = 20

def main():
    try:
        print(f"Connecting to Pixoo at {PIXOO_IP}...")
        pixoo = Pixoo(PIXOO_IP)

        print(f"Loading model '{MODEL_ID}'...")
        pipe = AutoPipelineForText2Image.from_pretrained(MODEL_ID, torch_dtype=torch.float16, variant="fp16")
        if torch.backends.mps.is_available():
            pipe.to("mps")

        for i, subject in enumerate(FLASHCARDS):
            prompt = f"flashcard of a single {subject.lower()}, pixel art, minimalist, centered on a plain white background, educational style"
            
            print(f"\n[{i+1}/{len(FLASHCARDS)}] Generating: {subject}")
            
            # Generate (8 Steps)
            image = pipe(prompt=prompt, num_inference_steps=8, guidance_scale=0.0, width=512, height=512).images[0]

            # Process Layout (64x52 + Bar)
            TOTAL_W, TOTAL_H = 64, 64
            LABEL_H = 12
            ART_H = TOTAL_H - LABEL_H 
            
            art_layer = image.resize((TOTAL_W, ART_H), Image.Resampling.NEAREST)
            final_image = Image.new("RGB", (TOTAL_W, TOTAL_H), "black")
            final_image.paste(art_layer, (0, 0))
            
            draw = ImageDraw.Draw(final_image)
            
            # Label
            try:
                label_text = subject
                if len(label_text) > 8: label_text = label_text[:8] 
                start_x = 32 - (len(label_text) * 3)
                draw.text((start_x, 54), label_text, fill="white")
            except:
                pass

            # Display
            pixoo.send_image(final_image)
            print(f"Displayed: {subject}")
            
            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = subject.replace(" ", "_").lower()
            filename = f"generated_images/{safe_name}_{timestamp}.png"
            final_image.save(filename)

            if i < len(FLASHCARDS) - 1:
                print(f"Waiting {DELAY_SECONDS} seconds...")
                time.sleep(DELAY_SECONDS)

        print("\nShow Complete!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
