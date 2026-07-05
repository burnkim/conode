"""preview — 노드 output(numpy 프레임) → base64 JPEG (프리뷰 전송용, PLAN §1.1).

프레임 경로와 프리뷰 경로를 분리한다: 노드는 numpy 를 출력하고(다운스트림이 소비),
프리뷰는 여기서만 인코딩한다. 최종 출력은 UI 경유 금지(R5) — 이건 프리뷰 전용.
"""
from __future__ import annotations

import base64
from typing import Optional

import cv2
import numpy as np


def encode_jpeg(frame: Optional[np.ndarray], quality: int = 70) -> Optional[str]:
    if frame is None:
        return None
    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    ok, enc = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return None
    return base64.b64encode(enc.tobytes()).decode("ascii")


def frame_size(frame: Optional[np.ndarray]) -> tuple[int, int]:
    if frame is None:
        return (0, 0)
    h, w = frame.shape[:2]
    return (int(w), int(h))
