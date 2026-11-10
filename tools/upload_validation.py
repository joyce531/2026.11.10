"""上传校验与安全预览。图片真实解码；视频仅做容器基础检查。"""

from io import BytesIO
from pathlib import Path
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from config.settings import IMAGE_MAX_MB, IMAGE_MAX_PIXELS, VIDEO_MAX_MB


def validate_size(data, limit_mb):
    if not data:
        raise ValueError("文件为空，请重新选择。")
    if len(data) > limit_mb * 1024 * 1024:
        raise ValueError(f"文件过大，请选择不超过 {limit_mb} MB 的文件。")


def prepare_image(data, filename):
    validate_size(data, IMAGE_MAX_MB)
    suffix = Path(filename).suffix.lower()
    formats = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG"}
    if suffix not in formats:
        raise ValueError("仅支持 PNG 或 JPEG 图片。")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                if image.format != formats[suffix]:
                    raise ValueError("文件内容与扩展名不一致，请重新导出为 PNG 或 JPEG。")
                if image.width * image.height > IMAGE_MAX_PIXELS:
                    raise ValueError("图片超过 1600 万像素，请缩小后上传。")
                size = image.size
                image.verify()
            with Image.open(BytesIO(data)) as image:
                oriented = ImageOps.exif_transpose(image).convert("RGBA")
                background = Image.new("RGBA", oriented.size, "white")
                preview = Image.alpha_composite(background, oriented).convert("RGB")
                preview.thumbnail((1600, 1600))
                return preview, size
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError("无法读取图片或图片尺寸不安全，请重新导出后上传。") from exc


def validate_video(data, filename):
    validate_size(data, VIDEO_MAX_MB)
    # MP4 的首个 box 应为有效的 ftyp；这不是完整的解码/安全扫描。
    if Path(filename).suffix.lower() != ".mp4":
        raise ValueError("当前仅支持 MP4 视频。")
    if len(data) < 16 or data[4:8] != b"ftyp":
        raise ValueError("未检测到 MP4 文件头，请重新导出为 MP4。")
    box_size = int.from_bytes(data[:4], "big")
    if box_size < 16 or box_size > len(data):
        raise ValueError("MP4 文件头不完整，请重新导出。")
