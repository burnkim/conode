"""Pose 노드 (T10) — PLAN §1.3 Vision. MediaPipe PoseLandmarker(Tasks API).

모델 로드는 start()에서(R4). 실패 시 폴백(입력을 어둡게 반환). detect 는 tick 안의
연산(허용). 스켈레톤을 입력 프레임 위에 오버레이한다.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.models import ensure_model
from ..core.param_spec import Slider, Toggle
from ..core.processor import FrameCtx, Processor

# BlazePose 33 포인트 중 몸통/팔다리 연결 (오버레이용)
_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (24, 26), (26, 28),
    (27, 31), (28, 32), (15, 19), (16, 20),
    (0, 11), (0, 12),
]
_LINE = (0, 255, 0)   # BGR green
_JOINT = (248, 244, 242)  # near-white


class Pose(Processor):
    category = "vision"
    name = "Pose"
    kind = "pose"
    inputs = ("in",)
    params = {
        "min_confidence": Slider(0.1, 0.9, default=0.5),
        "overlay": Toggle(True),
    }

    def __init__(self, node_id: str = "pose1", index: int = 0):
        super().__init__(node_id, index)
        self._lm = None
        self._mp = None
        self._ready = False

    def start(self) -> None:
        try:
            import mediapipe as mp
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision

            path = ensure_model("pose_landmarker_lite.task")
            if path is None:
                return
            opts = vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(path)),
                running_mode=vision.RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=float(self.get("min_confidence")),
            )
            self._lm = vision.PoseLandmarker.create_from_options(opts)
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

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        src = inputs.get("in")
        if src is None:
            return None
        if not self._ready or self._lm is None:
            return (src.astype(np.float32) * 0.6).astype(np.uint8)  # 폴백: 모델 없음
        out = src.copy()
        rgb = np.ascontiguousarray(src[:, :, ::-1])
        mp_img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        res = self._lm.detect(mp_img)
        if self.get("overlay") and res.pose_landmarks:
            h, w = out.shape[:2]
            for lms in res.pose_landmarks:
                pts = [(int(l.x * w), int(l.y * h)) for l in lms]
                for a, b in _CONNECTIONS:
                    if a < len(pts) and b < len(pts):
                        cv2.line(out, pts[a], pts[b], _LINE, 2, cv2.LINE_AA)
                for p in pts:
                    cv2.circle(out, p, 3, _JOINT, -1, cv2.LINE_AA)
        return out
