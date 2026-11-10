"""未来舞蹈视频专业 Agent 接口；没有实现模型或工具调度。"""
from typing import Protocol
from services.dance_service import DanceRequest


class DanceAgent(Protocol):
    def create(self, request: DanceRequest, reference_video: bytes) -> dict:
        """未来独立核查动作/服装/场景资料并调用视频服务。"""
        ...
