"""Depth 노드 (T11) — PLAN §1.3 Vision. v1 근사(모델 미사용).

밝기/블러 기반 의사 깊이 + 컬러맵. 실모델(DepthAnythingV2 등)은 RTX 타깃/M2에서
process() 만 교체하면 되도록 인터페이스 고정.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import IntSlider, Toggle
from ..core.processor import FrameCtx, Processor


class Depth(Processor):
    category = "depth"
    name = "DepthMap"
    kind = "depth"
    inputs = ("in",)
    params = {
        "blur": IntSlider(1, 31, default=9),
        "colormap": Toggle(True),
        "invert": Toggle(False),
    }

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        src = inputs.get("in")
        if src is None:
            return None
        gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY) if src.ndim == 3 else src
        k = int(self.get("blur"))
        if k % 2 == 0:
            k += 1
        blurred = cv2.GaussianBlur(gray, (k, k), 0)
        depth = cv2.normalize(blurred, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        if self.get("invert"):
            depth = 255 - depth
        if self.get("colormap"):
            return cv2.applyColorMap(depth, cv2.COLORMAP_INFERNO)
        return cv2.cvtColor(depth, cv2.COLOR_GRAY2BGR)
