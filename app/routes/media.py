"""Thumbnails, queue management, UI uploads, QR codes, and LAN discovery."""
from __future__ import annotations

import hashlib
import io
import os
import socket
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response

from .. import config, db, security, google_auth

router = APIRouter(prefix="/api")

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass


def _safe(rel_path: str) -> str:
    rel_path = rel_path.replace("\\", "/").lstrip("/")
    full = os.path.realpath(os.path.join(config.SYNC_DIR, rel_path))
    root = os.path.realpath(config.SYNC_DIR)
    if not (full == root or full.startswith(root + os.sep)):
        raise HTTPException(status_code=400, detail="Invalid path")
    return full


@router.get("/media/thumb")
def thumb(path: str, auth=Depends(security.require)):
    full = _safe(path)
    if not os.path.isfile(full):
        raise HTTPException(status_code=404, detail="Not found")
    ext = os.path.splitext(full)[1].lower()
    if ext in config.VIDEO_EXTS:
        raise HTTPException(status_code=415, detail="No thumbnail for video")

    mtime = os.path.getmtime(full)
    key = hashlib.md5(f"{full}:{mtime}".encode()).hexdigest()
    cached = os.path.join(config.THUMB_CACHE, f"{key}.jpg")
    if os.path.isfile(cached):
        return FileResponse(cached, media_type="image/jpeg")

    try:
        from PIL import Image, ImageOps
        with Image.open(full) as im:
            im = ImageOps.exif_transpose(im)
            im.thumbnail((320, 320))
            im = im.convert("RGB")
            im.save(cached, "JPEG", quality=78)
        return FileResponse(cached, media_type="image/jpeg")
    except Exception:
        raise HTTPException(status_code=415, detail="Cannot render thumbnail")


@router.get("/accounts/{account_id}/queue")
def queue(account_id: int, auth=Depends(security.require)):
    from ..gpmc_runner import scan_media
    acc = db.get_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    folder = os.path.join(config.SYNC_DIR, acc["folder"])
    files, excluded = scan_media(folder, bool(acc.get("recursive", 1)))
    items = []
    for f in files:
        rel = os.path.relpath(f, config.SYNC_DIR).replace("\\", "/")
        ext = os.path.splitext(f)[1].lower()
        try:
            size = os.path.getsize(f)
        except OSError:
            size = 0
        items.append({
            "path": rel, "name": os.path.basename(f),
            "is_video": ext in config.VIDEO_EXTS,
            "ext": ext.lstrip(".").upper(), "size": size,
        })
    return {"count": len(items), "excluded": excluded, "items": items}


@router.post("/accounts/{account_id}/upload")
async def upload_to_folder(account_id: int, files: List[UploadFile] = File(...),
                           auth=Depends(security.require)):
    acc = db.get_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    folder = os.path.join(config.SYNC_DIR, acc["folder"])
    os.makedirs(folder, exist_ok=True)
    saved = 0
    for f in files:
        name = os.path.basename(f.filename or "")
        if not name:
            continue
        dest = os.path.join(folder, name)
        with open(dest, "wb") as out:
            while chunk := await f.read(1024 * 1024):
                out.write(chunk)
        saved += 1
    db.add_history(account_id, f"{saved} file(s) added via web UI", "info")
    return {"status": "ok", "saved": saved}


@router.delete("/media")
def delete_media(path: str, auth=Depends(security.require)):
    full = _safe(path)
    if os.path.isfile(full):
        os.remove(full)
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Not found")


@router.get("/qr")
def qr(data: str, auth=Depends(security.require)):
    try:
        import qrcode
        img = qrcode.make(data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"QR generation failed: {exc}")


def _lan_ips() -> list[str]:
    ips: set[str] = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass
    return sorted(ips)


@router.get("/network")
def network(request: Request, auth=Depends(security.require)):
    ips = _lan_ips()
    urls = [f"http://{ip}:{config.PORT}" for ip in ips]
    return {
        "port": config.PORT,
        "urls": urls,
        "primary": urls[0] if urls else f"http://localhost:{config.PORT}",
        "embedded_setup_url": google_auth.EMBEDDED_SETUP_URL,
    }
