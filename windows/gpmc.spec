# PyInstaller spec for the GPMC Windows app (one-folder build).
# Run through windows/build.ps1, which generates windows/build/* first.
import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

HERE = os.path.abspath(SPECPATH)
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build")

datas = [
    (os.path.join(ROOT, "app", "web"), os.path.join("app", "web")),
    (os.path.join(BUILD, "gpmc.ico"), "."),
]
binaries = []
hiddenimports = collect_submodules("app") + collect_submodules("uvicorn")
for pkg in ("gpmc", "pillow_heif"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    [os.path.join(HERE, "gpmc_desktop.py")],
    pathex=[ROOT],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest"],
    # pystray is LGPL: ship it as plain .py files so it can be swapped out.
    module_collection_mode={"pystray": "py"},
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GPMC",
    console=False,
    icon=os.path.join(BUILD, "gpmc.ico"),
    version=os.path.join(BUILD, "version_info.txt"),
    upx=False,
)

coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="GPMC")
