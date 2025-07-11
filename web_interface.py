from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from schema import TaskStatus, TranscribeQuery, TokenPair, OneTimeTokenQuery
from psdb_client import init_db_client, add_task, get_task_status, get_task
from contextlib import asynccontextmanager

from supabase_client import upload_file_to_supabase

import os
from supabase import create_client, Client

from auth.security import (
    create_access_token,
    create_refresh_token,
    get_current_user_id,
    verify_service_token
)

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
    init_db_client()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  #список разрешённых доменов, например: ["https://your-frontend.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))  # type: ignore

ONE_TIME_TOKEN_TTL = int(os.getenv("ONE_TIME_TOKEN_TTL", 600))

@app.post('/transcribe')
async def start_transcribe(query: TranscribeQuery, _: None = Depends(verify_service_token)):
    return add_task(query)


@app.get('/status/{task_id}')
async def get_transcribe_status(task_id: str, _: None = Depends(verify_service_token)):
    return get_task_status(task_id)


@app.get('/result/{task_id}')
async def get_transcribe_result(task_id: str, _: None = Depends(verify_service_token)):
    task = get_task(task_id)
    if not task:
        return {"error": "Задача не найдена"}
    if task.status != TaskStatus.finished:
        return {"error": "Задача ещё не завершена"}
    return {"result_url": task.result_url}

# 1. Создание одноразового токена (вызывает бот)
@app.post("/token/one-time/create")
def create_one_time_token(query: OneTimeTokenQuery, _: None = Depends(verify_service_token)):
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    save_one_time_token(token_hash, query.telegram_id, ONE_TIME_TOKEN_TTL)

    return {"token": raw_token}


# 2. Обмен одноразового токена на пару JWT (вызывает фронтенд)
@app.post("/auth/one-time", response_model=TokenPair)
def auth_with_one_time(token: str):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    record = get_one_time_token(token_hash)
    if not record:
        raise HTTPException(status_code=401, detail="Недействительный или уже использованный токен")

    # Проверяем срок действия токена
    expires_at_str = record.get("expires_at")
    if expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            delete_one_time_token(token_hash)
            raise HTTPException(status_code=401, detail="Срок действия токена истёк")

    telegram_id = record["telegram_id"]
    user = get_user_by_telegram_id(telegram_id) or create_user(telegram_id)

    # Генерируем JWT-токены
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])

    # Сохраняем хэш refresh-токена
    refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    from auth.security import REFRESH_TOKEN_TTL  # late import to avoid circular
    save_refresh_token(refresh_hash, user["id"], REFRESH_TOKEN_TTL)

    # Удаляем одноразовый токен
    delete_one_time_token(token_hash)

    return TokenPair(access_token=access_token, refresh_token=refresh_token)


# 3. Обновление пары токенов по refresh-токену
@app.post("/auth/refresh", response_model=TokenPair)
def refresh_tokens(refresh_token: str):
    refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    record = get_refresh_token(refresh_hash)
    if not record or record.get("revoked_at") is not None:
        raise HTTPException(status_code=401, detail="Недействительный или отозванный refresh-токен")

    # Проверяем срок действия токена
    expires_at_str = record.get("expires_at")
    if expires_at_str:
        exp = datetime.fromisoformat(expires_at_str)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            revoke_refresh_token(refresh_hash)
            raise HTTPException(status_code=401, detail="Срок действия refresh-токена истёк")

    from auth.security import _decode_token 
    try:
        payload_data = _decode_token(refresh_token)
    except HTTPException:
        revoke_refresh_token(refresh_hash)
        raise

    if payload_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Неверный тип токена")

    user_id = payload_data["sub"]

    # Выполняем ротацию: отзываем старый refresh-токен и выпускаем новый
    revoke_refresh_token(refresh_hash)

    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)
    new_refresh_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
    from auth.security import REFRESH_TOKEN_TTL
    save_refresh_token(new_refresh_hash, user_id, REFRESH_TOKEN_TTL)

    return TokenPair(access_token=new_access, refresh_token=new_refresh)

# Новый защищённый эндпоинт, использующий заголовок Authorization
@app.get("/me")
def me(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id}