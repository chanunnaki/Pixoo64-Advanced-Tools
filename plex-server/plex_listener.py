import sys
import time
import json
import requests
import base64
import io
from plexapi.server import PlexServer
from PIL import Image, ImageDraw

print("Script starting...", flush=True)

# Configuration
PLEX_URL = 'http://127.0.0.1:32400'
PLEX_TOKEN = 'ryXAY6LKzwfb321xo9hD'
PIXOO_IP = '192.168.100.45'

# Pixoo API Endpoint
PIXOO_URL = f"http://{PIXOO_IP}/post"

# State Tracking
last_track_key = None
pic_id_counter = 100 
last_playing_time = time.time()
is_idle = False

def set_clock(clock_id=0):
    """Safely returns the Pixoo to the clock face."""
    try:
        # 1. Reset the GIF stream buffer first
        requests.post(PIXOO_URL, data=json.dumps({"Command": "Draw/ResetHttpGifId"}), timeout=5)
        time.sleep(0.5)
        
        # 2. Switch to Clock Index (0)
        payload = {
            "Command": "Channel/SetIndex",
            "SelectIndex": 0
        }
        print("Music stopped. Returning to clock face...", file=sys.stderr)
        requests.post(PIXOO_URL, data=json.dumps(payload), timeout=5)
    except Exception as e:
        print(f"Error setting clock: {e}", file=sys.stderr)

def send_to_pixoo(image):
    """Sends a PIL image to the Pixoo 64 using raw RGB bytes (Exact Library Standard)."""
    global pic_id_counter
    try:
        pic_id_counter += 1
        if pic_id_counter > 200: pic_id_counter = 100
        
        raw_bytes = bytearray(image.tobytes("raw", "RGB"))
        img_str = base64.b64encode(raw_bytes).decode('utf-8')
        
        payload = {
            "Command": "Draw/SendHttpGif",
            "PicNum": 1,
            "PicWidth": 64,
            "PicOffset": 0,
            "PicID": pic_id_counter,
            "PicSpeed": 1000,
            "PicData": img_str
        }
        
        print(f"Sending image to Pixoo at {PIXOO_IP} (ID: {pic_id_counter})...", file=sys.stderr)
        requests.post(PIXOO_URL, data=json.dumps(payload), timeout=5)
    except Exception as e:
        print(f"Error sending to Pixoo: {e}", file=sys.stderr)

def get_base_art(thumb_url):
    """Downloads and resizes album art to 64x64. Returns PIL Image."""
    try:
        img_data = requests.get(thumb_url, headers={'X-Plex-Token': PLEX_TOKEN}, stream=True, timeout=10).content
        img = Image.open(io.BytesIO(img_data)).convert('RGB')
        return img.resize((64, 64), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Error downloading art: {e}", file=sys.stderr)
        return None

def main():
    global last_track_key, last_playing_time, is_idle
    print(f"Connecting to Plex at {PLEX_URL}...", file=sys.stderr)
    try:
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
            # Filter for active music sessions that are actually PLAYING
            music_sessions = [s for s in sessions if s.type == 'track' and s.player.state == 'playing']
            
            if music_sessions:
                track = music_sessions[0]
                last_playing_time = time.time()
                is_idle = False
                
                current_key = track.ratingKey
                if current_key != last_track_key:
                    print(f"New Track Detected: {track.title}", file=sys.stderr)
                    last_track_key = current_key
                    art_img = get_base_art(track.thumbUrl)
                    if art_img:
                        send_to_pixoo(art_img)
            
            else:
                # Nothing is playing. Check if we should go to clock.
                if not is_idle and (time.time() - last_playing_time > 60):
                    set_clock(0)
                    is_idle = True
                    last_track_key = None # Reset so it re-sends if track starts again
                
            time.sleep(2.0)
            
        except Exception as e:
            print(f"Loop error: {e}", file=sys.stderr)
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}", file=sys.stderr)
        time.sleep(60)
