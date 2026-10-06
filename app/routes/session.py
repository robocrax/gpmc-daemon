"""UI session, global settings, and health."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from .. import config, db, security
from ..models import GlobalSettings, LoginRequest

router = APIRouter(prefix="/api")


@router.get("/session")
def session(request: Request):
    return {
        "app": config.APP_NAME,
        "version": config.VERSION,
        "has_password": security.has_password(),
        "authenticated": security.is_authenticated(request),
        "setup_done": db.get_setting("setup_done", "false") == "true",
        "theme": db.get_setting("theme", "system"),
    }


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    if not security.check_password(payload.password):
        raise HTTPException(status_code=401, detail="Wrong password")
    response.set_cookie(
        security.COOKIE, security.SESSION_TOKEN,
        httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30,
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(security.COOKIE)
    return {"status": "ok"}


@router.get("/settings")
def get_settings(auth=Depends(security.require)):
    return {
        "sync_interval_min": int(db.get_setting("sync_interval_min", "5")),
        "webhook_url": db.get_setting("webhook_url", ""),
        "allow_reveal_auth": db.get_setting("allow_reveal_auth", "false") == "true",
        "theme": db.get_setting("theme", "system"),
        "has_password": security.has_password(),
        "config_dir": str(config.CONFIG_DIR),
        "sync_dir": str(config.SYNC_DIR),
    }


@router.post("/settings")
def save_settings(payload: GlobalSettings, auth=Depends(security.require)):
    db.set_setting("sync_interval_min", payload.sync_interval_min)
    db.set_setting("webhook_url", payload.webhook_url or "")
    db.set_setting("allow_reveal_auth", str(payload.allow_reveal_auth).lower())
    db.set_setting("theme", payload.theme or "system")
    if payload.password is not None:
        security.set_password(payload.password)
    return {"status": "ok"}


@router.get("/health")
def health():
    return {"status": "ok", "version": config.VERSION}
