"""Runtime configuration.

Works in three environments with zero changes:
  * Docker        -> GPMC_CONFIG_DIR=/config, GPMC_SYNC_DIR=/sync (compose defaults)
  * bare metal    -> install.sh exports GPMC_* to /var/lib/gpmc-daemon/...
  * local dev     -> falls back to ./data/* when the configured dirs aren't writable
"""
from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "GPMC Daemon"
VERSION = "2.0.0"


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _resolve_dir(env_name: str, default_abs: str, fallback_rel: str) -> Path:
    """Return a writable directory, falling back to a repo-local path for dev."""
    candidate = Path(os.getenv(env_name, default_abs))
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        probe = candidate / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return candidate
    except Exception:
        fallback = Path.cwd() / fallback_rel
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


CONFIG_DIR = _resolve_dir("GPMC_CONFIG_DIR", "/config", "data/config")
SYNC_DIR = _resolve_dir("GPMC_SYNC_DIR", "/sync", "data/sync")

# gpmc keeps its per-account dedup cache under $HOME/.gpmc/<email>. Pin HOME so the
# cache is persistent across restarts (survives container/service recreation).
GPMC_HOME = _resolve_dir("GPMC_HOME", str(CONFIG_DIR / "gpmc_home"), "data/config/gpmc_home")
os.environ["HOME"] = str(GPMC_HOME)

DB_PATH = CONFIG_DIR / "gpmc.db"
THUMB_CACHE = _resolve_dir("GPMC_THUMB_CACHE", str(CONFIG_DIR / "thumbs"), "data/config/thumbs")

PORT = int(os.getenv("PORT", "8080"))
HOST = os.getenv("HOST", "0.0.0.0")

# Default cadence for the upload daemon. The folder watcher runs far more often so the
# queue preview feels live.
DEFAULT_SYNC_INTERVAL_MIN = int(os.getenv("SYNC_INTERVAL_MINUTES", "5"))
WATCH_INTERVAL_SEC = int(os.getenv("GPMC_WATCH_INTERVAL_SEC", "4"))

# Optional outbound proxy for both the login exchange and uploads.
HTTP_PROXY = os.getenv("GPMC_PROXY", "")

# Syncthing integration (optional). GPMC reads the API key from Syncthing's config.xml
# and drives its REST API on localhost, so phones can be managed from the GPMC UI.
SYNCTHING_URL = os.getenv("GPMC_SYNCTHING_URL", "http://127.0.0.1:8384")
SYNCTHING_CONFIG = os.getenv("GPMC_SYNCTHING_CONFIG", str(CONFIG_DIR.parent / "syncthing" / "config.xml"))
# Public base URL for the Syncthing GUI shown to the user (LAN by default).
SYNCTHING_GUI_URL = os.getenv("GPMC_SYNCTHING_GUI_URL", "")

# Lets the UI reveal a stored auth_data string (off by default; it's a long-lived token).
ALLOW_REVEAL_AUTH = _bool("ALLOW_REVEAL_AUTH", False)

# Optional bootstrap password for the UI (hashed into the DB on first boot).
INITIAL_UI_PASSWORD = os.getenv("UI_PASSWORD", "")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".gif", ".bmp", ".tif", ".tiff", ".dng"}
VIDEO_EXTS = {".mp4", ".m4v", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".3gp", ".3gpp", ".webm", ".mts", ".m2ts"}
MEDIA_EXTS = IMAGE_EXTS | VIDEO_EXTS
