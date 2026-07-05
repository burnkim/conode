"""Crossfade 노드 (M-B, PLAN §1.3 Logic) — 두 입력 사이 위치(pos) 크로스페이드.

pos 는 modulatable — 큐/씬 전환, 오디오/제스처로 페이드 제어.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import Slider
from ..core.processor import FrameCtx, Processor


class Crossfade(Processor):
    category = "generate"
    name = "Crossfade"
    kind = "crossfade"
    inputs = ("a", "b")
    params = {
        "pos": Slider(0.0, 1.0, default=0.0, modulatable=True),  # 0=a, 1=b
    }

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        a = inputs.get("a")
        b = inputs.get("b")
        p = float(self.get("pos"))
        if a is None:
            return b
        if b is None:
            return a
        if a.shape != b.shape:
            b = cv2.resize(b, (a.shape[1], a.shape[0]))
        return cv2.addWeighted(a, 1.0 - p, b, p, 0)
