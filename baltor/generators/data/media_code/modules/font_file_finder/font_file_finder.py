"""Find font files on the system without guessing paths.

Searches standard font folders (Linux, macOS, Windows, and user folders) or
custom roots for ``.ttf/.otf/.ttc`` files, reads each font's family and
style names with Pillow, and resolves a request like ("Inter", "Bold") to a
file, with a fallback chain (for example Inter -> DejaVu Sans -> any sans).
Uses ``fc-match`` when fontconfig is installed and nothing matched directly.

Usage::

    from font_file_finder import find_font, list_fonts
    path = find_font("Inter", "Bold", fallbacks=[("DejaVu Sans", "Bold")])
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from PIL import ImageFont

DEFAULT_ROOTS = ["/usr/share/fonts", "/usr/local/share/fonts", str(Path.home() / ".fonts"),
                 str(Path.home() / ".local/share/fonts"), "/Library/Fonts", "/System/Library/Fonts",
                 str(Path.home() / "Library/Fonts"), "C:\\Windows\\Fonts"]
EXTS = {".ttf", ".otf", ".ttc"}


def list_fonts(roots=None) -> list[dict]:
    out = []
    for root in roots or DEFAULT_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for f in sorted(files):
                if Path(f).suffix.lower() not in EXTS:
                    continue
                p = os.path.join(dirpath, f)
                try:
                    family, style = ImageFont.truetype(p, 12).getname()
                except OSError:
                    continue
                out.append({"path": p, "family": family, "style": style})
    return sorted(out, key=lambda d: (d["family"], d["style"], d["path"]))


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def find_font(family: str, style: str = "Regular", fallbacks=(), roots=None, use_fc_match: bool = True) -> str | None:
    fonts = list_fonts(roots)
    for fam, sty in [(family, style), *fallbacks]:
        exact = [f for f in fonts if _norm(f["family"]) == _norm(fam) and _norm(f["style"]) == _norm(sty)]
        if exact:
            return exact[0]["path"]
        loose = [f for f in fonts if _norm(f["family"]).startswith(_norm(fam)) and _norm(sty) in _norm(f["style"])]
        if loose:
            return loose[0]["path"]
    if use_fc_match and shutil.which("fc-match"):
        r = subprocess.run(["fc-match", "-f", "%{file}", f"{family}:style={style}"], capture_output=True, text=True,
                           timeout=20)
        if r.returncode == 0 and r.stdout and os.path.exists(r.stdout.strip()):
            return r.stdout.strip()
    return None
