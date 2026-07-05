"""오디오 특성 추출 (M4, PLAN §3.2) — 채널당 rms/peak/onset/centroid/flux/band.

numpy FFT 사용(scipy 불필요). 절대 레벨이 변하는 특성(onset/flux/band)은 running-max
적응 정규화로 0..1 스팬. rms/peak/centroid 는 본래 0..1.
"""
from __future__ import annotations

import numpy as np

FEATURES = ["rms", "peak", "onset", "centroid", "flux", "low", "mid", "high"]
_ABSOLUTE = {"rms", "peak", "centroid"}  # 이미 0..1


class FeatureExtractor:
    """한 채널의 연속 블록에서 특성을 뽑는다(상태: 이전 스펙트럼 + 적응 정규화)."""

    def __init__(self, samplerate: int = 48000, decay: float = 0.995):
        self.sr = samplerate
        self.decay = decay
        self._prev_mag: np.ndarray | None = None
        self._norm = {f: 1e-6 for f in FEATURES}

    def extract(self, block: np.ndarray) -> dict[str, float]:
        x = np.asarray(block, dtype=np.float32).ravel()
        n = x.size
        if n == 0:
            return {f: 0.0 for f in FEATURES}
        rms = float(np.sqrt(np.mean(x * x)))
        peak = float(np.max(np.abs(x)))

        win = x * np.hanning(n) if n > 1 else x
        mag = np.abs(np.fft.rfft(win))
        freqs = np.fft.rfftfreq(n, 1.0 / self.sr)
        total = float(mag.sum()) + 1e-9
        centroid = float((freqs * mag).sum() / total / (self.sr / 2.0))

        if self._prev_mag is not None and self._prev_mag.shape == mag.shape:
            flux = float(np.sum(np.maximum(mag - self._prev_mag, 0.0)))
        else:
            flux = 0.0
        self._prev_mag = mag

        low = float(mag[freqs < 250].sum())
        mid = float(mag[(freqs >= 250) & (freqs < 2000)].sum())
        high = float(mag[freqs >= 2000].sum())

        raw = {
            "rms": rms, "peak": peak, "onset": flux, "centroid": centroid,
            "flux": flux, "low": low, "mid": mid, "high": high,
        }
        out = {}
        for f, v in raw.items():
            if f in _ABSOLUTE:
                out[f] = min(1.0, max(0.0, v))
            else:
                self._norm[f] = max(v, self._norm[f] * self.decay, 1e-6)
                out[f] = min(1.0, v / self._norm[f])
        return out
