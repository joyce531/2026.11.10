"""Enable evidence slots only when matching local PNG/JPEG files decode.

No screenshots are generated here. Missing material remains visibly pending.
"""
from pathlib import Path
import re

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "evidence"
PAGES = [ROOT / "index.html", *(ROOT / "slides").glob("*.html")]
SLOT = re.compile(r'data-ready="(?:true|false)" data-src="../assets/evidence/([^"]+)"')


def valid_image(filename: str) -> bool:
    if "/" in filename or "\\" in filename or filename.startswith("."):
        return False
    path = ASSETS / filename
    if not path.is_file() or path.stat().st_size > 15 * 1024 * 1024:
        return False
    try:
        with Image.open(path) as image:
            if image.format not in {"PNG", "JPEG"}:
                return False
            image.verify()
        return True
    except (OSError, UnidentifiedImageError, ValueError):
        return False


count = 0
ready = 0
for page in PAGES:
    html = page.read_text(encoding="utf-8")
    def replace(match):
        global count, ready
        count += 1
        enabled = valid_image(match.group(1))
        ready += int(enabled)
        return f'data-ready="{str(enabled).lower()}" data-src="../assets/evidence/{match.group(1)}"'
    updated = SLOT.sub(replace, html)
    if updated != html:
        page.write_text(updated, encoding="utf-8")
print(f"证据截图位 {count} 个；已启用真实可读图片 {ready} 个，其他保持待插入。")
