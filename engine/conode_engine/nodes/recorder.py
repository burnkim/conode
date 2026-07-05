"""Recorder 노드 (M5, PLAN §4) — 입력 프레임을 비디오 파일로 기록.

record 토글 ON 시 cv2.VideoWriter 로 recordings/ 에 저장(gitignore). passthrough +
프리뷰에 REC 표시. 최종 출력은 엔진이 직접 낸다(R5) — 여긴 파일 기록.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import IntSlider, Text, Toggle
from ..core.processor import FrameCtx, Processor

_REC_DIR = Path(__file__).resolve().parents[2] / "recordings"


class Recorder(Processor):
    category = "output"
    name = "Recorder"
    kind = "recorder"
    inputs = ("in",)
    params = {
        "record": Toggle(False),
        "fps": IntSlider(1, 60, default=30),
        "filename": Text(default="out.mp4"),
    }

    def __init__(self, node_id: str = "rec1", index: int = 0):
        super().__init__(node_id, index)
        self._writer = None
        self._frames = 0

    def stop(self) -> None:
        self._close()

    def _close(self) -> None:
        if self._writer is not None:
            self._writer.release()
            self._writer = None

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        src = inputs.get("in")
        if src is None:
            return None
        recording = bool(self.get("record"))
        if recording:
            if self._writer is None:
                _REC_DIR.mkdir(parents=True, exist_ok=True)
                h, w = src.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                path = str(_REC_DIR / str(self.get("filename")))
                self._writer = cv2.VideoWriter(path, fourcc, float(self.get("fps")), (w, h))
                self._frames = 0
            self._writer.write(src)
            self._frames += 1
        else:
            self._close()

        out = src.copy()
        if recording:
            cv2.circle(out, (14, 14), 6, (0, 0, 255), -1)  # REC dot
            cv2.putText(out, f"REC {self._frames}", (26, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        return out
