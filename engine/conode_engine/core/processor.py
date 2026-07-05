"""Processor — 모든 노드의 베이스 (PLAN §1.2, R4).

R4: nodes/ 1파일 1노드, Processor 상속, tick() 안에서 blocking I/O 금지.
서브클래스는 process(ctx, inputs) 를 override 한다. inputs 는 {포트명: 업스트림 output}.
tick() 은 카운트/타이밍을 감싸고 self.output 에 결과(프레임 등)를 저장한다.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

from .param_spec import ParamStore


@dataclass
class FrameCtx:
    seq: int = 0
    t: float = 0.0  # 시작 이후 경과 초


class Processor:
    category: str = "generate"
    name: str = "Node"
    inputs: tuple[str, ...] = ()  # 입력 포트 이름들 (소스 노드는 빈 튜플)
    params: dict[str, Any] = {}

    def __init__(self, node_id: str, index: int = 0):
        self.id = node_id
        self.index = index
        self.store = ParamStore(type(self).params)
        self.tick_count = 0
        self.last_ms = 0.0
        self.output: Any = None  # 최신 출력 (다운스트림이 읽음)

    # --- 파라미터 ---
    def get(self, path: str) -> Any:
        return self.store.get(path)

    def set(self, path: str, value: Any) -> Any:
        return self.store.set(path, value)

    def modulation_targets(self) -> list[str]:
        return self.store.modulation_targets()

    # --- 실행 ---
    def tick(self, ctx: FrameCtx, inputs: Optional[dict[str, Any]] = None) -> Any:
        t0 = time.perf_counter()
        self.tick_count += 1
        self.output = self.process(ctx, inputs or {})
        self.last_ms = (time.perf_counter() - t0) * 1000.0
        return self.output

    def process(self, ctx: FrameCtx, inputs: dict[str, Any]) -> Any:
        """서브클래스 override. inputs[port] = 업스트림 노드 output. 기본은 no-op."""
        return None

    # --- 직렬화 ---
    def describe(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "index": self.index,
            "inputs": list(self.inputs),
            "params": self.store.describe(),
        }
