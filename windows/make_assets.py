"""Generate build assets for the Windows app: the GPMC icon and the exe version info.

    python windows/make_assets.py        -> windows/build/gpmc.ico, windows/build/version_info.txt

The icon is the same "iris" mark the web UI uses (app/web/app.js), drawn with Pillow
so no binary artwork has to live in the repo.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "build"
AMBER = (232, 165, 74)
INK = (14, 20, 26)

# (start, end) angles in degrees, clockwise from 3 o'clock, and opacity, for the five
# iris blades in the web UI's 32x32 SVG mark.
BLADES = [(-90, -30, .9), (0, 55, .55), (75, 130, .8), (170, 220, .4), (245, 270, .65)]


def version() -> str:
    text = (HERE.parent / "app" / "config.py").read_text(encoding="utf-8")
    return re.search(r'^VERSION\s*=\s*"([^"]+)"', text, re.M).group(1)


def draw(size: int) -> Image.Image:
    s = size * 4  # supersample, then downscale for clean edges
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = s * 0.03
    d.ellipse([pad, pad, s - pad, s - pad], fill=INK + (255,))
    r = s * 0.40
    c = s / 2
    box = [c - r, c - r, c + r, c + r]
    for start, end, alpha in BLADES:
        mixed = tuple(round(INK[i] + (AMBER[i] - INK[i]) * (0.35 + 0.65 * alpha)) for i in range(3))
        d.pieslice(box, start, end, fill=mixed + (255,))
    hub = s * 0.12
    d.ellipse([c - hub, c - hub, c + hub, c + hub], fill=INK + (255,))
    ring = max(2, round(s * 0.03))
    inset = pad + ring * 1.5
    d.ellipse([inset, inset, s - inset, s - inset], outline=AMBER + (70,), width=ring)
    return img.resize((size, size), Image.LANCZOS)


def write_icon() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    big = draw(256)
    path = OUT / "gpmc.ico"
    big.save(path, format="ICO", sizes=[(n, n) for n in sizes],
             append_images=[draw(n) for n in sizes if n != 256])
    return path


def write_version_info(ver: str) -> Path:
    nums = [int(x) for x in re.findall(r"\d+", ver)[:3]] + [0]
    nums = (nums + [0, 0, 0, 0])[:4]
    tup = ", ".join(str(n) for n in nums)
    text = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers=({tup}), prodvers=({tup}), mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'RoboCrax'),
      StringStruct('FileDescription', 'GPMC: Google Photos backup'),
      StringStruct('FileVersion', '{ver}'),
      StringStruct('InternalName', 'GPMC'),
      StringStruct('LegalCopyright', 'Open source. github.com/robocrax/gpmc-daemon'),
      StringStruct('OriginalFilename', 'GPMC.exe'),
      StringStruct('ProductName', 'GPMC'),
      StringStruct('ProductVersion', '{ver}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    path = OUT / "version_info.txt"
    path.write_text(text, encoding="utf-8")
    return path


if __name__ == "__main__":
    ver = version()
    print(write_icon())
    print(write_version_info(ver))
    print(ver)
    sys.exit(0)
