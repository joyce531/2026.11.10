"""字库边界：只展示核验且授权的条目，不访问外部数据库。"""

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from PIL import Image, ImageDraw

from tools.upload_validation import prepare_image

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "dongba"


def load_catalog(root=DATA_DIR):
    root = Path(root).resolve()
    try:
        schema = json.loads((DATA_DIR / "characters.schema.json").read_text(encoding="utf-8"))
        entries = json.loads((root / "characters.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(entries)
        ids = [entry["character_id"] for entry in entries]
        if len(set(ids)) != len(ids):
            raise ValueError("字库包含重复的 character_id。")
        usable = []
        for entry in entries:
            if entry["review_status"] != "verified" or entry["usage_permission"] != "authorized":
                continue
            path = (root / entry["reference_image"]).resolve()
            if not path.is_relative_to(root) or Path(entry["reference_image"]).is_absolute():
                raise ValueError("示范图片路径必须位于 data/dongba 目录内。")
            if path.stat().st_size > 10 * 1024 * 1024:
                raise ValueError("示范图片超过 10 MB。")
            image, _ = prepare_image(path.read_bytes(), path.name)
            usable.append({**entry, "image": image})
        return usable
    except (OSError, ValueError) as exc:
        raise ValueError(f"无法加载字库：{exc}") from exc
    except Exception as exc:
        # Schema 错误只输出位置和原因，不输出整个数据文件。
        from jsonschema import ValidationError
        if isinstance(exc, ValidationError):
            raise ValueError(f"字库字段校验失败：{exc.message}") from exc
        raise


def geometry_reference():
    """工程测试用非文字图形；不属于教学字库。"""
    image = Image.new("RGB", (480, 480), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((130, 50, 350, 240), outline="#233D4A", width=12)
    draw.line([(240, 240), (240, 410), (350, 410)], fill="#233D4A", width=12)
    return image
