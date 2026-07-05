"""ModMatrix 노드 (M4, PLAN §3.3) — 오디오 특성/LFO 로 그래프 파라미터를 모듈레이션.

audio.modmatrix.ModMatrix(라우팅 엔진)를 감싸고 그래프 콜백을 연결한다. 프롬프트
바인딩(token:{source})도 여기서 resolve → 타깃 노드 prompt 에 push. graph 는 app 이 세팅.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..audio.modmatrix import LFO, ModCell
from ..audio.modmatrix import ModMatrix as _Matrix
from ..audio.prompt_binding import bind_prompt
from ..core.param_spec import Text, Toggle
from ..core.processor import FrameCtx, Processor


class ModMatrix(Processor):
    category = "audio"
    name = "ModMatrix"
    kind = "mod_matrix"
    inputs = ("audio", "gesture")
    params = {
        "enable": Toggle(True),
        "prompt_target": Text(default="live1"),
        "prompt_template": Text(
            default="a field of (stars:{stem0.rms}), (geometric:{stem2.flux})", multiline=True
        ),
    }

    def __init__(self, node_id: str = "mod1", index: int = 0):
        super().__init__(node_id, index)
        self.graph = None  # app.py / server 가 세팅
        self.matrix = _Matrix()
        self._last_t: Optional[float] = None
        self._install_defaults()

    def _install_defaults(self) -> None:
        self.matrix.add_lfo("lfo0", LFO(rate=0.4, shape="sine"))
        self.matrix.add_cell(ModCell("stem0.rms", "live1.prompt_strength", amount=1.0))
        self.matrix.add_cell(ModCell("stem2.centroid", "live1.controlnet.weight", amount=0.8))
        self.matrix.add_cell(ModCell("lfo0", "cam1.exposure", amount=0.5))
        # 제스처 소스(§3.3): 프레임 제스처가 디퓨전 강도를 밀어올림
        self.matrix.add_cell(ModCell("gesture.frame", "live1.prompt_strength", amount=0.5))

    # --- 그래프 콜백 (target = "nodeId.paramPath") ---
    def _node_path(self, target: str):
        nid, _, path = target.partition(".")
        node = self.graph.nodes.get(nid) if self.graph else None
        return node, path

    def _get(self, target: str) -> float:
        n, p = self._node_path(target)
        try:
            return float(n.get(p)) if n else 0.0
        except Exception:
            return 0.0

    def _set(self, target: str, val: float) -> None:
        n, p = self._node_path(target)
        if n:
            try:
                n.set(p, val)
            except (KeyError, ValueError):
                pass

    def _rng(self, target: str):
        n, p = self._node_path(target)
        return n.param_range(p) if n else (0.0, 1.0)

    def _mod(self, target: str) -> bool:
        n, p = self._node_path(target)
        return n.is_modulatable(p) if n else False

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[dict]:
        audio = inputs.get("audio") if isinstance(inputs.get("audio"), dict) else {}
        gesture = inputs.get("gesture") if isinstance(inputs.get("gesture"), dict) else {}
        features = {**audio, "gesture": gesture}  # 오디오 스템 + 제스처 소스 결합
        if not self.get("enable") or self.graph is None:
            self.preview = self._viz(features, {})
            return {"features": features, "applied": {}}

        t = ctx.t
        dt = 1.0 / 30.0 if self._last_t is None else max(1e-3, t - self._last_t)
        self._last_t = t

        applied = self.matrix.apply(
            features, t, dt, get=self._get, set_=self._set, rng=self._rng, modulatable=self._mod
        )

        # 프롬프트 바인딩 → 타깃 노드 prompt
        tgt = self.graph.nodes.get(self.get("prompt_target")) if self.graph else None
        if tgt is not None and "prompt" in tgt.store.paths():
            resolved = bind_prompt(
                self.get("prompt_template"), lambda s: self.matrix.resolve(s, features, t)
            )
            try:
                tgt.set("prompt", resolved)
            except (KeyError, ValueError):
                pass

        self.preview = self._viz(features, applied)
        return {"features": features, "applied": applied}

    def _viz(self, features: dict, applied: dict) -> np.ndarray:
        w, h = 320, 180
        canvas = np.zeros((h, w, 3), np.uint8)
        col = (242, 156, 184)  # cat-audio
        rows = list(applied.items())[:6]
        y = 24
        for target, val in rows:
            lo, hi = self._rng(target)
            frac = (val - lo) / (hi - lo + 1e-9)
            cv2.rectangle(canvas, (10, y - 10), (10 + int(frac * (w - 120)), y), col, -1)
            cv2.putText(canvas, target.split(".", 1)[-1], (w - 110, y), cv2.FONT_HERSHEY_SIMPLEX, 0.35, col, 1, cv2.LINE_AA)
            y += 26
        if not rows:
            cv2.putText(canvas, "modmatrix (no targets)", (10, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
        return canvas
