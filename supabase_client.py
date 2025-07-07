import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "transcriptions")

supabase_conn = None

def init_supabase_client():
    global supabase_conn
    try:
        if supabase_conn is None:
            supabase_conn = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to connect: {e}")

def upload_file_to_supabase(file_path: str, bucket: str, dest_name) -> str:
    with open(file_path, "rb") as f:
        response = supabase_conn.storage.from_(bucket).upload(dest_name, f, {"content-type": "audio/wav"})
    # Получить публичный URL
    public_url = supabase_conn.storage.from_(bucket).get_public_url(dest_name)
    return public_url 