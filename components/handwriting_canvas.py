"""Streamlit v2 画布；PNG 仅在提交时传入 Python。"""
import base64
import binascii
import math
import re
from pathlib import Path
import streamlit.components.v2 as components
from tools.upload_validation import prepare_image

CANVAS = components.component(
    "naxi_handwriting_canvas",
    html="""<div class="toolbar">
      <label>画笔粗细 <input class="brush" type="range" min="2" max="30" value="10"><span class="size">10</span></label>
      <label>画笔颜色 <input class="color" type="color" value="#233d4a"></label>
      <button class="undo" type="button">撤销一笔</button><button class="clear" type="button">清空画布</button>
    </div><canvas width="640" height="480" aria-label="在线临摹画布"></canvas>
    <div class="toolbar"><button class="submit" type="button">提交画布评价</button>
    <span class="status" role="status">请用鼠标或触控笔书写。浅色笔迹可能无法检测。</span></div>""",
    css=""":host {font-family:sans-serif;color:#233D4A;}
    canvas {width:100%;max-width:800px;aspect-ratio:4/3;background:white;border:1px solid #8c9b9d;
      border-radius:6px;touch-action:none;display:block;cursor:crosshair;}
    .toolbar {display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin:12px 0;}
    label {display:flex;align-items:center;gap:6px;}
    button {border:1px solid #8c9b9d;border-radius:6px;padding:9px 14px;background:#f8f6f0;color:#233d4a;cursor:pointer;}
    button:disabled {opacity:.5;cursor:not-allowed;} .submit {background:#ad4939;color:white;}
    button:focus-visible {outline:3px solid #ad4939;} .status {font-size:14px;}""",
    js=Path(__file__).with_name("handwriting_canvas.js").read_text(encoding="utf-8"),
)

def decode_canvas(payload):
    if isinstance(payload, dict):
        validate_strokes(payload)
        payload = payload.get('png')
    prefix = "data:image/png;base64,"
    if not isinstance(payload, str) or not payload.startswith(prefix) or len(payload) > 14_000_000:
        raise ValueError("画布数据格式或大小无效，请清空后重新书写。")
    try:
        data = base64.b64decode(payload[len(prefix):], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("画布图片传输失败，请重新提交。") from exc
    return prepare_image(data, "canvas.png")[0]


def validate_strokes(payload):
    if (payload.get('version') != 1 or payload.get('width') != 640 or payload.get('height') != 480
            or not isinstance(payload.get('submission_id'),str) or len(payload['submission_id']) > 80):
        raise ValueError('画布提交信息无效。')
    strokes = payload.get('strokes')
    if not isinstance(strokes,list) or len(strokes)>300:
        raise ValueError('笔画轨迹数量无效。')
    count=0
    for stroke in strokes:
        if not isinstance(stroke,dict):
            raise ValueError('笔画轨迹格式无效。')
        points=stroke.get('points')
        width=stroke.get('width')
        if (not isinstance(width,(int,float)) or not 2<=width<=30
                or not isinstance(stroke.get('color'),str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',stroke['color'])
                or not isinstance(points,list) or not 1<=len(points)<=5000):
            raise ValueError('笔画参数无效。')
        count+=len(points)
        if count>100000:
            raise ValueError('轨迹点过多，请清空后重新书写。')
        for point in points:
            if (not isinstance(point,list) or len(point)!=2
                    or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in point)
                    or not 0<=point[0]<=640 or not 0<=point[1]<=480):
                raise ValueError('轨迹坐标无效。')
    return strokes

def handwriting_canvas(key, enabled):
    return CANVAS(key=key, data={"enabled": enabled},
                  on_submission_change=lambda: None)
