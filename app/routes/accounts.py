"""Account lifecycle: connect (easy login), list, configure, sync, remove."""
from __future__ import annotations

import os
import re

from fastapi import APIRouter, Depends, HTTPException

from .. import config, db, runtime, scheduler, security, google_auth
from ..google_auth import AuthError
from ..gpmc_runner import scan_media
from ..models import AccountUpdate, ConnectRaw, ConnectToken

router = APIRouter(prefix="/api")


def _slug(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip().lower()).strip("_")
    return text or "account"


def _unique_folder(base: str) -> str:
    existing = {a["folder"] for a in db.list_accounts()}
    if base not in existing:
        return base
    i = 2
    while f"{base}-{i}" in existing:
        i += 1
    return f"{base}-{i}"


def _persist(res: dict, label: str) -> dict:
    email = res["email"]
    existing = db.get_account_by_email(email)
    if existing:
        db.update_auth(existing["id"], res["auth_data"], res["android_id"], email)
        if label:
            db.update_account(existing["id"], {"label": label})
        action, aid, folder = "updated", existing["id"], existing["folder"]
    else:
        folder = _unique_folder(_slug(email.split("@")[0]))
        os.makedirs(os.path.join(config.SYNC_DIR, folder), exist_ok=True)
        aid = db.create_account(email, folder, res["auth_data"], res["android_id"], label)
        action = "created"
    db.set_setting("setup_done", "true")
    db.add_history(aid, f"Account {action}: {email}", "success")
    return {"status": "ok", "action": action, "account_id": aid, "email": email, "folder": folder}


@router.post("/connect/token")
def connect_token(payload: ConnectToken, auth=Depends(security.require)):
    try:
        res = google_auth.connect_with_oauth_token(payload.oauth_token, config.HTTP_PROXY)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _persist(res, payload.label.strip())


@router.post("/connect/raw")
def connect_raw(payload: ConnectRaw, auth=Depends(security.require)):
    try:
        res = google_auth.connect_with_raw_auth(payload.auth_data, config.HTTP_PROXY)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _persist(res, payload.label.strip())


def _preview(folder_abs: str, recursive: bool, limit: int = 8) -> list[dict]:
    files, _ = scan_media(folder_abs, recursive)
    out = []
    for f in files[:limit]:
        rel = os.path.relpath(f, config.SYNC_DIR).replace("\\", "/")
        ext = os.path.splitext(f)[1].lower()
        out.append({
            "path": rel,
            "name": os.path.basename(f),
            "is_video": ext in config.VIDEO_EXTS,
            "ext": ext.lstrip(".").upper(),
        })
    return out


def _account_view(acc: dict) -> dict:
    aid = acc["id"]
    folder_abs = os.path.join(config.SYNC_DIR, acc["folder"])
    snap = runtime.snapshot(aid)
    view = {k: acc[k] for k in acc if k != "auth_data"}
    view["auth_data"] = "connected"
    view["runtime"] = snap
    view["preview"] = _preview(folder_abs, bool(acc.get("recursive", 1)))
    return view


@router.get("/accounts")
def list_accounts(auth=Depends(security.require)):
    return [_account_view(a) for a in db.list_accounts()]


@router.get("/accounts/{account_id}")
def get_account(account_id: int, auth=Depends(security.require)):
    acc = db.get_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return _account_view(acc)


@router.put("/accounts/{account_id}")
def update_account(account_id: int, payload: AccountUpdate, auth=Depends(security.require)):
    acc = db.get_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    db.update_account(account_id, payload.model_dump())
    return {"status": "ok"}


@router.post("/accounts/{account_id}/pause")
def toggle_pause(account_id: int, auth=Depends(security.require)):
    acc = db.get_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    new_state = 0 if acc.get("enabled", 1) else 1
    db.update_account(account_id, {"enabled": bool(new_state)})
    runtime.update(account_id, status="disabled" if not new_state else "pending")
    return {"status": "ok", "enabled": bool(new_state)}


@router.post("/accounts/{account_id}/sync")
def sync_now(account_id: int, auth=Depends(security.require)):
    acc = db.get_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    started = scheduler.trigger(account_id)
    return {"status": "ok" if started else "busy"}


@router.get("/accounts/{account_id}/logs")
def account_logs(account_id: int, auth=Depends(security.require)):
    return {"live": runtime.logs(account_id), "history": db.list_history(account_id, 100)}


@router.get("/accounts/{account_id}/reveal")
def reveal_auth(account_id: int, auth=Depends(security.require)):
    if db.get_setting("allow_reveal_auth", "false") != "true":
        raise HTTPException(status_code=403, detail="Revealing auth_data is disabled in Settings")
    acc = db.get_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"auth_data": acc["auth_data"]}


@router.put("/accounts/reorder")
def reorder(order: list[int], auth=Depends(security.require)):
    db.set_priority(order)
    return {"status": "ok"}


@router.delete("/accounts/{account_id}")
def delete_account(account_id: int, delete_folder: bool = False, auth=Depends(security.require)):
    acc = db.get_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    if delete_folder:
        import shutil
        shutil.rmtree(os.path.join(config.SYNC_DIR, acc["folder"]), ignore_errors=True)
    db.delete_account(account_id)
    runtime.forget(account_id)
    return {"status": "ok"}
