"""未来东巴专业 Agent 的接口约定；无 SDK 运行循环，不是已实现 Agent。"""
from typing import Protocol
from PIL import Image


class DongbaAgent(Protocol):
    def evaluate(self, character_id: str, reference: Image.Image, handwriting: Image.Image) -> dict:
        """未来编排形态评价、视觉辅助和有来源的学习反馈。"""
        ...
