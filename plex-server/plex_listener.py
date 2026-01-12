import sys
import time
print("Script starting...", flush=True)
import requests
from plexapi.server import PlexServer
from PIL import Image, ImageDraw
import io
import base64
import os

# Configuration
PLEX_URL = 'http://127.0.0.1:32400'
PLEX_TOKEN = 'ryXAY6LKzwfb321xo9hD'
PIXOO_IP = '192.168.100.45'

# Pixoo API Endpoint
PIXOO_URL = f"http://{PIXOO_IP}/post"

# State Tracking
last_track_key = None
pic_id_counter = 1

def send_to_pixoo(image):
    """Sends a PIL image to the Pixoo 64 using raw RGB bytes (Library Standard)."""
    global pic_id_counter
    try:
        # Increment PicID
        pic_id_counter += 1
        if pic_id_counter > 60: pic_id_counter = 1
        
        # Exact logic from pixoo1664 library
        img_str = base64.b64encode(bytearray(image.tobytes("raw", "RGB"))).decode()
        
        # Payload for Pixoo
        payload = {
            "Command": "Draw/SendHttpGif",
            "PicNum": 1,
            "PicWidth": 64,
            "PicOffset": 0,
            "PicID": pic_id_counter,
            "PicSpeed": 1000,
            "PicData": img_str
        }
        
        print(f"Sending image to Pixoo at {PIXOO_IP}...", file=sys.stderr)
        requests.post(PIXOO_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending to Pixoo: {e}", file=sys.stderr)

def get_base_art(thumb_url):
    """Downloads and resizes album art to 64x64. Returns PIL Image."""
    try:
        # Added timeout=10 to prevent hanging forever
        img_data = requests.get(thumb_url, headers={'X-Plex-Token': PLEX_TOKEN}, stream=True, timeout=10).content
        img = Image.open(io.BytesIO(img_data)).convert('RGB')
        return img.resize((64, 64), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Error downloading art: {e}", file=sys.stderr)
        return None

def main():
    global last_track_key
    print(f"Connecting to Plex at {PLEX_URL}...", file=sys.stderr)
    try:
        # Create a session with timeout
        session = requests.Session()
        plex = PlexServer(PLEX_URL, PLEX_TOKEN, session=session, timeout=10)
        print("Connected! Listening for music...", file=sys.stderr)
    except Exception as e:
        print(f"Failed to connect to Plex: {e}", file=sys.stderr)
        time.sleep(30)
        return

    last_heartbeat = time.time()

    while True:
        try:
            if time.time() - last_heartbeat > 60:
                print("Heartbeat: Still listening...", file=sys.stderr)
                last_heartbeat = time.time()

            sessions = plex.sessions()
            music_sessions = [s for s in sessions if s.type == 'track']
            
            if music_sessions:
                track = music_sessions[0]
                
                # Check if track changed
                current_key = track.ratingKey
                if current_key != last_track_key:
                    print(f"New Track Detected: {track.title}", file=sys.stderr)
                    last_track_key = current_key
                    
                    # Get new art
                    art_img = get_base_art(track.thumbUrl)
                    if art_img:
                        send_to_pixoo(art_img)
            
            else:
                # Reset state when stopped
                last_track_key = None
                
            time.sleep(2.0) # Check every 2 seconds
            
        except Exception as e:
            print(f"Loop error: {e}", file=sys.stderr)
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}", file=sys.stderr)
        import time
        time.sleep(60)