"""AudioIn 노드 (M4, PLAN §3) — 멀티채널 캡처 → 채널별 특성.

output = {"stems": [{rms,peak,onset,centroid,flux,low,mid,high} × N], "n": N}.
ModMatrix 가 stemN.feature 소스로 읽는다. preview = 스템 rms 미터.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..audio.capture import AudioCapture
from ..audio.features import FEATURES, FeatureExtractor
from ..core.param_spec import Enum, IntSlider, Slider
from ..core.processor import FrameCtx, Processor


class AudioIn(Processor):
    category = "audio"
    name = "AudioIn"
    kind = "audio_in"
    inputs = ()
    params = {
        "source": Enum(["synth", "device"], default="synth"),
        "channels": IntSlider(1, 12, default=12),
        "gain": Slider(0.0, 4.0, default=1.0),
    }

    def __init__(self, node_id: str = "audio1", index: int = 0):
        super().__init__(node_id, index)
        self._cap: Optional[AudioCapture] = None
        self._ext: list[FeatureExtractor] = []

    def start(self) -> None:
        ch = int(self.get("channels"))
        self._cap = AudioCapture(channels=ch, mode=self.get("source"))
        self._ext = [FeatureExtractor(samplerate=self._cap.sr) for _ in range(ch)]
        self._cap.start()

    def stop(self) -> None:
        if self._cap is not None:
            self._cap.stop()

    @property
    def is_real(self) -> bool:
        return bool(self._cap and self._cap.real)

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[dict]:
        if self._cap is None:
            self.start()
        block = self._cap.get() * float(self.get("gain"))
        n = min(len(self._ext), block.shape[0])
        stems = [self._ext[c].extract(block[c]) for c in range(n)]
        self.preview = self._meter(stems)
        return {"stems": stems, "n": n}

    def _meter(self, stems: list[dict]) -> np.ndarray:
        w, h = 320, 180
        canvas = np.zeros((h, w, 3), np.uint8)
        col = (242, 156, 184)  # cat-audio (BGR of #B89CF2)
        n = max(1, len(stems))
        bw = w // n
        for i, s in enumerate(stems):
            bh = int(s.get("rms", 0.0) * h)
            x0 = i * bw
            cv2.rectangle(canvas, (x0 + 1, h - bh), (x0 + bw - 2, h), col, -1)
        return canvas
