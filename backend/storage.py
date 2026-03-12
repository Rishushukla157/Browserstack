import os
from config.settings import SUPABASE_URL
from backend.database import db


def save_and_upload_image(local_path: str, filename: str) -> dict:
    """
    Image already saved locally by image_downloader.py.
    This function also uploads it to Supabase Storage.
    Returns: { local_path, supabase_url }
    """
    result = {
        "local_path":   local_path,
        "supabase_url": ""
    }

    if not SUPABASE_URL:
        print("[STORAGE] Supabase not configured — local only")
        return result

    if not local_path or not os.path.exists(local_path):
        print(f"[STORAGE] File not found: {local_path}")
        return result

    try:
        client      = db.client
        bucket_name = "article-images"

        with open(local_path, "rb") as f:
            file_data = f.read()

        client.storage.from_(bucket_name).upload(
            path=filename,
            file=file_data,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )

        public_url             = client.storage.from_(bucket_name).get_public_url(filename)
        result["supabase_url"] = public_url

        print(f"[STORAGE] ✅ Local → {local_path}")
        print(f"[STORAGE] ✅ Cloud → {public_url}")

    except Exception as e:
        print(f"[STORAGE] Upload failed: {e} — local copy still safe")

    return result