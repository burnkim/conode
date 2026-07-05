"""ColorGrade 노드 (M-B, PLAN §1.3 Composite) — 밝기/대비/채도/색조."""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import Slider
from ..core.processor import FrameCtx, Processor


class ColorGrade(Processor):
    category = "generate"
    name = "ColorGrade"
    kind = "color_grade"
    inputs = ("in",)
    params = {
        "brightness": Slider(-1.0, 1.0, default=0.0, modulatable=True),
        "contrast": Slider(0.0, 2.0, default=1.0, modulatable=True),
        "saturation": Slider(0.0, 2.0, default=1.0, modulatable=True),
        "hue": Slider(-90.0, 90.0, default=0.0),
    }

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        img = inputs.get("in")
        if img is None:
            return None
        c = float(self.get("contrast"))
        b = float(self.get("brightness"))
        f = (img.astype(np.float32) - 128.0) * c + 128.0 + b * 128.0
        bgr = np.clip(f, 0, 255).astype(np.uint8)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[..., 1] = np.clip(hsv[..., 1] * float(self.get("saturation")), 0, 255)
        hsv[..., 0] = (hsv[..., 0] + float(self.get("hue"))) % 180
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
