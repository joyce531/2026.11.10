"""Agent 的受控图像工具：没有任意文件路径或外部命令入口。"""
from services.glyph_data import GlyphDataService
from services.dongba_evaluator import evaluate
from services.dongba_vision import EvaluationError


def get_reference_character(character_id, catalog=None):
    catalog = catalog or GlyphDataService()
    result = catalog.find_glyphs(character_id)
    if not result.records:
        raise EvaluationError('找不到目标字形，请检查 glyph_catalog.csv；不会调用 AI 猜测。')
    record = result.records[0]
    loaded = catalog.load_reference_image(record)
    if loaded.image is None:
        raise EvaluationError('标准图片不可用：'+'；'.join(loaded.messages))
    return record, loaded.image


def measure_structure(reference, handwriting):
    return evaluate(reference, handwriting)
