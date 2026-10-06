"""Scans account folders and uploads media to Google Photos via gpmc."""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime

import httpx

from . import config, db, runtime

_RUNNING: set[int] = set()
_RUNNING_LOCK = threading.Lock()

# Files Syncthing (and friends) create mid-transfer; never upload a partial file.
_SKIP_PREFIXES = (".syncthing.", "~syncthing~", ".")
_SKIP_SUFFIXES = (".tmp", ".part", ".partial", ".crdownload", ".!sync")
_SKIP_DIRS = {".stfolder", ".stversions", "@eaDir", ".thumbnails"}


def scan_media(folder: str, recursive: bool = True) -> tuple[list[str], int]:
    files: list[str] = []
    excluded = 0
    if not os.path.isdir(folder):
        return files, excluded
    for root, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for name in names:
            lower = name.lower()
            if name.startswith(_SKIP_PREFIXES) or lower.endswith(_SKIP_SUFFIXES):
                continue
            ext = os.path.splitext(name)[1].lower()
            full = os.path.join(root, name)
            if ext in config.MEDIA_EXTS:
                files.append(full)
            else:
                excluded += 1
        if not recursive:
            break
    files.sort()
    return files, excluded


def is_busy(account_id: int) -> bool:
    with _RUNNING_LOCK:
        return account_id in _RUNNING


def _album_name(acc: dict) -> str | None:
    mode = acc.get("album_mode", "auto")
    if mode == "auto":
        return "AUTO"
    if mode == "custom":
        return (acc.get("album_name") or "").strip() or None
    return None


def _notify(message: str, level: str = "info") -> None:
    url = db.get_setting("webhook_url", "").strip()
    if not url:
        return
    try:
        emoji = {"info": "📸", "success": "✅", "error": "❌"}.get(level, "📸")
        httpx.post(url, json={"text": f"{emoji} GPMC Daemon: {message}",
                              "content": f"{emoji} GPMC Daemon: {message}"}, timeout=10)
    except Exception:
        pass


def _heartbeat(acc: dict) -> None:
    url = (acc.get("heartbeat_url") or "").strip()
    if not url:
        return
    try:
        httpx.get(url, timeout=10)
    except Exception:
        pass


def run_cycle(account_id: int) -> None:
    with _RUNNING_LOCK:
        if account_id in _RUNNING:
            return
        _RUNNING.add(account_id)
    try:
        _run_cycle_inner(account_id)
    finally:
        with _RUNNING_LOCK:
            _RUNNING.discard(account_id)


def _run_cycle_inner(account_id: int) -> None:
    acc = db.get_account(account_id)
    if not acc:
        return
    if not acc.get("enabled", 1):
        runtime.update(account_id, status="paused")
        return

    folder = os.path.join(config.SYNC_DIR, acc["folder"])
    os.makedirs(folder, exist_ok=True)
    recursive = bool(acc.get("recursive", 1))

    runtime.update(account_id, status="scanning")
    files, excluded = scan_media(folder, recursive)
    runtime.update(account_id, queue_count=len(files), excluded=excluded)

    if not files:
        runtime.update(account_id, status="synced", phase="", current_file="")
        return

    runtime.reset_cycle(account_id, len(files))
    runtime.update(account_id, status="uploading")
    runtime.log(account_id, f"Starting cycle: {len(files)} file(s), {acc['threads']} thread(s)")

    counters = {"uploaded": 0, "skipped": 0, "failed": 0, "done": 0}
    clock = threading.Lock()

    def on_progress(event: dict) -> None:
        phase = event.get("phase", "")
        fname = event.get("filename", "")
        with clock:
            runtime.update(
                account_id,
                phase=phase,
                current_file=fname,
                file_bytes_done=event.get("bytes_completed", 0),
                file_bytes_total=event.get("bytes_total", 0),
            )
            if phase in ("complete", "skipped", "error"):
                counters["done"] += 1
                if phase == "complete":
                    counters["uploaded"] += 1
                elif phase == "skipped":
                    counters["skipped"] += 1
                else:
                    counters["failed"] += 1
                    runtime.log(account_id, f"Failed: {fname}", "error")
                runtime.update(
                    account_id,
                    done=counters["done"],
                    uploaded=counters["uploaded"],
                    skipped=counters["skipped"],
                    failed=counters["failed"],
                )

    attempts = int(acc.get("max_retries", 3))
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            from gpmc import Client
            client = Client(
                auth_data=acc["auth_data"],
                proxy=config.HTTP_PROXY,
                timeout=120,
                log_level="WARNING",
            )
            client.upload(
                target=folder,
                album_name=_album_name(acc),
                saver=bool(acc.get("saver", 0)),
                use_quota=bool(acc.get("use_quota", 0)),
                recursive=recursive,
                threads=int(acc.get("threads", 3)),
                delete_from_host=bool(acc.get("delete_after", 1)),
                skip_existing_filenames=bool(acc.get("skip_existing_filenames", 0)),
                show_progress=False,
                progress_callback=on_progress,
            )
            last_exc = None
            break
        except Exception as exc:  # network / auth / transient
            last_exc = exc
            runtime.log(account_id, f"Attempt {attempt}/{attempts} error: {exc}", "error")
            if attempt < attempts:
                time.sleep(min(5 * attempt, 30))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    remaining, _ = scan_media(folder, recursive)

    if last_exc is not None:
        runtime.update(account_id, status="error", last_error=str(last_exc),
                       queue_count=len(remaining))
        db.add_history(account_id, f"Cycle failed: {last_exc}", "error")
        _notify(f"[{acc['email']}] cycle failed: {last_exc}", "error")
        return

    up, sk, fa = counters["uploaded"], counters["skipped"], counters["failed"]
    summary = f"Uploaded {up}, skipped {sk}, failed {fa}"
    runtime.update(
        account_id,
        status="error" if fa and not up else "synced",
        phase="", current_file="",
        last_success=now if up or sk else runtime.rt(account_id)["last_success"],
        last_error=f"{fa} file(s) failed" if fa else "",
        queue_count=len(remaining),
    )
    runtime.log(account_id, summary, "error" if fa else "success")
    db.add_history(account_id, summary, "error" if fa else "success")
    if up or fa:
        _notify(f"[{acc['email']}] {summary}", "error" if fa and not up else "success")
    if up and not fa:
        _heartbeat(acc)
