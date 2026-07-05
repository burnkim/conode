"""Image 노드 (M-B, PLAN §1.3 Input) — 정적 이미지 또는 컬러바 테스트 패턴."""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import IntSlider, Text, Toggle
from ..core.processor import FrameCtx, Processor

_BARS = [
    (255, 255, 255), (0, 255, 255), (255, 255, 0), (0, 255, 0),
    (255, 0, 255), (0, 0, 255), (255, 0, 0), (30, 30, 30),
]


class Image(Processor):
    category = "input"
    name = "Image"
    kind = "image"
    inputs = ()
    params = {
        "path": Text(default=""),
        "test_pattern": Toggle(True),
        "width": IntSlider(64, 1920, default=320),
        "height": IntSlider(64, 1080, default=180),
    }

    def __init__(self, node_id: str = "image1", index: int = 0):
        super().__init__(node_id, index)
        self._img: Optional[np.ndarray] = None
        self._loaded = ""

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        w, h = int(self.get("width")), int(self.get("height"))
        path = self.get("path")
        if path and path != self._loaded:
            img = cv2.imread(path)
            self._img = cv2.resize(img, (w, h)) if img is not None else None
            self._loaded = path
        if self._img is not None:
            return self._img
        if self.get("test_pattern"):
            bars = np.zeros((h, w, 3), np.uint8)
            bw = max(1, w // len(_BARS))
            for i, c in enumerate(_BARS):
                bars[:, i * bw : (i + 1) * bw] = c
            return bars
        return np.zeros((h, w, 3), np.uint8)
