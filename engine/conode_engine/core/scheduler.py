"""Scheduler — 프레임 클록 + 노드별 target fps (PLAN §1.2).

각 노드는 독립 fps 로 tick 된다. 주기보다 늦으면 다음 기한을 리셋해
'지연 누적 금지'(latest-wins 정신)를 지킨다. asyncio 단일 루프.
"""
from __future__ import annotations

import asyncio
import time
from typing import Callable, Iterable, Optional

from .processor import FrameCtx, Processor


class Scheduler:
    def __init__(
        self,
        nodes: Optional[Iterable[Processor]] = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.nodes: list[Processor] = list(nodes or [])
        self.fps: dict[str, float] = {n.id: 30.0 for n in self.nodes}
        self._clock = clock
        self._stop: Optional[asyncio.Event] = None

    def add(self, node: Processor, fps: float = 30.0) -> None:
        self.nodes.append(node)
        self.fps[node.id] = fps

    async def _run_node(self, node: Processor, stop: asyncio.Event) -> None:
        target = self.fps.get(node.id, 30.0) or 30.0
        period = 1.0 / target
        start = self._clock()
        next_t = start
        seq = 0
        while not stop.is_set():
            t0 = self._clock()
            node.tick(FrameCtx(seq=seq, t=t0 - start))
            node.last_ms = (self._clock() - t0) * 1000.0
            seq += 1
            next_t += period
            delay = next_t - self._clock()
            if delay < 0:
                next_t = self._clock()  # 지연 누적 금지: 기한 리셋
                delay = 0.0
            try:
                await asyncio.wait_for(stop.wait(), timeout=delay)
            except asyncio.TimeoutError:
                pass

    async def run(self, duration: Optional[float] = None) -> dict[str, int]:
        """duration 초 동안(None=무한) 노드들을 돌리고 tick 카운트를 반환."""
        self._stop = asyncio.Event()
        tasks = [asyncio.create_task(self._run_node(n, self._stop)) for n in self.nodes]
        if duration is not None:
            await asyncio.sleep(duration)
            self._stop.set()
        try:
            await asyncio.gather(*tasks)
        finally:
            self._stop = None
        return {n.id: n.tick_count for n in self.nodes}

    def stop(self) -> None:
        if self._stop is not None:
            self._stop.set()
