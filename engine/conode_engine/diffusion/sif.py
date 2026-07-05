"""Similar Image Filter (M2, PLAN §1.2 advanced) — 연속 프레임이 충분히 비슷하면
디퓨전을 건너뛰어 지연 누적을 막는다(최대 sif_max_skip 프레임 연속 스킵).
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


class SimilarImageFilter:
    def __init__(self, threshold: float = 0.9, max_skip: int = 15):
        self.threshold = threshold
        self.max_skip = max_skip
        self._prev: Optional[np.ndarray] = None
        self._skips = 0

    def _similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        if a.shape != b.shape:
            b = cv2.resize(b, (a.shape[1], a.shape[0]))
        diff = np.abs(a.astype(np.int16) - b.astype(np.int16)).mean()
        return 1.0 - float(diff) / 255.0

    def should_skip(self, frame: np.ndarray) -> bool:
        """True 면 디퓨전 스킵(직전 결과 재사용). 상태를 갱신한다."""
        if self._prev is None:
            self._prev = frame.copy()
            self._skips = 0
            return False
        sim = self._similarity(self._prev, frame)
        if sim >= self.threshold and self._skips < self.max_skip:
            self._skips += 1
            return True
        self._prev = frame.copy()
        self._skips = 0
        return False

    def reset(self) -> None:
        self._prev = None
        self._skips = 0
