"""GPMC for Windows.

Runs the same GPMC web app as the Docker / Linux builds, plus a private copy of
Syncthing, on the user's own PC. A tray icon sits by the clock; the UI opens in the
default browser at http://127.0.0.1:<port> (loopback only).

    GPMC.exe               start (or, if already running, open the UI)
    GPMC.exe --background  start without opening the browser (used at sign-in)
    GPMC.exe --quit        ask a running GPMC to exit, and wait for it

Data lives in %LOCALAPPDATA%\\GPMC (override with GPMC_DATA_DIR for testing):
    config\\     accounts, settings, thumbnails
    photos\\     one folder per account: photos waiting to upload
    syncthing\\  Syncthing's config, keys and database
    logs\\       gpmc.log, syncthing.log
"""
from __future__ import annotations

import ctypes
import json
import logging
import logging.handlers
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
import xml.etree.ElementTree as ET
from ctypes import wintypes
from pathlib import Path

APP = "GPMC"
FROZEN = getattr(sys, "frozen", False)
EXE_DIR = Path(sys.executable).parent if FROZEN else Path(__file__).resolve().parent
RES_DIR = Path(getattr(sys, "_MEIPASS", EXE_DIR))
ROOT = Path(os.environ.get("GPMC_DATA_DIR") or Path(os.environ["LOCALAPPDATA"]) / APP)
STATE_FILE = ROOT / "desktop.json"

MUTEX_NAME = "Local\\GPMC.Desktop"
EV_SHOW = "Local\\GPMC.Desktop.Show"
EV_QUIT = "Local\\GPMC.Desktop.Quit"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
QUIET = bool(os.environ.get("GPMC_QUIET"))  # tests: no browser, no toasts

log = logging.getLogger("gpmc.desktop")

# ---------------------------------------------------------------- Win32 helpers
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateMutexW.restype = wintypes.HANDLE
k32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
k32.OpenMutexW.restype = wintypes.HANDLE
k32.OpenMutexW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
k32.CreateEventW.restype = wintypes.HANDLE
k32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
k32.OpenEventW.restype = wintypes.HANDLE
k32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
k32.SetEvent.argtypes = [wintypes.HANDLE]
k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
k32.WaitForSingleObject.restype = wintypes.DWORD
k32.CloseHandle.argtypes = [wintypes.HANDLE]
k32.CreateJobObjectW.restype = wintypes.HANDLE
k32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]

ERROR_ALREADY_EXISTS = 183
SYNCHRONIZE = 0x00100000
EVENT_MODIFY_STATE = 0x0002
INFINITE = 0xFFFFFFFF


def _signal(name: str) -> bool:
    h = k32.OpenEventW(EVENT_MODIFY_STATE, False, name)
    if not h:
        return False
    k32.SetEvent(h)
    k32.CloseHandle(h)
    return True


def _instance_running() -> bool:
    h = k32.OpenMutexW(SYNCHRONIZE, False, MUTEX_NAME)
    if h:
        k32.CloseHandle(h)
        return True
    return False


class _BasicLimits(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]


class _IoCounters(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in ("Read", "Write", "Other", "ReadBytes", "WriteBytes", "OtherBytes")]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [("Basic", _BasicLimits), ("Io", _IoCounters), ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]


def _kill_with_us(proc: subprocess.Popen):
    """Put a child in a job object that Windows closes when GPMC exits, even on a crash."""
    job = k32.CreateJobObjectW(None, None)
    if not job:
        return None
    info = _ExtendedLimits()
    info.Basic.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
    k32.AssignProcessToJobObject(job, int(proc._handle))
    return job  # keep a reference for the life of the process


# ---------------------------------------------------------------- setup
def _setup_logging() -> None:
    logs = ROOT / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(logs / "gpmc.log", maxBytes=2_000_000,
                                                   backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one line per request otherwise
    # A windowed build has no console: give stray prints somewhere harmless to go.
    if sys.stdout is None or sys.stderr is None:
        stream = open(logs / "console.log", "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or stream
        sys.stderr = sys.stderr or stream


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _pick_port(preferred: int) -> int:
    if preferred and _port_free(preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _configure() -> dict:
    """Choose ports and folders, and export them to the GPMC app via its env vars."""
    state = _load_state()
    state["port"] = _pick_port(int(os.environ.get("PORT") or state.get("port") or 8580))
    state["st_port"] = _pick_port(int(state.get("st_port") or 8584))
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

    st_url = f"http://127.0.0.1:{state['st_port']}"
    os.environ.update({
        "HOST": "127.0.0.1",
        "PORT": str(state["port"]),
        "GPMC_CONFIG_DIR": str(ROOT / "config"),
        "GPMC_SYNC_DIR": str(ROOT / "photos"),
        "GPMC_SYNCTHING_CONFIG": str(ROOT / "syncthing" / "config.xml"),
        "GPMC_SYNCTHING_URL": st_url,
        "GPMC_SYNCTHING_GUI_URL": st_url,
    })
    return state


# ---------------------------------------------------------------- Syncthing
def _syncthing_exe() -> Path | None:
    override = os.environ.get("GPMC_SYNCTHING_EXE")
    for p in ([Path(override)] if override else []) + [EXE_DIR / "syncthing" / "syncthing.exe"]:
        if p.is_file():
            return p
    return None


def _start_syncthing(st_port: int):
    exe = _syncthing_exe()
    if not exe:
        log.warning("syncthing.exe not found next to GPMC; Device Sync will be unavailable")
        return None, None
    home = ROOT / "syncthing"
    home.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, STNODEFAULTFOLDER="1", STNOUPGRADE="1")
    args = [str(exe), "serve", f"--home={home}", "--no-browser", "--no-restart", "--no-upgrade",
            f"--gui-address=127.0.0.1:{st_port}", f"--log-file={ROOT / 'logs' / 'syncthing.log'}"]
    proc = subprocess.Popen(args, env=env, cwd=str(home), stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    log.info("Syncthing started (pid %s) on %s", proc.pid, st_port)
    return proc, _kill_with_us(proc)


def _stop_syncthing(proc, st_port: int) -> None:
    if not proc or proc.poll() is not None:
        return
    try:
        import httpx
        key = ET.parse(ROOT / "syncthing" / "config.xml").getroot().findtext("gui/apikey")
        httpx.post(f"http://127.0.0.1:{st_port}/rest/system/shutdown", headers={"X-API-Key": key}, timeout=5)
        proc.wait(timeout=10)
    except Exception:
        proc.terminate()


# ---------------------------------------------------------------- autostart
def _autostart_cmd() -> str:
    return f'"{sys.executable}" --background'


def autostart_enabled() -> bool:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            return bool(winreg.QueryValueEx(k, APP)[0])
    except OSError:
        return False


def set_autostart(on: bool) -> None:
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, APP, 0, winreg.REG_SZ, _autostart_cmd())
        else:
            try:
                winreg.DeleteValue(k, APP)
            except OSError:
                pass


# ---------------------------------------------------------------- main
def main(argv: list[str]) -> int:
    if "--quit" in argv:
        if _signal(EV_QUIT):
            for _ in range(150):  # wait up to 15 s for it to let go of its files
                if not _instance_running():
                    break
                time.sleep(0.1)
        return 0

    mutex = k32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        if "--background" not in argv:
            _signal(EV_SHOW)
        return 0

    ROOT.mkdir(parents=True, exist_ok=True)
    first_run = not STATE_FILE.exists()
    _setup_logging()
    state = _configure()
    url = f"http://127.0.0.1:{state['port']}"
    log.info("GPMC desktop starting: %s (data %s)", url, ROOT)

    st_proc, _job = _start_syncthing(state["st_port"])

    # gpmc registers a SIGINT handler at import time, which only works on the main
    # thread, so import the app here before the server thread starts.
    import uvicorn
    from app.main import app as web_app
    from app import config as app_config

    server = uvicorn.Server(uvicorn.Config(web_app, host="127.0.0.1", port=state["port"],
                                           log_config=None, access_log=False))
    threading.Thread(target=server.run, name="web", daemon=True).start()

    def wait_ready(timeout: float = 30) -> bool:
        import httpx
        end = time.time() + timeout
        while time.time() < end:
            try:
                if httpx.get(url + "/api/health", timeout=2).status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(0.25)
        return False

    def open_ui() -> None:
        if not QUIET:
            webbrowser.open(url)

    def open_photos() -> None:
        folder = Path(app_config.SYNC_DIR)
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(folder)

    import pystray
    from PIL import Image

    stopping = threading.Event()

    def quit_app(icon=None, _item=None) -> None:
        if stopping.is_set():
            return
        stopping.set()
        log.info("Quitting")
        server.should_exit = True
        _stop_syncthing(st_proc, state["st_port"])
        tray.stop()

    def toggle_autostart(_icon, _item) -> None:
        set_autostart(not autostart_enabled())

    menu = pystray.Menu(
        pystray.MenuItem("Open GPMC", lambda *_: open_ui(), default=True),
        pystray.MenuItem("Open upload folder", lambda *_: open_photos()),
        pystray.MenuItem("Start when I sign in", toggle_autostart,
                         checked=lambda _i: autostart_enabled(), enabled=FROZEN),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(f"Version {app_config.VERSION}", None, enabled=False),
        pystray.MenuItem("Quit GPMC", quit_app),
    )
    icon_file = next((p for p in (RES_DIR / "gpmc.ico", EXE_DIR / "build" / "gpmc.ico") if p.is_file()), None)
    image = Image.open(icon_file) if icon_file else Image.new("RGBA", (64, 64), (232, 165, 74, 255))
    tray = pystray.Icon(APP, image, "GPMC: photo backup", menu)

    def watch(name: str, action) -> None:
        h = k32.CreateEventW(None, False, False, name)
        while not stopping.is_set():
            if k32.WaitForSingleObject(h, 500) == 0:
                action()

    threading.Thread(target=watch, args=(EV_SHOW, open_ui), daemon=True).start()
    threading.Thread(target=watch, args=(EV_QUIT, quit_app), daemon=True).start()

    def after_start(icon) -> None:
        icon.visible = True
        ready = wait_ready()
        if not ready:
            log.error("Web app did not answer on %s", url)
            icon.notify(f"GPMC could not start. The log is in {ROOT / 'logs'}.", APP)
            return
        if "--background" not in argv or first_run:
            open_ui()
        if first_run and not QUIET:
            icon.notify("GPMC is running. Find it in the tray by the clock.", APP)

    tray.run(setup=after_start)  # blocks until quit_app()
    server.should_exit = True
    _stop_syncthing(st_proc, state["st_port"])
    k32.CloseHandle(mutex)
    return 0


if __name__ == "__main__":
    if not FROZEN:
        sys.path.insert(0, str(EXE_DIR.parent))  # run from a source checkout
    sys.exit(main(sys.argv[1:]))
