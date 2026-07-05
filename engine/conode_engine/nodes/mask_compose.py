"""MaskCompose 노드 (M-B, PLAN §1.3 Logic) — 두 마스크 합/차/교차 + feather."""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import Enum, IntSlider
from ..core.processor import FrameCtx, Processor


def _gray(m: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(m, cv2.COLOR_BGR2GRAY) if m.ndim == 3 else m


class MaskCompose(Processor):
    category = "depth"
    name = "MaskCompose"
    kind = "mask_compose"
    inputs = ("a", "b")
    params = {
        "op": Enum(["union", "intersect", "subtract"], default="union"),
        "feather": IntSlider(0, 60, default=0),
    }

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        a = inputs.get("a")
        b = inputs.get("b")
        if a is None and b is None:
            return None
        if a is None:
            return b
        if b is None:
            return a
        ga = _gray(a)
        gb = _gray(b)
        if ga.shape != gb.shape:
            gb = cv2.resize(gb, (ga.shape[1], ga.shape[0]))
        op = self.get("op")
        if op == "intersect":
            m = cv2.min(ga, gb)
        elif op == "subtract":
            m = cv2.subtract(ga, gb)
        else:
            m = cv2.max(ga, gb)
        k = int(self.get("feather"))
        if k > 0:
            if k % 2 == 0:
                k += 1
            m = cv2.GaussianBlur(m, (k, k), 0)
        return cv2.cvtColor(m, cv2.COLOR_GRAY2BGR)
