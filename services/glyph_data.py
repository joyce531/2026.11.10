"""独立 CSV 资料库；只读，不替代现有 JSON 教学字库。"""
import csv
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath

from PIL import Image
from tools.upload_validation import prepare_image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GLYPH_FIELDS = (
    "glyph_id", "chinese_meaning", "english_label", "image_file", "image_path",
    "image_width", "image_height",
)
SAMPLE_FIELDS = (
    "sample_id", "character_id", "input_method", "image_path", "stroke_data_path",
    "annotator_id", "human_rating", "error_type", "annotation_status", "notes",
)


@dataclass
class CatalogResult:
    records: list[dict[str, str]] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


@dataclass
class ImageResult:
    image: Image.Image | None = None
    messages: list[str] = field(default_factory=list)


class GlyphDataService:
    def __init__(self, root=PROJECT_ROOT):
        # root 可注入用于隔离测试；CSV 中所有路径始终相对此根目录。
        self.root = Path(root).resolve()

    def _path(self, relative, area):
        if not isinstance(relative, str) or not relative.strip():
            raise ValueError("路径为空。")
        relative = relative.replace("\\", "/")
        if Path(relative).is_absolute() or PureWindowsPath(relative).drive or ":" in relative:
            raise ValueError("必须使用项目根目录相对路径，不能使用绝对路径或 URL。")
        if ".." in Path(relative).parts:
            raise ValueError("路径不能包含 ..。")
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root / area):
            raise ValueError(f"路径必须位于 {area} 内（不能通过链接越界）。")
        return path

    def check_path(self, relative, area="data/glyphs"):
        """返回 (是否为存在的文件, 中文提示)，不读取任意外部文件。"""
        try:
            path = self._path(relative, area)
            if not path.is_file():
                return False, f"文件不存在：{relative}"
            return True, ""
        except (ValueError, OSError, RuntimeError):
            return False, f"路径无效：{relative}；须位于 {area} 内并使用项目相对路径。"

    def _read(self, name, fields, required):
        result = CatalogResult()
        try:
            with (self.root / name).open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, strict=True)
                headers = reader.fieldnames or []
                missing = set(fields) - set(headers)
                if missing or len(headers) != len(set(headers)):
                    return CatalogResult(messages=[f"{name} 表头不完整或重复；缺少字段：{', '.join(sorted(missing)) or '无（重复表头）'}"])
                seen = set()
                for row in reader:
                    line = reader.line_num
                    if None in row or any(value is None for value in row.values()):
                        result.messages.append(f"{name} 第 {line} 行列数与表头不一致，已跳过。")
                        continue
                    row = {key: value.strip() for key, value in row.items()}
                    empty = [key for key in required if not row[key]]
                    if empty:
                        result.messages.append(f"{name} 第 {line} 行必填值为空：{', '.join(empty)}；已跳过。")
                        continue
                    identity = row[fields[0]]
                    if identity in seen:
                        return CatalogResult(messages=[f"{name} 存在重复 {fields[0]}：{identity}；请修正后重新读取。"])
                    seen.add(identity)
                    result.records.append(row)
        except (OSError, UnicodeError, csv.Error):
            return CatalogResult(messages=[f"无法读取 {name}：请检查文件是否存在、UTF-8 编码及 CSV 格式。"])
        return result

    def read_glyph_catalog(self):
        result = self._read("data/glyphs/glyph_catalog.csv", GLYPH_FIELDS,
                            GLYPH_FIELDS)
        for row in result.records:
            messages = []
            ok, message = self.check_path(row["image_path"])
            if not ok:
                messages.append(message)
            try:
                if int(row['image_width']) <= 0 or int(row['image_height']) <= 0:
                    raise ValueError
            except ValueError:
                messages.append("图片宽高必须为正整数。")
            if Path(row['image_path'].replace('\\', '/')).name != row['image_file']:
                messages.append("image_file 与 image_path 文件名不一致。")
            result.messages.extend(f"{row['glyph_id']}：{message}" for message in messages)
        return result

    def find_glyphs(self, glyph_id):
        """按五字基础目录中的 glyph_id 查询。"""
        result = self.read_glyph_catalog()
        result.records = [row for row in result.records if row["glyph_id"] == glyph_id]
        if not result.records:
            result.messages.append(f"未找到 glyph_id：{glyph_id}")
        return result

    def load_reference_image(self, record):
        messages = []
        relative = record.get("image_path", "")
        ok, message = self.check_path(relative)
        if not ok:
            return ImageResult(messages=messages + [message])
        try:
            path = self._path(relative, "data/glyphs")
            if path.stat().st_size > 10 * 1024 * 1024:
                raise ValueError("图片超过 10 MB。")
            image, size = prepare_image(path.read_bytes(), path.name)
            if size != (int(record['image_width']), int(record['image_height'])):
                return ImageResult(messages=["图片实际尺寸与目录不一致，请重新建档。"])
            return ImageResult(image, messages)
        except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
            return ImageResult(messages=messages + [f"标准图读取失败：{exc}"])

    def find_samples(self, character_id=None):
        result = self._read("data/handwriting_samples/sample_annotations.csv", SAMPLE_FIELDS,
                            ("sample_id", "character_id", "input_method", "image_path"))
        if character_id is not None:
            result.records = [row for row in result.records if row["character_id"] == character_id]
            if not result.records:
                result.messages.append(f"未找到该字符的手写样本：{character_id}")
        for row in result.records:
            for key, area in (("image_path", "data/handwriting_samples/images"),
                              ("stroke_data_path", "data/handwriting_samples/strokes")):
                if key == "stroke_data_path" and not row[key]:
                    continue
                ok, message = self.check_path(row[key], area)
                if not ok:
                    result.messages.append(f"{row['sample_id']}：{message}")
            if row["annotation_status"] != "annotated":
                result.messages.append(f"{row['sample_id']}：尚未完成人工标注。")
        return result
