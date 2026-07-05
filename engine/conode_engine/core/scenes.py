"""씬/큐 시스템 (D, PLAN §0.2 "cue 시스템") — 파라미터 스냅샷 + 크로스페이드 recall.

씬 = 그래프 전체 파라미터 스냅샷(nodeId.path→value). recall 시 fade 초 동안 현재값에서
목표값으로 보간(수치형), 비수치형은 종료 시 스냅. temporal transition = 라이브 악기의 핵심.
"""
from __future__ import annotations

from typing import Optional


class SceneStore:
    def __init__(self):
        self.scenes: dict[str, dict[str, object]] = {}
        self._fade: Optional[dict] = None  # {start, end, t0, dur}
        self.bindings: dict[str, tuple[str, float]] = {}  # event → (scene, fade) — 큐(§2)

    def capture(self, graph) -> dict[str, object]:
        snap: dict[str, object] = {}
        for nid, node in graph.nodes.items():
            for path, val in node.store.values().items():
                snap[f"{nid}.{path}"] = val
        return snap

    def save(self, name: str, graph) -> None:
        self.scenes[name] = self.capture(graph)

    def remove(self, name: str) -> None:
        self.scenes.pop(name, None)

    def names(self) -> list[str]:
        return list(self.scenes.keys())

    def recall(self, name: str, graph, fade: float = 0.0, now: float = 0.0) -> bool:
        target = self.scenes.get(name)
        if target is None:
            return False
        if fade <= 0:
            self._apply(graph, target)
            self._fade = None
        else:
            self._fade = {"start": self.capture(graph), "end": dict(target), "t0": now, "dur": fade}
        return True

    # --- 큐 바인딩 (§2: 이벤트 → 씬 전환) ---
    def bind(self, event: str, scene: str, fade: float = 0.0) -> None:
        self.bindings[event] = (scene, fade)

    def trigger(self, event: str, graph, now: float = 0.0) -> bool:
        b = self.bindings.get(event)
        if b is None:
            return False
        scene, fade = b
        return self.recall(scene, graph, fade=fade, now=now)

    def update(self, graph, now: float) -> None:
        """크로스페이드 진행 — 매 tick 호출."""
        f = self._fade
        if f is None:
            return
        p = min(1.0, (now - f["t0"]) / f["dur"]) if f["dur"] > 0 else 1.0
        for path, endv in f["end"].items():
            startv = f["start"].get(path, endv)
            if isinstance(endv, (int, float)) and isinstance(startv, (int, float)) and not isinstance(endv, bool):
                self._set(graph, path, startv + (endv - startv) * p)
            elif p >= 1.0:
                self._set(graph, path, endv)
        if p >= 1.0:
            self._fade = None

    def _apply(self, graph, snap: dict) -> None:
        for path, val in snap.items():
            self._set(graph, path, val)

    def _set(self, graph, path: str, val) -> None:
        nid, _, ppath = path.partition(".")
        node = graph.nodes.get(nid)
        if node is not None and ppath:
            try:
                node.set(ppath, val)
            except (KeyError, ValueError):
                pass
