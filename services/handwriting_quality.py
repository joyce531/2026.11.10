"""保守的质量门槛和非破坏性 ROI 预处理；阈值是工程启发式。"""
import numpy as np
from PIL import Image, ImageOps


def inspect_image(image):
    rgba = ImageOps.exif_transpose(image).convert('RGBA')
    rgb = Image.alpha_composite(Image.new('RGBA', rgba.size, 'white'), rgba).convert('RGB')
    rgb.thumbnail((1200, 1200))
    gray = np.asarray(rgb).min(axis=2).astype(float)
    ink = gray < 200
    ys, xs = np.where(ink)
    reason = ''
    if len(xs) < 20 or ink.mean() < .0004:
        reason = '没有检测到足够笔迹，请在白纸或画布上用深色笔书写。'
    elif ink.mean() > .65:
        reason = '图片大面积过暗或涂满，请改善光照并保留完整字形。'
    elif min(xs.max()-xs.min()+1, ys.max()-ys.min()+1) < 8:
        reason = '笔迹区域过小或过细，请放大拍摄并对焦。'
    bbox = None
    sharpness = 0.0
    if len(xs):
        left, top, right, bottom = int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)
        bbox = (max(0,left-12),max(0,top-12),min(rgb.width,right+12),min(rgb.height,bottom+12))
        # 包含边缘外的白底；否则单条实心线的紧包围盒全黑，会被误判模糊。
        roi = gray[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        if min(roi.shape) > 2:
            lap = 4*roi[1:-1,1:-1]-roi[:-2,1:-1]-roi[2:,1:-1]-roi[1:-1,:-2]-roi[1:-1,2:]
            sharpness = float(lap.var())
        if not reason and sharpness < 6:
            reason = '笔迹边缘过于模糊，无法可靠比较；请重新对焦拍摄，避免抖动。'
    # 只裁空白并等比缩放，不二值化、补笔、镜像或自动纠正方向。
    crop = rgb.crop(bbox) if bbox and not reason else rgb.copy()
    normalized = ImageOps.pad(crop, (512,512), method=Image.Resampling.LANCZOS, color='white')
    return {'usable': not reason, 'reason': reason, 'sharpness': round(sharpness,2),
            'ink_fraction': round(float(ink.mean()),5), 'bbox': bbox}, normalized
