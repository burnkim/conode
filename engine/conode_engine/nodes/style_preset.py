"""StylePreset 노드 (M-B, PLAN §1.3 Generate) — 비-ML 스타일 프리셋(cv2)."""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import Enum, Slider
from ..core.processor import FrameCtx, Processor


class StylePreset(Processor):
    category = "generate"
    name = "StylePreset"
    kind = "style_preset"
    inputs = ("in",)
    params = {
        "preset": Enum(["ink", "neon", "posterize", "pencil", "none"], default="ink"),
        "amount": Slider(0.0, 1.0, default=0.7, modulatable=True),
    }

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        img = inputs.get("in")
        if img is None:
            return None
        preset = self.get("preset")
        styled = img
        try:
            if preset == "ink":
                styled = cv2.stylization(img, sigma_s=60, sigma_r=0.45)
            elif preset == "neon":
                edges = cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 60, 160)
                styled = cv2.applyColorMap(edges, cv2.COLORMAP_COOL)
            elif preset == "posterize":
                styled = (img // 64) * 64 + 32
            elif preset == "pencil":
                _gray, styled = cv2.pencilSketch(img, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
        except Exception:
            styled = img
        if preset == "none":
            return img
        a = float(self.get("amount"))
        return cv2.addWeighted(styled, a, img, 1.0 - a, 0)
