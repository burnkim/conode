"""EnvelopeFollower 노드 (§3, standalone) — 오디오 특성에 어택/릴리스 엔벨로프.

AudioIn 출력(stems)의 stem×feature 를 골라 어택/릴리스 밸리스틱으로 매끈한 엔벨로프를
만든다. 출력 {"signal": name, "value": 0..1} → ModMatrix 가 'sig.<name>' 소스로 읽는다.
preview = 엔벨로프 히스토리 스크롤.
"""
from __future__ import annotations

import math
from collections import deque
from typing import Optional

import cv2
import numpy as np

from ..audio.features import FEATURES
from ..core.param_spec import Enum, IntSlider, Slider, Text
from ..core.processor import FrameCtx, Processor


class EnvelopeFollower(Processor):
    category = "audio"
    name = "EnvelopeFollower"
    kind = "envelope_follower"
    inputs = ("audio",)
    params = {
        "name": Text(default="env1"),
        "stem": IntSlider(0, 11, default=0),
        "feature": Enum(list(FEATURES), default="rms"),
        "attack_ms": Slider(1.0, 1000.0, default=20.0),
        "release_ms": Slider(1.0, 2000.0, default=250.0),
        "gain": Slider(0.0, 4.0, default=1.0),
    }

    def __init__(self, node_id: str = "env1", index: int = 0):
        super().__init__(node_id, index)
        self._env = 0.0
        self._last_t: Optional[float] = None
        self._hist: deque = deque(maxlen=320)

    def signal_name(self) -> str:
        return str(self.get("name"))

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[dict]:
        audio = inputs.get("audio") if isinstance(inputs.get("audio"), dict) else {}
        stems = audio.get("stems", []) if isinstance(audio, dict) else []
        i = int(self.get("stem"))
        feat = self.get("feature")
        raw = float(stems[i].get(feat, 0.0)) if 0 <= i < len(stems) else 0.0
        raw = max(0.0, min(1.0, raw * float(self.get("gain"))))

        dt = 1.0 / 30.0 if self._last_t is None else max(1e-3, ctx.t - self._last_t)
        self._last_t = ctx.t
        tau_ms = self.get("attack_ms") if raw > self._env else self.get("release_ms")
        coef = 1.0 - math.exp(-dt / (float(tau_ms) / 1000.0))
        self._env += coef * (raw - self._env)
        self._env = max(0.0, min(1.0, self._env))

        self._hist.append(self._env)
        self.preview = self._viz(raw)
        return {"signal": self.signal_name(), "value": self._env}

    def _viz(self, raw: float) -> np.ndarray:
        w, h = 320, 180
        canvas = np.zeros((h, w, 3), np.uint8)
        col = (242, 156, 184)  # cat-audio (BGR)
        # 엔벨로프 히스토리 라인
        hist = list(self._hist)
        if len(hist) > 1:
            n = len(hist)
            for x in range(1, n):
                x0 = int((x - 1) / max(1, n - 1) * (w - 1))
                x1 = int(x / max(1, n - 1) * (w - 1))
                y0 = int((1.0 - hist[x - 1]) * (h - 20)) + 10
                y1 = int((1.0 - hist[x]) * (h - 20)) + 10
                cv2.line(canvas, (x0, y0), (x1, y1), col, 1, cv2.LINE_AA)
        # 현재 raw(회색) vs env(마커)
        cv2.rectangle(canvas, (w - 22, h - int(raw * (h - 20)) - 10), (w - 14, h - 10), (120, 120, 120), -1)
        cv2.rectangle(canvas, (w - 12, h - int(self._env * (h - 20)) - 10), (w - 4, h - 10), col, -1)
        cv2.putText(canvas, f"{self.get('name')} stem{int(self.get('stem'))}.{self.get('feature')}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.38, col, 1, cv2.LINE_AA)
        return canvas
