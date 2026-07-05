"""One-Euro Filter (M3) — 마스크/좌표 지터 제거 + 관성. PLAN §2.

저속에선 지터 억제(정확), 고속에선 지연 최소(반응). 마커/좌표에 채널별로 적용.
"""
from __future__ import annotations

import math
from typing import Sequence


class OneEuroFilter:
    def __init__(self, freq: float = 30.0, min_cutoff: float = 1.0, beta: float = 0.02, d_cutoff: float = 1.0):
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._x_prev: float | None = None
        self._dx_prev = 0.0

    def _alpha(self, cutoff: float) -> float:
        tau = 1.0 / (2 * math.pi * cutoff)
        te = 1.0 / self.freq
        return 1.0 / (1.0 + tau / te)

    def __call__(self, x: float) -> float:
        if self._x_prev is None:
            self._x_prev = x
            return x
        dx = (x - self._x_prev) * self.freq
        a_d = self._alpha(self.d_cutoff)
        dx_hat = a_d * dx + (1 - a_d) * self._dx_prev
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._alpha(cutoff)
        x_hat = a * x + (1 - a) * self._x_prev
        self._x_prev = x_hat
        self._dx_prev = dx_hat
        return x_hat

    def reset(self) -> None:
        self._x_prev = None
        self._dx_prev = 0.0


class OneEuroVec:
    """벡터(rect/point 등)를 채널별 OneEuroFilter 로 스무딩."""

    def __init__(self, n: int, **kw):
        self._f = [OneEuroFilter(**kw) for _ in range(n)]

    def __call__(self, vec: Sequence[float]) -> list[float]:
        return [self._f[i](v) for i, v in enumerate(vec)]

    def reset(self) -> None:
        for f in self._f:
            f.reset()
