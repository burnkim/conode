"""Canny 노드 (T8) — PLAN §1.3 Vision. 순수 OpenCV(모델 불필요).

입력 프레임 → 그레이 → Canny 엣지 → BGR. low/high 임계값은 modulatable.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import IntSlider, Toggle
from ..core.processor import FrameCtx, Processor


class Canny(Processor):
    category = "vision"
    name = "Canny"
    inputs = ("in",)
    params = {
        "low": IntSlider(0, 255, default=80, modulatable=True),
        "high": IntSlider(0, 255, default=160, modulatable=True),
        "invert": Toggle(False),
    }

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        src = inputs.get("in")
        if src is None:
            return None
        gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY) if src.ndim == 3 else src
        lo = int(self.get("low"))
        hi = int(self.get("high"))
        if hi < lo:
            lo, hi = hi, lo
        edges = cv2.Canny(gray, lo, hi)
        if self.get("invert"):
            edges = 255 - edges
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
