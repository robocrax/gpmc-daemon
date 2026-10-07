"""Device Sync: manage Syncthing phones and map them to accounts, from the GPMC UI."""
from __future__ import annotations

import os
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import config, db, security, syncthing
from ..syncthing import SyncthingError
from .media import _lan_ips

router = APIRouter(prefix="/api")

_DEVICE_RE = re.compile(r"^[A-Z0-9]{7}(-[A-Z0-9]{7}){7}$")


class LinkDevice(BaseModel):
    device_id: str
    name: str = ""
    account_id: int


def _norm_device(raw: str) -> str:
    dev = (raw or "").strip().upper().replace(" ", "")
    if not _DEVICE_RE.match(dev):
        raise HTTPException(status_code=400, detail="That doesn't look like a Syncthing Device ID (it's a long XXXXXXX-XXXXXXX-… string).")
    return dev


def _gui_url() -> str:
    if config.SYNCTHING_GUI_URL:
        return config.SYNCTHING_GUI_URL
    ips = _lan_ips()
    return f"http://{ips[0]}:8384" if ips else ""


@router.get("/syncthing/status")
def status(auth=Depends(security.require)):
    if not syncthing.available():
        return {"available": False, "config_path": config.SYNCTHING_CONFIG}
    try:
        cfg = syncthing._config()
        me = syncthing.my_id()
        conns = syncthing._connections()
        folders = {f["id"]: f for f in cfg.get("folders", [])}

        accounts, acct_by_folder = [], {}
        for a in db.list_accounts():
            fid = syncthing.folder_id_for(a["folder"])
            f = folders.get(fid)
            shared = [d["deviceID"] for d in f.get("devices", [])] if f else []
            accounts.append({
                "id": a["id"], "email": a["email"], "label": a["label"] or a["email"],
                "folder": a["folder"], "st_folder_id": fid, "exists": bool(f),
                "device_ids": [d for d in shared if d != me],
            })
            acct_by_folder[fid] = a["id"]

        def account_for(dev_id):
            for fid, f in folders.items():
                if fid.startswith("gpmc-") and any(d["deviceID"] == dev_id for d in f.get("devices", [])):
                    return acct_by_folder.get(fid)
            return None

        devices = []
        for d in cfg.get("devices", []):
            if d["deviceID"] == me:
                continue
            conn = conns.get(d["deviceID"], {})
            devices.append({
                "id": d["deviceID"], "name": d.get("name", ""),
                "connected": bool(conn.get("connected")), "address": conn.get("address", ""),
                "account_id": account_for(d["deviceID"]),
            })

        pending = [{"id": k, "name": v.get("name", ""), "address": v.get("address", "")}
                   for k, v in syncthing._pending_devices().items()]

        return {"available": True, "my_id": me, "gui_url": _gui_url(),
                "accounts": accounts, "devices": devices, "pending": pending}
    except SyncthingError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Syncthing error: {exc}")


@router.post("/syncthing/link")
def link(payload: LinkDevice, auth=Depends(security.require)):
    acc = db.get_account(payload.account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    dev_id = _norm_device(payload.device_id)
    try:
        existing = {d["deviceID"] for d in syncthing._config().get("devices", [])}
        if dev_id not in existing:
            syncthing.add_device(dev_id, payload.name.strip())
        fid = syncthing.folder_id_for(acc["folder"])
        path = os.path.join(config.SYNC_DIR, acc["folder"])
        os.makedirs(path, exist_ok=True)
        syncthing.ensure_folder(fid, acc["email"], path, [dev_id])
        # keep it one-phone-to-one-account: drop it from other GPMC folders
        for f in syncthing._config().get("folders", []):
            if f["id"].startswith("gpmc-") and f["id"] != fid \
               and any(d["deviceID"] == dev_id for d in f.get("devices", [])):
                syncthing.unshare(f["id"], dev_id)
        db.add_history(acc["id"], f"Linked a device to backup ({dev_id[:7]}…)", "info")
        return {"status": "ok"}
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Syncthing rejected the change: {exc.response.text[:200]}")
    except SyncthingError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Syncthing error: {exc}")


@router.delete("/syncthing/devices/{device_id}")
def remove(device_id: str, auth=Depends(security.require)):
    try:
        syncthing.remove_device(device_id.strip().upper())
        return {"status": "ok"}
    except SyncthingError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Syncthing error: {exc}")
