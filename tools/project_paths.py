"""Resolve the starter-package layout or the installed single-repository layout."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = ROOT / ".52km-installed.json"
INSTALLED = MARKER.is_file() or (
    (ROOT / "index.html").is_file()
    and (ROOT / "assets/app.js").is_file()
    and (ROOT / "archive/index.html").is_file()
    and not (ROOT / "site/index.html").exists()
)
SITE = ROOT if INSTALLED else ROOT / "site"
CONTENT = ROOT / "content"
PRIVATE = ROOT / "_private"


def ensure_new_site():
    if not (SITE / "index.html").exists():
        raise SystemExit(f"New website index.html not found under {SITE}.")
    text = (SITE / "index.html").read_text(encoding="utf-8-sig")
    if not (
        re.search(r'<header\b[^>]*class=["\'][^"\']*\btopbar\b', text, re.I)
        and re.search(r'src=["\'][^"\']*assets/app\.js["\']', text, re.I)
    ):
        raise SystemExit("This is not the new weekly website. Original 52@52 site left unchanged.")
    if MARKER.exists():
        info = json.loads(MARKER.read_text(encoding="utf-8"))
        if info.get("layout") != "root-with-archive-v1":
            raise SystemExit("Unrecognized installation marker. No files changed.")
