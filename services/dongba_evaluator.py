"""目标条件形态评价原型：只测图形，不识别文字或推断文化含义。"""

from dataclasses import dataclass
from typing import Protocol
import math

import numpy as np
from PIL import Image, ImageFilter, ImageOps

VERSION = "local-shape-v1"
MISMATCH = "当前书写与目标字差异较大，无法判定为正确临摹，请重新观察示范字。"


class VisionReviewer(Protocol):
    """未来适配器契约；当前没有实现、实例化或调用远程模型。"""

    def analyze(self, reference: Image.Image, handwriting: Image.Image,
                measured_result: dict) -> dict: ...


@dataclass
class Prepared:
    mask: np.ndarray
    aspect: float
    centroid: tuple
    bands: list
    density: float
    angle: float | None


def edit_photo(image, rotation=0, crop=(0, 0, 100, 100)):
    """旋转后按百分比裁剪；不做会掩盖方向错误的自动旋转。"""
    image = image.rotate(rotation, expand=True, fillcolor="white")
    left, top, right, bottom = crop
    if not (0 <= left < right <= 100 and 0 <= top < bottom <= 100):
        raise ValueError("裁剪区域无效：左边必须小于右边，上边必须小于下边。")
    box = (round(image.width * left / 100), round(image.height * top / 100),
           round(image.width * right / 100), round(image.height * bottom / 100))
    if box[2] - box[0] < 8 or box[3] - box[1] < 8:
        raise ValueError("裁剪区域过小，请保留完整字形。")
    return image.crop(box)


def binarize(image, threshold=180, remove_background=False):
    if not 40 <= threshold <= 230:
        raise ValueError("二值化阈值必须在 40–230 之间。")
    rgba = ImageOps.exif_transpose(image).convert("RGBA")
    rgb = Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("RGB")
    rgb.thumbnail((900, 900))
    # 最暗色通道保留红/蓝画笔；建议使用深色笔，避免白色或极浅色。
    gray = np.asarray(rgb).min(axis=2).astype(float)
    if remove_background:
        background = np.asarray(Image.fromarray(gray.astype("uint8")).filter(
            ImageFilter.GaussianBlur(30))).astype(float)
        gray = np.clip(gray / np.maximum(background, 1) * 255, 0, 255)
    return Image.fromarray(np.where(gray < threshold, 0, 255).astype("uint8"))


def prepare(binary):
    ink = np.asarray(binary.convert("L")) < 128
    ys, xs = np.where(ink)
    if len(xs) < 20 or len(xs) / ink.size < 0.0004:
        raise ValueError("没有检测到足够的笔迹，请书写后再提交，或调整裁剪与阈值。")
    if ink.mean() > 0.65:
        raise ValueError("图片大面积过暗或涂满，无法可靠评价；请使用白纸深色字并调整背景处理。")
    bbox = ink[ys.min():ys.max()+1, xs.min():xs.max()+1]
    h, w = bbox.shape
    if min(h, w) < 3:
        raise ValueError("笔迹过细或区域过小，无法可靠评价。")
    # 保留长宽比，消除画布空白、平移和整体尺寸差异。
    scale = 140 / max(h, w)
    resized = Image.fromarray((bbox * 255).astype("uint8")).resize(
        (max(1, round(w * scale)), max(1, round(h * scale))), Image.Resampling.NEAREST)
    normalized = Image.new("L", (160, 160))
    normalized.paste(resized, ((160-resized.width)//2, (160-resized.height)//2))
    mask = np.asarray(normalized) > 0
    yy, xx = np.where(mask)
    bands = [float(part.sum() / mask.sum()) for part in np.array_split(mask, 3, axis=0)]
    cov = np.cov(np.stack([xx, yy]))
    values, vectors = np.linalg.eigh(cov)
    angle = None
    if values[-1] > 1.5 * max(values[0], 1):
        v = vectors[:, -1]
        angle = math.degrees(math.atan2(v[1], v[0])) % 180
    return Prepared(mask, w/h, (float(xx.mean()/160), float(yy.mean()/160)),
                    bands, float(mask.mean()), angle)


def dilate(mask):
    return np.asarray(Image.fromarray((mask * 255).astype("uint8")).filter(ImageFilter.MaxFilter(7))) > 0


def coverage(a, b):
    precision = float((a & dilate(b)).sum() / max(a.sum(), 1))
    recall = float((b & dilate(a)).sum() / max(b.sum(), 1))
    return 2 * precision * recall / max(precision + recall, 1e-9)


def evaluate(reference, handwriting, *, threshold=180, remove_background=False):
    ref_binary = binarize(reference)
    user_binary = binarize(handwriting, threshold, remove_background)
    base = {"algorithm": VERSION, "prototype": True, "is_correct": None,
            "similarity_label": None, "structure_errors": [], "evaluation_feedback": [],
            "limitations": "图像形态原型分数，不是识别准确率；未经真实东巴手写样本标定，不判断笔顺、读音或文化含义。"}
    try:
        ref = prepare(ref_binary)
    except ValueError as exc:
        raise ValueError(f"示范图片不可用：{exc}") from exc
    try:
        user = prepare(user_binary)
    except ValueError as exc:
        return {**base, "status": "invalid", "similarity": None, "summary": str(exc),
                "evaluation_feedback": ["请保留完整字形，检查光照、裁剪与二值化预览后重新提交。"]}
    shape = coverage(user.mask, ref.mask)
    aspect = min(user.aspect/ref.aspect, ref.aspect/user.aspect)
    center_delta = np.array(user.centroid) - ref.centroid
    center = max(0, 1 - float(np.linalg.norm(center_delta)) * 3)
    distribution = max(0, 1 - sum(abs(a-b) for a, b in zip(ref.bands, user.bands))/2)
    density = min(user.density/ref.density, ref.density/user.density)
    score = round(100 * (.65*shape + .15*aspect + .10*center + .10*distribution), 1)
    errors, suggestions, regions = [], [], []
    for name, a, b, ref_share, user_share in zip(
            ["上部", "中部", "下部"], np.array_split(ref.mask, 3), np.array_split(user.mask, 3), ref.bands, user.bands):
        local = coverage(b, a) if a.any() and b.any() else (1.0 if not a.any() and not b.any() else 0.0)
        regions.append({"区域": name, "形态覆盖分": round(local*100, 1),
                        "示范笔迹占比": round(ref_share, 3), "书写笔迹占比": round(user_share, 3)})
        if ref_share > .10 and user_share < ref_share * .45:
            errors.append(f"{name}笔迹明显不足，可能缺失主要结构。")
            suggestions.append(f"对照示范检查{name}，补齐可见的轮廓和线条。")
        elif local < .60:
            errors.append(f"{name}轮廓或线条位置与示范差异较大。")
            suggestions.append(f"先观察{name}的外轮廓，再调整线条位置；本原型不能确定具体笔画名称。")
    if aspect < .8:
        errors.append("整体比例偏宽。" if user.aspect > ref.aspect else "整体比例偏窄。")
        suggestions.append("参照示范的宽高比例调整字形，不必与示范大小完全相同。")
    if abs(center_delta[0]) > .06 or abs(center_delta[1]) > .06:
        errors.append("笔迹重心位置偏移（归一化字形内）。")
        suggestions.append("检查左右及上下笔迹分布，把重心移向示范的相应位置。")
    angle_delta = None
    if ref.angle is not None and user.angle is not None:
        angle_delta = min(abs(ref.angle-user.angle), 180-abs(ref.angle-user.angle))
        if angle_delta > 20:
            errors.append("整体主轴方向偏差较大。")
            suggestions.append("对照示范检查整体倾斜方向；照片歪斜时先旋转图片。")
    if density < .5:
        errors.append("笔迹密度差异较大，可能存在多余涂画、缺笔或笔画过粗/过细。")
        suggestions.append("避免整块涂满，观察示范各线条间的留白。")
    mismatch = score < 55 or shape < .45 or density < .3
    status = "mismatch" if mismatch else ("close" if score >= 82 and shape >= .8 and not errors else "review")
    summary = MISMATCH if mismatch else ("形态较接近；原型不能据此认定为正确东巴字，仍需教师核验。" if status == "close" else "存在结构差异，请根据对照与建议修改后再试。")
    return {**base, "status": status, "is_correct": False if mismatch else None,
            "similarity": score, "summary": summary, "structure_errors": errors,
            "evaluation_feedback": suggestions or ["继续保持整体比例，逐区域对照线条与留白；本结果不评价笔顺。"],
            "metrics": {"容差形态覆盖分": round(shape*100, 1), "宽高比一致分": round(aspect*100, 1),
                        "重心一致分": round(center*100, 1), "区域分布一致分": round(distribution*100, 1),
                        "示范宽高比": round(ref.aspect, 3), "书写宽高比": round(user.aspect, 3),
                        "重心偏移_x_y": center_delta.round(3).tolist(),
                        "主轴角度差": round(angle_delta, 1) if angle_delta is not None else None},
            "regions": regions}
