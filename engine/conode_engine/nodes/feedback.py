"""FeedbackLoop 노드 (M-B, PLAN §1.3 Composite) — 이전 출력을 워프+블렌드 (트레일/에코)."""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import Slider
from ..core.processor import FrameCtx, Processor


class FeedbackLoop(Processor):
    category = "generate"
    name = "FeedbackLoop"
    kind = "feedback"
    inputs = ("in",)
    params = {
        "feedback": Slider(0.0, 0.98, default=0.7, modulatable=True),
        "zoom": Slider(0.9, 1.1, default=1.0),
        "rotate": Slider(-5.0, 5.0, default=0.0, modulatable=True),
    }

    def __init__(self, node_id: str = "feedback1", index: int = 0):
        super().__init__(node_id, index)
        self._prev: Optional[np.ndarray] = None

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        img = inputs.get("in")
        if img is None:
            return None
        if self._prev is None or self._prev.shape != img.shape:
            self._prev = np.zeros_like(img)
        h, w = img.shape[:2]
        mat = cv2.getRotationMatrix2D((w / 2, h / 2), float(self.get("rotate")), float(self.get("zoom")))
        warped = cv2.warpAffine(self._prev, mat, (w, h))
        fb = float(self.get("feedback"))
        out = cv2.addWeighted(img, 1.0 - fb, warped, fb, 0)
        self._prev = out
        return out
