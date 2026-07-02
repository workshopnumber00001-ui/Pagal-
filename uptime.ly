import requests
import time
import os

URL = os.getenv("RENDER_URL", "https://your-app.onrender.com")
INTERVAL = 600  # 10 minutes

while True:
    try:
        requests.get(URL)
        print(f"Pinged {URL} at {time.ctime()}")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(INTERVAL)
