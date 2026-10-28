from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import Professional

COOKIE_NAME = "kinetra_session"
_hasher = PasswordHash.recommended()  # argon2


def hash_password(p: str) -> str:
    return _hasher.hash(p)


def verify_password(p: str, h: str) -> bool:
    return _hasher.verify(p, h)


def create_token(professional_id: int) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(professional_id), "iat": now, "exp": now + timedelta(hours=s.session_hours)},
                      s.secret_key, algorithm="HS256")


def current_professional(request: Request, db: Session = Depends(get_db)) -> Professional:
    token = request.cookies.get(COOKIE_NAME)
    unauth = HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")
    if not token:
        raise unauth
    try:
        data = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
        pid = int(data["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauth
    prof = db.get(Professional, pid)
    if not prof or not prof.is_active:
        raise unauth
    return prof
