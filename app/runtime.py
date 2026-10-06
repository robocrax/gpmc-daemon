"""In-memory runtime state for each account (progress, live logs, schedule)."""
from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime
from typing import Optional

_LOCK = threading.RLock()
_STATE: dict[int, dict] = {}

# When each account is next due for an upload cycle (epoch seconds).
NEXT_RUN: dict[int, float] = {}


def _blank() -> dict:
    return {
        "status": "idle",          # idle|scanning|uploading|synced|error|paused|disabled
        "phase": "",
        "current_file": "",
        "done": 0,
        "total": 0,
        "uploaded": 0,
        "skipped": 0,
        "failed": 0,
        "queue_count": 0,
        "excluded": 0,
        "file_bytes_done": 0,
        "file_bytes_total": 0,
        "cycle_started": 0.0,
        "last_success": "",
        "last_error": "",
        "logs": deque(maxlen=250),
    }


def rt(account_id: int) -> dict:
    with _LOCK:
        if account_id not in _STATE:
            _STATE[account_id] = _blank()
        return _STATE[account_id]


def update(account_id: int, **fields) -> None:
    with _LOCK:
        st = rt(account_id)
        st.update(fields)


def log(account_id: int, message: str, level: str = "info") -> None:
    with _LOCK:
        st = rt(account_id)
        st["logs"].appendleft({
            "ts": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message,
        })


def snapshot(account_id: int) -> dict:
    with _LOCK:
        st = rt(account_id)
        out = {k: v for k, v in st.items() if k != "logs"}
        out["logs"] = list(st["logs"])[:40]
        out["next_run"] = NEXT_RUN.get(account_id, 0)
        return out


def logs(account_id: int, limit: int = 250) -> list[dict]:
    with _LOCK:
        return list(rt(account_id)["logs"])[:limit]


def reset_cycle(account_id: int, total: int) -> None:
    with _LOCK:
        st = rt(account_id)
        st.update({
            "done": 0, "total": total, "uploaded": 0, "skipped": 0, "failed": 0,
            "current_file": "", "phase": "", "file_bytes_done": 0, "file_bytes_total": 0,
            "cycle_started": time.time(),
        })


def forget(account_id: int) -> None:
    with _LOCK:
        _STATE.pop(account_id, None)
        NEXT_RUN.pop(account_id, None)


def set_next_run(account_id: int, when: float) -> None:
    with _LOCK:
        NEXT_RUN[account_id] = when
