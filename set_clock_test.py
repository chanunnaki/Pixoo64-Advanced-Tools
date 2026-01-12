import requests
import json
import time

PIXOO_IP = "192.168.100.45"
URL = f"http://{PIXOO_IP}/post"

def send(cmd):
    print(f"Sending: {cmd}")
    resp = requests.post(URL, data=json.dumps(cmd))
    print(f"Response: {resp.text}")

# 1. Reset the GIF ID
send({"Command": "Draw/ResetHttpGifId"})
time.sleep(0.5)

# 2. Set Index to 0 (Clock)
send({"Command": "Channel/SetIndex", "SelectIndex": 0})
time.sleep(0.5)

# 3. Specifically set clock ID 0 just in case
send({"Command": "Channel/SetClockSelectId", "ClockId": 0})

print("\nDone. Did it change?")