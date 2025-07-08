from fastapi import HTTPException, Cookie
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"

def create_access_token(uid: str, expires_delta: timedelta = timedelta(hours=1)):
    payload = {
        "sub": uid,
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def access_token_required(token: str = Cookie(None)):
    if not token:
        raise HTTPException(status_code=403, detail="Token missing")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")