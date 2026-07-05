"""HandTracker 노드 (M3, PLAN §1.3/§2) — MediaPipe HandLandmarker(21×2).

output = {"hands": [[(x,y,z)×21], ...], "w", "h"} (정규화 좌표, 구조화 데이터).
preview = 손 스켈레톤 오버레이. 모델 로드는 start()(R4), 실패 시 폴백.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.models import ensure_model
from ..core.param_spec import IntSlider, Slider
from ..core.processor import FrameCtx, Processor

_HAND_CONN = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]
_LINE = (168, 242, 125)  # BGR (cat-generate green)
_JOINT = (248, 244, 242)


class HandTracker(Processor):
    category = "vision"
    name = "HandTracker"
    kind = "hand_tracker"
    inputs = ("in",)
    params = {
        "max_hands": IntSlider(1, 2, default=2),
        "min_confidence": Slider(0.1, 0.9, default=0.5),
    }

    def __init__(self, node_id: str = "hands1", index: int = 0):
        super().__init__(node_id, index)
        self._lm = None
        self._mp = None
        self._ready = False

    def start(self) -> None:
        try:
            import mediapipe as mp
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision

            path = ensure_model("hand_landmarker.task")
            if path is None:
                return
            opts = vision.HandLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(path)),
                running_mode=vision.RunningMode.IMAGE,
                num_hands=int(self.get("max_hands")),
                min_hand_detection_confidence=float(self.get("min_confidence")),
            )
            self._lm = vision.HandLandmarker.create_from_options(opts)
            self._mp = mp
            self._ready = True
        except Exception:
            self._ready = False

    def stop(self) -> None:
        try:
            if self._lm is not None:
                self._lm.close()
        except Exception:
            pass

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[dict]:
        src = inputs.get("in")
        if src is None:
            return None
        h, w = src.shape[:2]
        out_hands = []
        prev = src.copy()
        if self._ready and self._lm is not None:
            rgb = np.ascontiguousarray(src[:, :, ::-1])
            mp_img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
            res = self._lm.detect(mp_img)
            for hand in res.hand_landmarks:
                pts = [(lm.x, lm.y, lm.z) for lm in hand]
                out_hands.append(pts)
                px = [(int(x * w), int(y * h)) for (x, y, _z) in pts]
                for a, b in _HAND_CONN:
                    cv2.line(prev, px[a], px[b], _LINE, 2, cv2.LINE_AA)
                for p in px:
                    cv2.circle(prev, p, 3, _JOINT, -1, cv2.LINE_AA)
        else:
            prev = (src.astype(np.float32) * 0.6).astype(np.uint8)  # 폴백 표시
        self.preview = prev
        return {"hands": out_hands, "w": w, "h": h}
