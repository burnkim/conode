"""Camera 노드 (T6) — PLAN §1.3 Input.

캡처는 백그라운드 스레드에서 (R4: tick() 안 blocking I/O 금지). tick/process 는
LatestWins 에서 최신 프레임만 꺼내 JPEG 인코딩 → base64. 실카메라 열기에 실패하면
움직이는 합성 패턴으로 폴백(무대/헤드리스 환경에서도 E2E 검증 가능).
"""
from __future__ import annotations

import base64
import threading
import time
from typing import Optional

import cv2
import numpy as np

from ..core.latest_wins import LatestWins
from ..core.param_spec import IntSlider, Slider, Toggle
from ..core.processor import FrameCtx, Processor


class _CameraSource:
    """디바이스 캡처 스레드 → LatestWins[np.ndarray] (BGR)."""

    def __init__(self, device: int = 0, width: int = 320, height: int = 180):
        self.device = device
        self.width = width
        self.height = height
        self.buf: LatestWins = LatestWins()
        self.real = False
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
            cap = cv2.VideoCapture(self.device)
            ok = False
            t0 = time.monotonic()
            while time.monotonic() - t0 < 1.5 and not self._stop.is_set():
                r, frame = cap.read()
                if r and frame is not None:
                    ok = True
                    break
                time.sleep(0.05)
            self.real = ok
            if ok:
                while not self._stop.is_set():
                    r, frame = cap.read()
                    if r and frame is not None:
                        self.buf.put(cv2.resize(frame, (self.width, self.height)))
                    else:
                        time.sleep(0.01)
                return
        except Exception:
            self.real = False
        finally:
            if cap is not None:
                cap.release()
        self._synthetic_loop()

    def _synthetic_loop(self) -> None:
        """실카메라 부재 시 움직이는 그라디언트 패턴 (~30fps)."""
        h, w = self.height, self.width
        xx = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
        yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
        i = 0
        while not self._stop.is_set():
            t = i * 0.05
            b = (0.5 + 0.5 * np.sin(2 * np.pi * (xx + t))) * 255.0
            g = (0.5 + 0.5 * np.sin(2 * np.pi * (yy + t * 0.7))) * 255.0
            r = (0.5 + 0.5 * np.sin(2 * np.pi * (xx + yy + t * 0.3))) * 255.0
            frame = np.dstack(
                [np.broadcast_to(b, (h, w)), np.broadcast_to(g, (h, w)), np.broadcast_to(r, (h, w))]
            ).astype(np.uint8)
            self.buf.put(frame)
            i += 1
            time.sleep(1.0 / 30.0)


class Camera(Processor):
    category = "input"
    name = "Camera"
    params = {
        "device": IntSlider(0, 8, default=0),
        "exposure": Slider(0.0, 1.0, default=0.5, modulatable=True),
        "mirror": Toggle(True),
    }

    def __init__(self, node_id: str = "cam1", index: int = 1, width: int = 320, height: int = 180):
        super().__init__(node_id, index)
        self.width = width
        self.height = height
        self.source = _CameraSource(device=int(self.get("device")), width=width, height=height)
        self.last_jpeg_b64: Optional[str] = None

    def start(self) -> None:
        self.source.start()

    def stop(self) -> None:
        self.source.stop()

    @property
    def is_real(self) -> bool:
        return self.source.real

    def process(self, ctx: FrameCtx) -> Optional[str]:
        frame = self.source.buf.get()
        if frame is None:
            return None
        if self.get("mirror"):
            frame = cv2.flip(frame, 1)
        exposure = float(self.get("exposure"))
        if abs(exposure - 0.5) > 1e-3:
            frame = np.clip(frame.astype(np.float32) * (0.4 + 1.2 * exposure), 0, 255).astype(np.uint8)
        ok, enc = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if not ok:
            return None
        self.last_jpeg_b64 = base64.b64encode(enc.tobytes()).decode("ascii")
        return self.last_jpeg_b64
