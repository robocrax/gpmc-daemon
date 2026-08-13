import os
import io
import time
import sqlite3
import threading
import subprocess
import urllib.parse
from datetime import datetime
from collections import deque
from typing import Optional, List, Dict
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import bcrypt
import httpx
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

app = FastAPI(title="GPMC Controller")

DB_PATH = "/config/gpmc.db"
SESSION_TOKEN = os.urandom(16).hex()
DB_CORRUPT = False
DB_ERROR_MSG = ""

# In-Memory Ephemeral Log Buffer (Profile ID -> deque of log entries, max 200)
IN_MEMORY_LOGS: Dict[int, deque] = {}

def check_db_file_exists():
    global DB_CORRUPT, DB_ERROR_MSG
    if not os.path.exists(DB_PATH):
        DB_CORRUPT = True
        DB_ERROR_MSG = "Database file /config/gpmc.db was deleted or removed from disk."

def init_db():
    global DB_CORRUPT, DB_ERROR_MSG
    os.makedirs("/config", exist_ok=True)
    os.makedirs("/sync", exist_ok=True)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA integrity_check")
        check = cursor.fetchone()
        if check and check[0] != "ok":
            raise sqlite3.DatabaseError(f"Integrity check failed: {check[0]}")

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            folder_name TEXT UNIQUE,
            auth_data TEXT,
            heartbeat TEXT,
            purge BOOLEAN DEFAULT 1,
            saver BOOLEAN DEFAULT 0,
            threads INTEGER DEFAULT 3,
            max_retries INTEGER DEFAULT 3,
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Idle',
            progress INTEGER DEFAULT 0,
            file_count INTEGER DEFAULT 0,
            exclude_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            last_log TEXT DEFAULT '',
            last_success TEXT DEFAULT '',
            last_error TEXT DEFAULT '',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)
        
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('sync_interval_min', '5')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('webhook_url', '')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('ui_console_show', 'false')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('obfuscate_auth', 'true')")
        
        conn.commit()
        conn.close()
        DB_CORRUPT = False
        DB_ERROR_MSG = ""
    except Exception as e:
        DB_CORRUPT = True
        DB_ERROR_MSG = str(e)

init_db()

@app.middleware("http")
async def check_db_health(request: Request, call_next):
    check_db_file_exists()
    if DB_CORRUPT and request.url.path.startswith("/api/") and request.url.path not in ["/api/db/reset", "/api/db/status"]:
        return JSONResponse(status_code=503, content={"detail": "Database corrupt", "error": DB_ERROR_MSG})
    return await call_next(request)

@app.get("/api/db/status")
def db_status():
    check_db_file_exists()
    return {"corrupt": DB_CORRUPT, "error": DB_ERROR_MSG}

@app.post("/api/db/reset")
def reset_db():
    global DB_CORRUPT, DB_ERROR_MSG
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        return {"status": "ok", "message": "Database reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset DB: {e}")

# --- Models ---
class ProfileCreate(BaseModel):
    folder_name: str
    auth_data: str
    heartbeat: Optional[str] = ""
    purge: bool = True
    saver: bool = False
    threads: int = 3
    max_retries: int = 3

class ProfileUpdate(BaseModel):
    folder_name: str
    auth_data: Optional[str] = ""
    heartbeat: Optional[str] = ""
    purge: bool = True
    saver: bool = False
    threads: int = 3
    max_retries: int = 3

class SettingsUpdate(BaseModel):
    sync_interval_min: int
    webhook_url: Optional[str] = ""
    ui_console_show: bool = False
    obfuscate_auth: bool = True
    password: Optional[str] = ""

class LoginRequest(BaseModel):
    password: str

# --- Helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_setting(key, default=""):
    try:
        conn = get_db()
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        conn.close()
        return row["value"] if row else default
    except Exception:
        return default

def set_setting(key, value):
    try:
        conn = get_db()
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
        conn.commit()
        conn.close()
    except Exception:
        pass

def extract_email(auth_data: str) -> str:
    try:
        parsed = urllib.parse.parse_qs(auth_data)
        if "Email" in parsed and parsed["Email"]:
            return urllib.parse.unquote(parsed["Email"][0])
    except Exception:
        pass
    return "Google Account"

def add_log(profile_id: int, message: str):
    # Store in ephemeral memory buffer
    if profile_id not in IN_MEMORY_LOGS:
        IN_MEMORY_LOGS[profile_id] = deque(maxlen=200)
    
    entry = {
        "id": len(IN_MEMORY_LOGS[profile_id]) + 1,
        "profile_id": profile_id,
        "message": message,
        "created_at": datetime.now().isoformat()
    }
    IN_MEMORY_LOGS[profile_id].appendleft(entry)

    # Update lightweight status string in SQLite
    try:
        conn = get_db()
        conn.execute("UPDATE profiles SET last_log = ? WHERE id = ?", (message, profile_id))
        conn.commit()
        conn.close()
    except Exception:
        pass

def send_webhook(email: str, message: str):
    webhook_url = get_setting("webhook_url")
    if not webhook_url:
        return
    try:
        payload = {"text": f"📸 **GPMC Controller [{email}]**: {message}"}
        httpx.post(webhook_url, json=payload, timeout=10.0)
    except Exception:
        pass

def verify_auth(request: Request):
    has_password = get_setting("ui_password_hash") != ""
    if not has_password:
        return True
    token = request.cookies.get("gpmc_session")
    if token == SESSION_TOKEN and SESSION_TOKEN != "":
        return True
    raise HTTPException(status_code=401, detail="Unauthorized")

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".gif", ".bmp", ".tiff",
    ".mp4", ".m4v", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".3gp", ".webm"
}
VIDEO_EXTENSIONS = {".mp4", ".m4v", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".3gp", ".webm"}

def scan_media_files(folder_path: str):
    valid_files = []
    excluded_count = 0
    if not os.path.exists(folder_path):
        return valid_files, excluded_count
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.startswith("."):
                continue
            ext = os.path.splitext(file)[1].lower()
            full_path = os.path.join(root, file)
            if ext in ALLOWED_EXTENSIONS:
                valid_files.append(full_path)
            else:
                excluded_count += 1
    return valid_files, excluded_count

def process_profile(profile_id: int):
    if DB_CORRUPT:
        return

    try:
        conn = get_db()
        p = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        conn.close()
    except Exception:
        return

    if not p:
        return

    target_dir = f"/sync/{p['folder_name']}"
    os.makedirs(target_dir, exist_ok=True)

    valid_files, excluded_count = scan_media_files(target_dir)
    total_files = len(valid_files)

    if total_files == 0:
        try:
            conn = get_db()
            conn.execute("UPDATE profiles SET status = 'Synced', progress = 0, file_count = 0, exclude_count = ?, failed_count = 0 WHERE id = ?", (excluded_count, profile_id))
            conn.commit()
            conn.close()
        except Exception:
            pass
        return

    add_log(profile_id, f"Starting upload cycle for {total_files} files (Threads: {p['threads']})")

    successful_uploads = 0
    failed_count = 0

    for idx, file_path in enumerate(valid_files):
        file_num = idx + 1
        progress_pct = int((file_num / total_files) * 100)
        file_name = os.path.basename(file_path)

        try:
            conn = get_db()
            conn.execute("UPDATE profiles SET status = 'Uploading', progress = ?, file_count = ?, exclude_count = ?, failed_count = ? WHERE id = ?", 
                         (progress_pct, total_files, excluded_count, failed_count, profile_id))
            conn.commit()
            conn.close()
        except Exception:
            pass

        cmd = [
            "gpmc",
            file_path,
            "--auth_data", p["auth_data"],
            "--album", "AUTO",
            "--threads", str(p["threads"])
        ]
        if p["saver"]:
            cmd.append("--saver")
        if p["purge"]:
            cmd.append("--delete-from-host")

        file_success = False
        for attempt in range(1, p["max_retries"] + 1):
            add_log(profile_id, f"Executing GPMC (Attempt {attempt}/{p['max_retries']}) for [{file_name}]")
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if res.returncode == 0:
                    add_log(profile_id, f"Successfully uploaded [{file_name}]\n{res.stdout}")
                    file_success = True
                    break
                else:
                    add_log(profile_id, f"Attempt {attempt} failed [{file_name}]: {res.stderr or res.stdout}")
            except Exception as e:
                add_log(profile_id, f"Attempt {attempt} exception [{file_name}]: {e}")
            
            if attempt < p["max_retries"]:
                time.sleep(1)

        if file_success:
            successful_uploads += 1
        else:
            failed_count += 1
            try:
                conn = get_db()
                conn.execute("UPDATE profiles SET failed_count = ? WHERE id = ?", (failed_count, profile_id))
                conn.commit()
                conn.close()
            except Exception:
                pass

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = get_db()
        if successful_uploads > 0:
            if failed_count > 0:
                conn.execute("UPDATE profiles SET status = 'Failed', progress = 0, file_count = ?, exclude_count = ?, failed_count = ?, last_error = ? WHERE id = ?",
                             (total_files - successful_uploads, excluded_count, failed_count, f"{failed_count} files failed", profile_id))
            else:
                conn.execute("UPDATE profiles SET status = 'Synced', progress = 100, file_count = 0, exclude_count = ?, failed_count = 0, last_success = ? WHERE id = ?",
                             (excluded_count, now, profile_id))
            conn.commit()
            conn.close()
            
            msg = f"Upload cycle completed: {successful_uploads}/{total_files} files successfully uploaded."
            add_log(profile_id, msg)
            send_webhook(p["email"], msg)

            if p["heartbeat"]:
                try:
                    httpx.get(p["heartbeat"], timeout=10.0)
                except Exception:
                    pass
        else:
            conn.execute("UPDATE profiles SET status = 'Failed', progress = 0, file_count = ?, exclude_count = ?, failed_count = ?, last_error = 'All uploads failed' WHERE id = ?",
                         (total_files, excluded_count, failed_count, profile_id))
            conn.commit()
            conn.close()
            msg = f"Upload cycle failed: 0/{total_files} files uploaded."
            add_log(profile_id, msg)
            send_webhook(p["email"], "❌ " + msg)
    except Exception:
        pass

def background_scheduler():
    while True:
        if not DB_CORRUPT:
            try:
                interval_min = int(get_setting("sync_interval_min", "5"))
            except ValueError:
                interval_min = 5

            try:
                conn = get_db()
                profiles = conn.execute("SELECT id FROM profiles").fetchall()
                conn.close()

                threads = []
                for prof in profiles:
                    t = threading.Thread(target=process_profile, args=(prof["id"],))
                    t.start()
                    threads.append(t)

                for t in threads:
                    t.join()
            except Exception:
                pass

            time.sleep(interval_min * 60)
        else:
            time.sleep(5)

def folder_watcher():
    while True:
        if not DB_CORRUPT:
            try:
                conn = get_db()
                profiles = conn.execute("SELECT * FROM profiles").fetchall()
                conn.close()

                for p in profiles:
                    if not p["status"].startswith("Processing") and p["status"] != "Uploading":
                        target_dir = f"/sync/{p['folder_name']}"
                        valid_files, excluded_count = scan_media_files(target_dir)
                        count = len(valid_files)
                        
                        conn = get_db()
                        if count == 0 and p["status"] != "Failed":
                            conn.execute("UPDATE profiles SET file_count = 0, exclude_count = ?, status = 'Synced' WHERE id = ?", (excluded_count, p["id"]))
                        elif count > 0 and p["status"] == "Synced":
                            conn.execute("UPDATE profiles SET file_count = ?, exclude_count = ?, status = 'Ready' WHERE id = ?", (count, excluded_count, p["id"]))
                        else:
                            conn.execute("UPDATE profiles SET file_count = ?, exclude_count = ? WHERE id = ?", (count, excluded_count, p["id"]))
                        conn.commit()
                        conn.close()
            except Exception:
                pass
        time.sleep(3)

threading.Thread(target=background_scheduler, daemon=True).start()
threading.Thread(target=folder_watcher, daemon=True).start()

# --- API Endpoints ---
@app.get("/api/auth/status")
def auth_status(request: Request):
    has_password = get_setting("ui_password_hash") != ""
    authenticated = not has_password
    if has_password:
        token = request.cookies.get("gpmc_session")
        if token == SESSION_TOKEN and SESSION_TOKEN != "":
            authenticated = True
    return {"has_password": has_password, "authenticated": authenticated}

@app.post("/api/auth/login")
def login(payload: LoginRequest, response: Response):
    stored_hash = get_setting("ui_password_hash")
    if stored_hash and bcrypt.checkpw(payload.password.encode(), stored_hash.encode()):
        response.set_cookie(key="gpmc_session", value=SESSION_TOKEN, httponly=True, samesite="strict")
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail="Invalid password")

@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(key="gpmc_session")
    return {"status": "ok"}

@app.get("/api/settings")
def get_settings(auth=Depends(verify_auth)):
    return {
        "sync_interval_min": int(get_setting("sync_interval_min", "5")),
        "webhook_url": get_setting("webhook_url", ""),
        "ui_console_show": get_setting("ui_console_show", "false") == "true",
        "obfuscate_auth": get_setting("obfuscate_auth", "true") == "true",
        "has_password": get_setting("ui_password_hash") != ""
    }

@app.post("/api/settings")
def save_settings(payload: SettingsUpdate, auth=Depends(verify_auth)):
    set_setting("sync_interval_min", payload.sync_interval_min)
    set_setting("webhook_url", payload.webhook_url or "")
    set_setting("ui_console_show", str(payload.ui_console_show).lower())
    set_setting("obfuscate_auth", str(payload.obfuscate_auth).lower())
    if payload.password:
        hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
        set_setting("ui_password_hash", hashed)
    return {"status": "ok"}

@app.get("/api/profiles")
def get_profiles(auth=Depends(verify_auth)):
    conn = get_db()
    rows = conn.execute("SELECT * FROM profiles ORDER BY priority ASC, id ASC").fetchall()
    conn.close()
    
    profiles = []
    for r in rows:
        p = dict(r)
        folder = f"/sync/{p['folder_name']}"
        valid_files, _ = scan_media_files(folder)
        
        queue = []
        for f in valid_files:
            rel_path = os.path.relpath(f, "/sync")
            ext = os.path.splitext(f)[1].lower()
            queue.append({
                "id": rel_path,
                "url": f"/api/media/{rel_path}",
                "is_video": ext in VIDEO_EXTENSIONS,
                "ext": ext.replace(".", "").upper(),
                "name": os.path.basename(f)
            })
        p["media_queue"] = queue
        profiles.append(p)
    return profiles

@app.get("/api/media/{path:path}")
def serve_media(path: str, auth=Depends(verify_auth)):
    full_path = os.path.join("/sync", path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Media not found")

    ext = os.path.splitext(full_path)[1].lower()
    
    if ext in [".heic", ".heif"]:
        try:
            im = Image.open(full_path)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=75)
            buf.seek(0)
            return Response(content=buf.getvalue(), media_type="image/jpeg")
        except Exception:
            try:
                res = subprocess.run(["convert", full_path, "jpg:-"], capture_output=True, timeout=5)
                if res.returncode == 0 and res.stdout:
                    return Response(content=res.stdout, media_type="image/jpeg")
            except Exception:
                pass

    return FileResponse(full_path)

@app.post("/api/profiles")
def create_profile(payload: ProfileCreate, auth=Depends(verify_auth)):
    email = extract_email(payload.auth_data)
    folder_name = "".join(c for c in payload.folder_name if c.isalnum() or c in ('_', '-'))
    if not folder_name:
        raise HTTPException(status_code=400, detail="Invalid folder name")

    os.makedirs(f"/sync/{folder_name}", exist_ok=True)
    
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO profiles (email, folder_name, auth_data, heartbeat, purge, saver, threads, max_retries) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (email, folder_name, payload.auth_data, payload.heartbeat, payload.purge, payload.saver, payload.threads, payload.max_retries)
        )
        conn.commit()
        profile_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Folder name already exists")
    finally:
        conn.close()

    return {"id": profile_id, "folder_name": folder_name}

@app.put("/api/profiles/{profile_id}")
def update_profile(profile_id: int, payload: ProfileUpdate, auth=Depends(verify_auth)):
    conn = get_db()
    existing = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Profile not found")

    auth_data = payload.auth_data
    if not auth_data or auth_data.strip() == "":
        auth_data = existing["auth_data"]

    email = extract_email(auth_data)
    folder_name = "".join(c for c in payload.folder_name if c.isalnum() or c in ('_', '-'))

    conn.execute(
        "UPDATE profiles SET email = ?, folder_name = ?, auth_data = ?, heartbeat = ?, purge = ?, saver = ?, threads = ?, max_retries = ? WHERE id = ?",
        (email, folder_name, auth_data, payload.heartbeat, payload.purge, payload.saver, payload.threads, payload.max_retries, profile_id)
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/profiles/{profile_id}/sync")
def sync_now(profile_id: int, auth=Depends(verify_auth)):
    threading.Thread(target=process_profile, args=(profile_id,)).start()
    return {"status": "ok"}

@app.get("/api/profiles/{profile_id}/logs")
def get_logs(profile_id: int, auth=Depends(verify_auth)):
    logs = list(IN_MEMORY_LOGS.get(profile_id, []))
    return logs

@app.put("/api/profiles/reorder")
def reorder_profiles(order: List[int], auth=Depends(verify_auth)):
    conn = get_db()
    for index, pid in enumerate(order):
        conn.execute("UPDATE profiles SET priority = ? WHERE id = ?", (index, pid))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: int, delete_folder: bool = False, auth=Depends(verify_auth)):
    conn = get_db()
    p = conn.execute("SELECT folder_name FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    if p and delete_folder:
        folder_path = f"/sync/{p['folder_name']}"
        if os.path.exists(folder_path):
            import shutil
            shutil.rmtree(folder_path, ignore_errors=True)
            
    if profile_id in IN_MEMORY_LOGS:
        del IN_MEMORY_LOGS[profile_id]

    conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

app.mount("/", StaticFiles(directory="web/static", html=True), name="static")