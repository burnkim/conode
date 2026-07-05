"""Processor — 모든 노드의 베이스 (PLAN §1.2, R4).

R4: nodes/ 1파일 1노드, Processor 상속, tick() 안에서 blocking I/O 금지.
서브클래스는 process(ctx) 를 override 한다. tick() 은 카운트/타이밍을 감싼다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .param_spec import ParamSpec, ParamStore


@dataclass
class FrameCtx:
    seq: int = 0
    t: float = 0.0  # 시작 이후 경과 초


class Processor:
    category: str = "generate"
    name: str = "Node"
    params: dict[str, Any] = {}

    def __init__(self, node_id: str, index: int = 0):
        self.id = node_id
        self.index = index
        self.store = ParamStore(type(self).params)
        self.tick_count = 0
        self.last_ms = 0.0

    # --- 파라미터 ---
    def get(self, path: str) -> Any:
        return self.store.get(path)

    def set(self, path: str, value: Any) -> Any:
        return self.store.set(path, value)

    def modulation_targets(self) -> list[str]:
        return self.store.modulation_targets()

    # --- 실행 ---
    def tick(self, ctx: FrameCtx) -> Any:
        self.tick_count += 1
        return self.process(ctx)

    def process(self, ctx: FrameCtx) -> Any:
        """서브클래스 override. 기본은 no-op."""
        return None

    # --- 직렬화 ---
    def describe(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "index": self.index,
            "params": self.store.describe(),
        }
