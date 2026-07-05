"""RegionMask 노드 (M3, PLAN §2) — 제스처 state → 마스크(BGR white on black).

사각/원형 마스크, one-euro 관성 스무딩(떨림 방지), feather(가장자리 부드럽게).
출력 마스크는 LiveDiffusion.mask 포트로 들어가 영역만 디퓨전(§2 RegionApply).
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import Enum, IntSlider, Slider
from ..core.processor import FrameCtx, Processor
from ..gesture.one_euro import OneEuroVec


class RegionMask(Processor):
    category = "depth"
    name = "RegionMask"
    kind = "region_mask"
    inputs = ("gesture",)
    params = {
        "width": IntSlider(64, 1024, default=320),
        "height": IntSlider(64, 1024, default=180),
        "feather": IntSlider(0, 60, default=12),
        "responsiveness": Slider(0.3, 5.0, default=1.0),  # 낮을수록 관성↑
        "no_gesture": Enum(["full", "none"], default="full"),
    }

    def __init__(self, node_id: str = "region1", index: int = 0):
        super().__init__(node_id, index)
        self._rect_f = OneEuroVec(4, freq=30.0, min_cutoff=1.0, beta=0.02)
        self._circle_f = OneEuroVec(3, freq=30.0, min_cutoff=1.0, beta=0.02)
        self._active = ""

    def _set_cutoff(self, mc: float) -> None:
        for f in self._rect_f._f + self._circle_f._f:
            f.min_cutoff = mc

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        w = int(self.get("width"))
        h = int(self.get("height"))
        self._set_cutoff(float(self.get("responsiveness")))
        state = inputs.get("gesture") if isinstance(inputs.get("gesture"), dict) else None
        mask = np.zeros((h, w), np.uint8)

        gtype = state["type"] if state else "none"
        if gtype != self._active:  # 제스처가 바뀌면 필터 리셋(스냅)
            self._rect_f.reset()
            self._circle_f.reset()
            self._active = gtype

        if state and state.get("rect"):
            x0, y0, x1, y1 = self._rect_f(state["rect"])
            cv2.rectangle(mask, (int(x0 * w), int(y0 * h)), (int(x1 * w), int(y1 * h)), 255, -1)
        elif state and state.get("circle"):
            cx, cy, r = self._circle_f(state["circle"])
            cv2.circle(mask, (int(cx * w), int(cy * h)), int(r * min(w, h)), 255, -1)
        elif self.get("no_gesture") == "full":
            mask[:] = 255  # 제스처 없으면 전체(디퓨전 항상 켜짐)

        k = int(self.get("feather"))
        if k > 0:
            if k % 2 == 0:
                k += 1
            mask = cv2.GaussianBlur(mask, (k, k), 0)
        return cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
