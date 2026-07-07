"""LFO 노드 (§3.3, standalone) — sine/tri/saw/square 저주파 발진기.

독립 신호 노드. 출력 {"signal": name, "value": 0..1} 를 내고 signal_name() 으로
ModMatrix 가 'sig.<name>' 소스로 읽는다(그래프에 추가 시 매트릭스 에디터에 자동 노출).
preview = 파형 + 현재 위상 마커.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..audio.modmatrix import LFO as _LFO
from ..core.param_spec import Enum, Slider, Text
from ..core.processor import FrameCtx, Processor


class LFO(Processor):
    category = "audio"
    name = "LFO"
    kind = "lfo"
    inputs = ()
    params = {
        "name": Text(default="lfo1"),
        "shape": Enum(["sine", "tri", "saw", "square"], default="sine"),
        "rate": Slider(0.01, 10.0, default=1.0),  # Hz
        "phase": Slider(0.0, 1.0, default=0.0),  # 위상 오프셋 (사이클)
        "amount": Slider(0.0, 1.0, default=1.0),
    }

    def __init__(self, node_id: str = "lfo1", index: int = 0):
        super().__init__(node_id, index)
        self._v = 0.0

    def signal_name(self) -> str:
        return str(self.get("name"))

    def _eval(self, t: float) -> float:
        rate = float(self.get("rate"))
        phase = float(self.get("phase"))
        lfo = _LFO(rate=rate, shape=self.get("shape"))
        tt = t + (phase / rate if rate > 0 else 0.0)
        return float(self.get("amount")) * lfo.value(tt)

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[dict]:
        self._v = self._eval(ctx.t)
        self.preview = self._viz(ctx.t)
        return {"signal": self.signal_name(), "value": self._v}

    def _viz(self, t: float) -> np.ndarray:
        w, h = 320, 180
        canvas = np.zeros((h, w, 3), np.uint8)
        col = (242, 156, 184)  # cat-audio (BGR)
        rate = float(self.get("rate")) or 1.0
        # 2 사이클 표시
        span = 2.0 / rate
        pts = []
        for x in range(w):
            tt = t - span + (x / w) * span
            y = int((1.0 - self._eval(tt)) * (h - 20)) + 10
            pts.append((x, y))
        for i in range(1, len(pts)):
            cv2.line(canvas, pts[i - 1], pts[i], col, 1, cv2.LINE_AA)
        # 현재값 마커 (우측)
        cy = int((1.0 - self._v) * (h - 20)) + 10
        cv2.circle(canvas, (w - 6, cy), 4, (255, 255, 255), -1)
        cv2.putText(canvas, f"{self.get('shape')} {rate:.2f}Hz", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1, cv2.LINE_AA)
        return canvas
