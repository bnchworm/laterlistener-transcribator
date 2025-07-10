from fastapi import HTTPException, Cookie, Header, HTTPException, status, Depends
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import os
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or "change_me_in_prod"
JWT_ALGORITHM = "HS256"

# Время жизни токенов (секунд): access по умолчанию 15 минут, refresh — 7 дней
ACCESS_TOKEN_TTL = int(os.getenv("ACCESS_TOKEN_TTL", 900))
REFRESH_TOKEN_TTL = int(os.getenv("REFRESH_TOKEN_TTL", 604800))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(uid: str) -> str:
    payload = {
        "sub": uid,
        "type": "access",
        # "exp": _now() + timedelta(seconds=ACCESS_TOKEN_TTL),  # TTL отключён временно
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(uid: str) -> str:
    payload = {
        "sub": uid,
        "type": "refresh",
        # "exp": _now() + timedelta(seconds=REFRESH_TOKEN_TTL),  # TTL отключён временно
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Токен недействителен или срок его действия истёк")


def verify_access_token(token: str) -> str:
    payload = _decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=403, detail="Неверный тип токена")
    return payload["sub"]


security = HTTPBearer()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return verify_access_token(credentials.credentials)


def access_token_required(token: str = Cookie(None)):
    if not token:
        raise HTTPException(status_code=403, detail="Отсутствует токен в cookie")
    return verify_access_token(token)

def verify_service_token(authorization: str = Header(...)):
    SERVICE_API_TOKEN = os.getenv("SERVICE_API_TOKEN")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth header")
    token = authorization.split(" ", 1)[1]
    if token != SERVICE_API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")