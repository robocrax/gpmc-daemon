"""Thin client for the local Syncthing instance's REST API.

GPMC and Syncthing run on the same host as the same user, so GPMC reads the API
key from Syncthing's config.xml and talks to its REST API on localhost. This lets
the GPMC UI pair phones and map them to accounts without the user needing direct
LAN access to the Syncthing GUI (works through the Cloudflare tunnel).
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET

import httpx

from . import config


class SyncthingError(Exception):
    pass


def _read_gui() -> tuple[str, str]:
    """Return (api_key, gui_address) parsed from Syncthing's config.xml."""
    if not os.path.isfile(config.SYNCTHING_CONFIG):
        raise SyncthingError("Syncthing is not installed on this server.")
    try:
        root = ET.parse(config.SYNCTHING_CONFIG).getroot()
        gui = root.find("gui")
        api_key = gui.findtext("apikey") if gui is not None else None
        address = gui.findtext("address") if gui is not None else None
        if not api_key:
            raise SyncthingError("Could not read the Syncthing API key.")
        return api_key, (address or "127.0.0.1:8384")
    except SyncthingError:
        raise
    except Exception as exc:
        raise SyncthingError(f"Could not read Syncthing config: {exc}") from exc


def _client() -> httpx.Client:
    api_key, _ = _read_gui()
    return httpx.Client(base_url=config.SYNCTHING_URL,
                        headers={"X-API-Key": api_key}, timeout=15)


def available() -> bool:
    try:
        with _client() as c:
            return c.get("/rest/system/ping").status_code == 200
    except Exception:
        return False


def my_id() -> str:
    with _client() as c:
        r = c.get("/rest/system/status"); r.raise_for_status()
        return r.json()["myID"]


def _config() -> dict:
    with _client() as c:
        r = c.get("/rest/config"); r.raise_for_status()
        return r.json()


def _connections() -> dict:
    try:
        with _client() as c:
            r = c.get("/rest/system/connections"); r.raise_for_status()
            return r.json().get("connections", {})
    except Exception:
        return {}


def _pending_devices() -> dict:
    try:
        with _client() as c:
            r = c.get("/rest/cluster/pending/devices")
            return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def add_device(device_id: str, name: str) -> None:
    device_id = device_id.strip().upper().replace(" ", "")
    dev = {"deviceID": device_id, "name": name or device_id[:7],
           "addresses": ["dynamic"], "compression": "metadata",
           "introducer": False, "paused": False}
    with _client() as c:
        r = c.put(f"/rest/config/devices/{device_id}", json=dev)
        r.raise_for_status()


def remove_device(device_id: str) -> None:
    with _client() as c:
        # drop it from any folders first, then delete the device
        try:
            for f in c.get("/rest/config/folders").json():
                if any(d["deviceID"] == device_id for d in f.get("devices", [])):
                    f["devices"] = [d for d in f["devices"] if d["deviceID"] != device_id]
                    c.put(f"/rest/config/folders/{f['id']}", json=f)
        except Exception:
            pass
        c.delete(f"/rest/config/devices/{device_id}")


def ensure_folder(folder_id: str, label: str, path: str, device_ids: list[str]) -> None:
    """Create the folder (receive-only) if missing, or add devices to it. Additive."""
    with _client() as c:
        r = c.get(f"/rest/config/folders/{folder_id}")
        if r.status_code == 200:
            folder = r.json()
            existing = {d["deviceID"] for d in folder.get("devices", [])}
            for d in device_ids:
                if d not in existing:
                    folder.setdefault("devices", []).append({"deviceID": d})
            resp = c.put(f"/rest/config/folders/{folder_id}", json=folder)
        else:
            devices = [{"deviceID": my_id()}] + [{"deviceID": d} for d in device_ids]
            folder = {"id": folder_id, "label": label, "path": path,
                      "type": "receiveonly", "devices": devices,
                      "fsWatcherEnabled": True, "rescanIntervalS": 3600,
                      "ignorePerms": True}
            resp = c.put(f"/rest/config/folders/{folder_id}", json=folder)
        resp.raise_for_status()


def unshare(folder_id: str, device_id: str) -> None:
    with _client() as c:
        r = c.get(f"/rest/config/folders/{folder_id}")
        if r.status_code != 200:
            return
        folder = r.json()
        folder["devices"] = [d for d in folder.get("devices", []) if d["deviceID"] != device_id]
        c.put(f"/rest/config/folders/{folder_id}", json=folder).raise_for_status()


def folder_id_for(account_folder: str) -> str:
    return f"gpmc-{account_folder}"
