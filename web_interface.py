from fastapi import FastAPI, Response, HTTPException, Depends
from dotenv import load_dotenv
from schema import TaskStatus, TranscribeQuery, TokenPair
from psdb_client import init_db_client, add_task, get_task_status, get_task
from contextlib import asynccontextmanager

from supabase_client import upload_file_to_supabase

import os
from supabase import create_client, Client

from auth.security import (
    create_access_token,
    create_refresh_token,
    get_current_user_id,
)

# Supabase token/user helpers
from supabase_client import (
    save_one_time_token,
    get_one_time_token,
    delete_one_time_token,
    get_user_by_telegram_id,
    create_user,
    save_refresh_token,
    get_refresh_token,
    revoke_refresh_token,
)

import secrets
import hashlib
from datetime import datetime, timezone

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    init_db_client()
    yield
load_dotenv()
app = FastAPI(lifespan=lifespan)
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))  # type: ignore[arg-type]
ONE_TIME_TOKEN_TTL = int(os.getenv("ONE_TIME_TOKEN_TTL", 600))  # 10 minutes default

@app.post('/transcribe')
async def start_transcribe(query: TranscribeQuery):
    return add_task(query)


@app.get('/status/{task_id}')
async def get_transcribe_status(task_id: str):
    return get_task_status(task_id)


@app.get('/result/{task_id}')
async def get_transcribe_result(task_id: str):
    task = get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    if task.status != TaskStatus.finished:
        return {"error": "Task not finished"}
    return {"result_url": task.result_url}

@app.get("/protected")
def protected(user_id: str = Depends(get_current_user_id)):
    return {"message": f"Hello, user {user_id}!"}

# 1. Bot requests creation of one-time token
@app.post("/token/one-time/create")
def create_one_time_token(telegram_id: int):
    """Создать одноразовый токен. telegram_id передаётся как query/form параметр."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    save_one_time_token(token_hash, telegram_id, ONE_TIME_TOKEN_TTL)

    return {"token": raw_token}


# 2. Frontend exchanges one-time token for JWT pair
@app.post("/auth/one-time", response_model=TokenPair)
def auth_with_one_time(token: str):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    record = get_one_time_token(token_hash)
    if not record:
        raise HTTPException(status_code=401, detail="Invalid or used token")

    # Check expiration
    expires_at_str = record.get("expires_at")
    if expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            delete_one_time_token(token_hash)
            raise HTTPException(status_code=401, detail="Token expired")

    telegram_id = record["telegram_id"]
    user = get_user_by_telegram_id(telegram_id) or create_user(telegram_id)

    # Generate tokens
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])

    # Persist refresh token hash
    refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    from auth.security import REFRESH_TOKEN_TTL  # late import to avoid circular
    save_refresh_token(refresh_hash, user["id"], REFRESH_TOKEN_TTL)

    # Consume one-time token
    delete_one_time_token(token_hash)

    return TokenPair(access_token=access_token, refresh_token=refresh_token)


# 3. Refresh tokens
@app.post("/auth/refresh", response_model=TokenPair)
def refresh_tokens(refresh_token: str):
    refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    record = get_refresh_token(refresh_hash)
    if not record or record.get("revoked_at") is not None:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    # Verify expiration
    expires_at_str = record.get("expires_at")
    if expires_at_str:
        exp = datetime.fromisoformat(expires_at_str)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            revoke_refresh_token(refresh_hash)
            raise HTTPException(status_code=401, detail="Refresh token expired")

    # Decode JWT to ensure signature and expiry correct
    from auth.security import _decode_token  # type: ignore
    try:
        payload_data = _decode_token(refresh_token)
    except HTTPException:
        revoke_refresh_token(refresh_hash)
        raise

    if payload_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload_data["sub"]

    # Rotate tokens: revoke old, issue new
    revoke_refresh_token(refresh_hash)

    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)
    new_refresh_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
    from auth.security import REFRESH_TOKEN_TTL
    save_refresh_token(new_refresh_hash, user_id, REFRESH_TOKEN_TTL)

    return TokenPair(access_token=new_access, refresh_token=new_refresh)

# New protected route using Authorization header
@app.get("/me")
def me(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id}