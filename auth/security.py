from fastapi import HTTPException, Cookie, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import os
from typing import Optional

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME")
JWT_ALGORITHM = "HS256"

# TTLs from env with sane defaults
ACCESS_TOKEN_TTL = int(os.getenv("ACCESS_TOKEN_TTL", 900))          # 15 minutes
REFRESH_TOKEN_TTL = int(os.getenv("REFRESH_TOKEN_TTL", 604800))     # 7 days

# --------------------------------------------------------------------
# Token creation helpers
# --------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(uid: str) -> str:
    """Create short-lived access JWT."""
    payload = {
        "sub": uid,
        "type": "access",
        "exp": _now() + timedelta(seconds=ACCESS_TOKEN_TTL),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(uid: str) -> str:
    """Create long-lived refresh JWT."""
    payload = {
        "sub": uid,
        "type": "refresh",
        "exp": _now() + timedelta(seconds=REFRESH_TOKEN_TTL),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# --------------------------------------------------------------------
# Verification helpers
# --------------------------------------------------------------------

def _decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")


def verify_access_token(token: str) -> str:
    payload = _decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=403, detail="Invalid token type")
    return payload["sub"]


# --------------------------------------------------------------------
# Dependency: extract Bearer token from Authorization header
# --------------------------------------------------------------------

_http_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(_http_bearer),
    authorization: Optional[str] = Header(None),
) -> str:
    """Return user_id encoded in a valid access JWT.

    Works with both standard Bearer auth (preferred) and manual header input in Swagger.
    """
    token: Optional[str] = None

    # Preferred path: parsed by HTTPBearer
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    # Fallback: raw header string (if user entered via parameters list)
    elif authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]

    if not token:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    return verify_access_token(token)

# Kept for backward compatibility with cookie-based auth

def access_token_required(token: str = Cookie(None)):
    if not token:
        raise HTTPException(status_code=403, detail="Token missing")
    return verify_access_token(token)