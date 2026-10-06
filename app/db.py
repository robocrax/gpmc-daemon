"""SQLite persistence layer (thread-safe, WAL)."""
from __future__ import annotations

import sqlite3
import threading
import time
from typing import Any, Optional

from . import config

_LOCK = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    email                    TEXT    NOT NULL,
    label                    TEXT    DEFAULT '',
    folder                   TEXT    UNIQUE NOT NULL,
    auth_data                TEXT    NOT NULL,
    android_id               TEXT    DEFAULT '',
    album_mode               TEXT    DEFAULT 'auto',
    album_name               TEXT    DEFAULT '',
    delete_after             INTEGER DEFAULT 1,
    saver                    INTEGER DEFAULT 0,
    use_quota                INTEGER DEFAULT 0,
    recursive                INTEGER DEFAULT 1,
    skip_existing_filenames  INTEGER DEFAULT 0,
    threads                  INTEGER DEFAULT 3,
    max_retries              INTEGER DEFAULT 3,
    enabled                  INTEGER DEFAULT 1,
    heartbeat_url            TEXT    DEFAULT '',
    priority                 INTEGER DEFAULT 0,
    created_at               TEXT    DEFAULT (datetime('now')),
    updated_at               TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    ts         TEXT DEFAULT (datetime('now')),
    level      TEXT DEFAULT 'info',
    message    TEXT
);
CREATE INDEX IF NOT EXISTS idx_history_account ON history(account_id, id DESC);
"""

DEFAULT_SETTINGS = {
    "sync_interval_min": str(config.DEFAULT_SYNC_INTERVAL_MIN),
    "webhook_url": "",
    "allow_reveal_auth": "false",
    "theme": "system",
    "setup_done": "false",
    "ui_password_hash": "",
}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init() -> None:
    with _LOCK:
        conn = connect()
        try:
            conn.executescript(SCHEMA)
            for key, value in DEFAULT_SETTINGS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (key, value)
                )
            conn.commit()
        finally:
            conn.close()


# --- settings -------------------------------------------------------------
def get_setting(key: str, default: str = "") -> str:
    conn = connect()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default
    finally:
        conn.close()


def set_setting(key: str, value: Any) -> None:
    with _LOCK:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value)),
            )
            conn.commit()
        finally:
            conn.close()


# --- accounts -------------------------------------------------------------
ACCOUNT_FIELDS = (
    "label", "album_mode", "album_name", "delete_after", "saver", "use_quota",
    "recursive", "skip_existing_filenames", "threads", "max_retries", "enabled",
    "heartbeat_url",
)


def list_accounts() -> list[dict]:
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM accounts ORDER BY priority ASC, id ASC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_account(account_id: int) -> Optional[dict]:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_account_by_email(email: str) -> Optional[dict]:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT * FROM accounts WHERE lower(email)=lower(?)", (email,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_account(email: str, folder: str, auth_data: str, android_id: str, label: str = "") -> int:
    with _LOCK:
        conn = connect()
        try:
            cur = conn.execute(
                "INSERT INTO accounts(email, folder, auth_data, android_id, label) "
                "VALUES (?, ?, ?, ?, ?)",
                (email, folder, auth_data, android_id, label or email),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()


def update_auth(account_id: int, auth_data: str, android_id: str, email: str) -> None:
    with _LOCK:
        conn = connect()
        try:
            conn.execute(
                "UPDATE accounts SET auth_data=?, android_id=?, email=?, "
                "updated_at=datetime('now') WHERE id=?",
                (auth_data, android_id, email, account_id),
            )
            conn.commit()
        finally:
            conn.close()


def update_account(account_id: int, values: dict) -> None:
    fields = [f for f in ACCOUNT_FIELDS if f in values]
    if not fields:
        return
    assignments = ", ".join(f"{f}=?" for f in fields)
    params = []
    for f in fields:
        v = values[f]
        params.append(int(v) if isinstance(v, bool) else v)
    params.append(account_id)
    with _LOCK:
        conn = connect()
        try:
            conn.execute(
                f"UPDATE accounts SET {assignments}, updated_at=datetime('now') WHERE id=?",
                params,
            )
            conn.commit()
        finally:
            conn.close()


def set_priority(order: list[int]) -> None:
    with _LOCK:
        conn = connect()
        try:
            for idx, aid in enumerate(order):
                conn.execute("UPDATE accounts SET priority=? WHERE id=?", (idx, aid))
            conn.commit()
        finally:
            conn.close()


def delete_account(account_id: int) -> None:
    with _LOCK:
        conn = connect()
        try:
            conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
            conn.execute("DELETE FROM history WHERE account_id=?", (account_id,))
            conn.commit()
        finally:
            conn.close()


# --- history --------------------------------------------------------------
def add_history(account_id: Optional[int], message: str, level: str = "info") -> None:
    with _LOCK:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO history(account_id, level, message) VALUES (?, ?, ?)",
                (account_id, level, message),
            )
            # keep the table bounded
            conn.execute(
                "DELETE FROM history WHERE id NOT IN "
                "(SELECT id FROM history ORDER BY id DESC LIMIT 2000)"
            )
            conn.commit()
        finally:
            conn.close()


def list_history(account_id: Optional[int] = None, limit: int = 200) -> list[dict]:
    conn = connect()
    try:
        if account_id is None:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM history WHERE account_id=? ORDER BY id DESC LIMIT ?",
                (account_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
