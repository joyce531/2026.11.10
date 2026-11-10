"""曲谱改编入口；旧自由创作契约保留兼容，但不提供自由生成。"""
from dataclasses import dataclass

INSTRUMENTS = ["钢琴（通用）", "长笛（通用）", "弦乐组（通用）", "打击乐（通用）"]
TIMBRES = ["弹拨质感", "吹管质感", "弓弦质感", "打击质感"]


@dataclass(frozen=True)
class MusicRequest:
    instruments: list[str]
    timbres: list[str]
    style: str
    mood: str
    tempo_bpm: int
    duration_seconds: int
    rhythm: str
    description: str


def validate_request(request: MusicRequest):
    errors = []
    if not request.instruments or any(x not in INSTRUMENTS for x in request.instruments):
        errors.append("请选择至少一种列表中的乐器。")
    if not request.timbres or any(x not in TIMBRES for x in request.timbres):
        errors.append("请选择至少一种期望音色。")
    if not 40 <= request.tempo_bpm <= 180 or not 10 <= request.duration_seconds <= 120:
        errors.append("速度或时长超出当前原型范围。")
    if len(request.description) > 1000:
        errors.append("作品描述不能超过 1000 字。")
    return errors


def generate_music(request: MusicRequest):
    errors = validate_request(request)
    if errors:
        raise ValueError("；".join(errors))
    raise NotImplementedError("音乐生成 API 尚未接入，没有生成音频。")


def arrange_music(data, filename, asset_ids, style, preservation, *, real=None, client=None):
    from naxi_agents.music_agent import MusicArrangementAgent
    return MusicArrangementAgent(client=client).run(data,filename,asset_ids,style,preservation,real=real)
