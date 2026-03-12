import os
import requests

def download_image(image_url, index):
    if not image_url:
        return None

    os.makedirs("output", exist_ok=True)

    filename = f"article_{index}.jpg"
    filepath = os.path.join("output", filename)

    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"[IMAGE] Saved locally → {filepath}")
            return filepath                          # ← only change
    except Exception as e:
        print(f"[IMAGE] Failed to download: {e}")

    return None