"""VideoFile 노드 (§1.3 Input) — 비디오 파일에서 프레임 재생. Camera 대체 입력.

캡처는 백그라운드 스레드(R4: tick 안 blocking I/O 금지). 파일 fps×speed 로 페이싱,
EOF 시 loop 옵션이면 되감기. 파일이 없거나 못 열면 합성 패턴으로 폴백(파일 없이도
E2E 검증 가능). 출력 = BGR numpy — 프리뷰 인코딩은 core.preview.
"""
from __future__ import annotations

import threading
import time
from typing import Optional

import cv2
import numpy as np

from ..core.latest_wins import LatestWins
from ..core.param_spec import Slider, Text, Toggle
from ..core.processor import FrameCtx, Processor


class _VideoSource:
    """파일 캡처 스레드 → LatestWins[np.ndarray] (BGR)."""

    def __init__(self, path: str = "", width: int = 320, height: int = 180):
        self.path = path
        self.width = width
        self.height = height
        self.buf: LatestWins = LatestWins()
        self.real = False
        self.speed = 1.0
        self.loop = True
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.5)

    def _loop(self) -> None:
        cap = None
        try:
            if self.path:
                cap = cv2.VideoCapture(self.path)
            if cap is not None and cap.isOpened():
                self.real = True
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                fps = fps if 1.0 <= fps <= 120.0 else 30.0
                while not self._stop.is_set():
                    r, frame = cap.read()
                    if not r or frame is None:
                        if self.loop:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        break
                    self.buf.put(cv2.resize(frame, (self.width, self.height)))
                    time.sleep(1.0 / (fps * max(0.05, self.speed)))
                if not self.loop:
                    return
        except Exception:
            self.real = False
        finally:
            if cap is not None:
                cap.release()
        self._synthetic_loop()

    def _synthetic_loop(self) -> None:
        """파일 부재/실패 시 움직이는 패턴 (no-file 표시)."""
        h, w = self.height, self.width
        xx = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
        yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
        i = 0
        while not self._stop.is_set():
            t = i * 0.04
            r = (0.5 + 0.5 * np.sin(2 * np.pi * (xx * 2 + t))) * 255.0
            g = (0.5 + 0.5 * np.sin(2 * np.pi * (yy * 2 + t * 0.6))) * 255.0
            b = (0.5 + 0.5 * np.sin(2 * np.pi * (xx + yy + t * 0.2))) * 255.0
            frame = np.dstack(
                [np.broadcast_to(b, (h, w)), np.broadcast_to(g, (h, w)), np.broadcast_to(r, (h, w))]
            ).astype(np.uint8)
            cv2.putText(frame, "no video file", (8, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            self.buf.put(frame)
            i += 1
            time.sleep(1.0 / 30.0)


class VideoFile(Processor):
    category = "input"
    name = "VideoFile"
    kind = "video_file"
    inputs = ()  # 소스 노드
    params = {
        "path": Text(default=""),
        "speed": Slider(0.1, 4.0, default=1.0),
        "loop": Toggle(True),
        "mirror": Toggle(False),
    }

    def __init__(self, node_id: str = "video1", index: int = 0, width: int = 320, height: int = 180):
        super().__init__(node_id, index)
        self.width = width
        self.height = height
        self.source = _VideoSource(path=self.get("path"), width=width, height=height)

    def start(self) -> None:
        self.source.path = self.get("path")
        self.source.speed = float(self.get("speed"))
        self.source.loop = bool(self.get("loop"))
        self.source.start()

    def stop(self) -> None:
        self.source.stop()

    @property
    def is_real(self) -> bool:
        return self.source.real

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        self.source.speed = float(self.get("speed"))  # 라이브 속도 반영
        frame = self.source.buf.get()
        if frame is None:
            return None
        if self.get("mirror"):
            frame = cv2.flip(frame, 1)
        return frame
