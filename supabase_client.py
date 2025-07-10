import os
from supabase import create_client
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "transcriptions")

USERS_TABLE = os.getenv("SUPABASE_USERS_TABLE", "users")
ONE_TIME_TOKENS_TABLE = os.getenv("SUPABASE_ONE_TIME_TOKENS_TABLE", "one_time_tokens")
REFRESH_TOKENS_TABLE = os.getenv("SUPABASE_REFRESH_TOKENS_TABLE", "refresh_tokens")

supabase_conn: Any = None

def init_supabase_client():
    global supabase_conn
    try:
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "transcriptions")

        if supabase_conn is None:
            supabase_conn = create_client(SUPABASE_URL, SUPABASE_KEY)  # type: ignore[arg-type]
    except Exception as e:
        print(f"Failed to connect: {e}")

def upload_file_to_supabase(file_path: str, bucket: str, dest_name) -> str:
    global supabase_conn
    if supabase_conn is None:
        init_supabase_client()
    with open(file_path, "rb") as f:
        response = supabase_conn.storage.from_(bucket).upload(dest_name, f, {"content-type": "audio/wav"})
    public_url = supabase_conn.storage.from_(bucket).get_public_url(dest_name)
    return public_url


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_client():
    global supabase_conn
    if supabase_conn is None:
        init_supabase_client()


def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    _ensure_client()
    result = (
        supabase_conn
        .table(USERS_TABLE)
        .select("*")
        .eq("telegram_id", telegram_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def create_user(telegram_id: int) -> dict:
    _ensure_client()
    email = f"{telegram_id}@tg.laterlistener.com"
    insert = {
        "telegram_id": telegram_id,
        "email": email,
    }
    result = supabase_conn.table(USERS_TABLE).insert(insert).execute()
    return result.data[0]


def save_one_time_token(token_hash: str, telegram_id: int, ttl_seconds: int) -> None:
    _ensure_client()
    now = _now_utc()
    supabase_conn.table(ONE_TIME_TOKENS_TABLE).delete().or_(
        f"telegram_id.eq.{telegram_id},expires_at.lt.{now.isoformat()}"
    ).execute()

    expires_at = _now_utc() + timedelta(seconds=ttl_seconds)
    record = {
        "token_hash": token_hash,
        "telegram_id": telegram_id,
        "expires_at": expires_at.isoformat(),
    }
    supabase_conn.table(ONE_TIME_TOKENS_TABLE).insert(record).execute()


def get_one_time_token(token_hash: str) -> Optional[dict]:
    _ensure_client()
    result = (
        supabase_conn
        .table(ONE_TIME_TOKENS_TABLE)
        .select("*")
        .eq("token_hash", token_hash)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def delete_one_time_token(token_hash: str):
    _ensure_client()
    supabase_conn.table(ONE_TIME_TOKENS_TABLE).delete().eq("token_hash", token_hash).execute()


def _purge_old_refresh_tokens(user_id: str):
    _ensure_client()

    # 1. Удаляем все токены конкретного пользователя — им на смену придёт новый
    supabase_conn.table(REFRESH_TOKENS_TABLE).delete().eq("user_id", user_id).execute()

    # 2. Дополнительно удаляем все глобально просроченные токены
    now_iso = _now_utc().isoformat()
    supabase_conn.table(REFRESH_TOKENS_TABLE).delete().lt("expires_at", now_iso).execute()

def save_refresh_token(token_hash: str, user_id: str, ttl_seconds: int):
    _ensure_client()
    # Сначала чистим старые записи
    _purge_old_refresh_tokens(user_id)

    expires_at = _now_utc() + timedelta(seconds=ttl_seconds)
    record = {
        "token_hash": token_hash,
        "user_id": user_id,
        "expires_at": expires_at.isoformat(),
    }
    supabase_conn.table(REFRESH_TOKENS_TABLE).insert(record).execute()


def get_refresh_token(token_hash: str) -> Optional[dict]:
    _ensure_client()
    result = (
        supabase_conn
        .table(REFRESH_TOKENS_TABLE)
        .select("*")
        .eq("token_hash", token_hash)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def revoke_refresh_token(token_hash: str):
    _ensure_client()
    supabase_conn.table(REFRESH_TOKENS_TABLE).update({"revoked_at": _now_utc().isoformat()}).eq("token_hash", token_hash).execute()


