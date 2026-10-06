"""Optional password lock for the web UI (single shared session)."""
from __future__ import annotations

import os

import bcrypt
from fastapi import HTTPException, Request

from . import db

SESSION_TOKEN = os.urandom(24).hex()
COOKIE = "gpmc_session"


def has_password() -> bool:
    return bool(db.get_setting("ui_password_hash", ""))


def set_password(password: str | None) -> None:
    if password is None:
        return
    if password == "":
        db.set_setting("ui_password_hash", "")
        return
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db.set_setting("ui_password_hash", hashed)


def check_password(password: str) -> bool:
    stored = db.get_setting("ui_password_hash", "")
    if not stored:
        return True
    try:
        return bcrypt.checkpw(password.encode(), stored.encode())
    except Exception:
        return False


def is_authenticated(request: Request) -> bool:
    if not has_password():
        return True
    return request.cookies.get(COOKIE) == SESSION_TOKEN


def require(request: Request) -> bool:
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
