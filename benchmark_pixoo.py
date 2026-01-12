from pixoo1664 import Pixoo
from PIL import Image
import time
import sys

PIXOO_IP = "192.168.100.45"

try:
    print(f"Connecting to Pixoo at {PIXOO_IP}...")
    pixoo = Pixoo(PIXOO_IP)
    
    # Pre-generate two simple images (Red and Blue) to avoid processing lag during test
    img_red = Image.new('RGB', (64, 64), color=(255, 0, 0))
    img_blue = Image.new('RGB', (64, 64), color=(0, 0, 255))
    
    NUM_FRAMES = 30
    print(f"Starting benchmark: Pushing {NUM_FRAMES} frames...")
    
    start_time = time.time()
    
    for i in range(NUM_FRAMES):
        if i % 2 == 0:
            pixoo.send_image(img_red)
        else:
            pixoo.send_image(img_blue)
        # Print a dot for progress without spamming newlines
        print(".", end="", flush=True)
            
    end_time = time.time()
    duration = end_time - start_time
    fps = NUM_FRAMES / duration
    
    print(f"\n\nBenchmark Complete!")
    print(f"Total Time: {duration:.2f} seconds")
    print(f"Average Speed: {fps:.2f} FPS")
    
except Exception as e:
    print(f"\nError: {e}")
    sys.exit(1)
