import json
import os

OUTPUT_FILE = "output/articles.json"

def save_json(data):
    os.makedirs("output", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"\n[OUTPUT] Saved to {OUTPUT_FILE}")