"""未来音乐专业 Agent 接口；当前页面直接处理参数，不实例化此接口。"""
from typing import Protocol
from services.music_service import MusicRequest


class MusicAgent(Protocol):
    def create(self, request: MusicRequest) -> dict:
        """未来独立检索音乐资料、审查参数并调用音乐生成服务。"""
        ...
