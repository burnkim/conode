"""Blend 노드 (M-B, PLAN §1.3 Composite) — 두 입력 합성(mix/add/multiply/screen)."""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import Enum, Slider
from ..core.processor import FrameCtx, Processor


class Blend(Processor):
    category = "generate"
    name = "Blend"
    kind = "blend"
    inputs = ("a", "b")
    params = {
        "mix": Slider(0.0, 1.0, default=0.5, modulatable=True),
        "mode": Enum(["mix", "add", "multiply", "screen"], default="mix"),
    }

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        a = inputs.get("a")
        b = inputs.get("b")
        if a is None:
            return b
        if b is None:
            return a
        if a.shape != b.shape:
            b = cv2.resize(b, (a.shape[1], a.shape[0]))
        m = float(self.get("mix"))
        af, bf = a.astype(np.float32), b.astype(np.float32)
        mode = self.get("mode")
        if mode == "add":
            out = af + bf * m
        elif mode == "multiply":
            out = af * (bf / 255.0 * m + (1.0 - m))
        elif mode == "screen":
            out = 255.0 - (255.0 - af) * (255.0 - bf * m) / 255.0
        else:
            out = af * (1.0 - m) + bf * m
        return np.clip(out, 0, 255).astype(np.uint8)
