"""Background daemon: watches folders and runs upload cycles on a schedule."""
from __future__ import annotations

import os
import threading
import time

from . import config, db, runtime
from .gpmc_runner import is_busy, run_cycle, scan_media

_started = False


def trigger(account_id: int) -> bool:
    """Kick off an immediate cycle for one account. Returns False if already running."""
    if is_busy(account_id):
        return False
    runtime.set_next_run(account_id, time.time() + _interval_seconds())
    threading.Thread(target=run_cycle, args=(account_id,), daemon=True).start()
    return True


def _interval_seconds() -> int:
    try:
        return max(1, int(db.get_setting("sync_interval_min", "5"))) * 60
    except ValueError:
        return 300


def _watch_loop() -> None:
    while True:
        try:
            for acc in db.list_accounts():
                aid = acc["id"]
                if is_busy(aid):
                    continue
                folder = os.path.join(config.SYNC_DIR, acc["folder"])
                files, excluded = scan_media(folder, bool(acc.get("recursive", 1)))
                runtime.update(aid, queue_count=len(files), excluded=excluded)
                st = runtime.rt(aid)["status"]
                if not acc.get("enabled", 1):
                    runtime.update(aid, status="disabled")
                elif st in ("idle", "synced", "pending", "disabled", "scanning"):
                    runtime.update(aid, status="pending" if files else "synced")
        except Exception:
            pass
        time.sleep(config.WATCH_INTERVAL_SEC)


def _schedule_loop() -> None:
    # Give the folder watcher a beat to populate, then run a first pass soon after boot.
    boot_grace = time.time() + 15
    while True:
        try:
            interval = _interval_seconds()
            now = time.time()
            for acc in db.list_accounts():
                aid = acc["id"]
                if not acc.get("enabled", 1):
                    continue
                nr = runtime.NEXT_RUN.get(aid)
                if nr is None:
                    runtime.set_next_run(aid, max(now + 5, boot_grace))
                    continue
                if now >= nr and not is_busy(aid):
                    runtime.set_next_run(aid, now + interval)
                    threading.Thread(target=run_cycle, args=(aid,), daemon=True).start()
        except Exception:
            pass
        time.sleep(3)


def start() -> None:
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_watch_loop, daemon=True).start()
    threading.Thread(target=_schedule_loop, daemon=True).start()
