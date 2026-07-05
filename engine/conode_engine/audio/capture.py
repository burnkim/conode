"""오디오 캡처 (M4, PLAN §3.1) — 멀티채널 디바이스(loopback) 또는 12스템 합성.

v1 실전은 DAW loopback(BlackHole 등)으로 12ch 수신. 개발/데모는 합성 12스템(스템별
다른 톤+리듬)으로 ModMatrix 를 검증한다. 캡처는 백그라운드(R4).
"""
from __future__ import annotations

import threading
import time
from typing import Optional

import numpy as np


class AudioCapture:
    def __init__(
        self,
        channels: int = 12,
        samplerate: int = 48000,
        blocksize: int = 1024,
        mode: str = "synth",
        device: Optional[int] = None,
    ):
        self.channels = channels
        self.sr = samplerate
        self.blocksize = blocksize
        self.mode = mode
        self.device = device
        self.real = False
        self.latest = np.zeros((channels, blocksize), np.float32)
        self._stream = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._t = 0
        self._rng = np.random.default_rng(0)

    def start(self) -> None:
        if self.mode == "device":
            try:
                import sounddevice as sd

                info = sd.query_devices(kind="input")
                dev_ch = max(1, min(self.channels, int(info["max_input_channels"])))
                self._dev_ch = dev_ch
                self._stream = sd.InputStream(
                    channels=dev_ch,
                    samplerate=self.sr,
                    blocksize=self.blocksize,
                    callback=self._cb,
                    device=self.device,
                )
                self._stream.start()
                self.real = True
                return
            except Exception:
                self.real = False
        self._thread = threading.Thread(target=self._synth_loop, daemon=True)
        self._thread.start()

    def _cb(self, indata, frames, time_info, status) -> None:
        d = np.asarray(indata, dtype=np.float32).T  # (dev_ch, frames)
        buf = np.zeros((self.channels, self.blocksize), np.float32)
        m = min(d.shape[0], self.channels)
        f = min(d.shape[1], self.blocksize)
        buf[:m, :f] = d[:m, :f]
        self.latest = buf

    def _synth_loop(self) -> None:
        while not self._stop.is_set():
            self.latest = self._synth_block()
            self._t += self.blocksize
            time.sleep(self.blocksize / self.sr)

    def _synth_block(self) -> np.ndarray:
        t = (self._t + np.arange(self.blocksize)) / self.sr
        out = np.zeros((self.channels, self.blocksize), np.float32)
        for c in range(self.channels):
            freq = 55.0 * (c + 1)
            rate = 0.5 + c * 0.35  # 스템별 다른 리듬
            env = 0.5 + 0.5 * np.sin(2 * np.pi * rate * t)
            if c % 4 == 1:  # hats 계열 = 노이즈
                sig = self._rng.standard_normal(self.blocksize).astype(np.float32) * 0.5
            else:
                sig = np.sin(2 * np.pi * freq * t).astype(np.float32)
            out[c] = (sig * env * 0.5).astype(np.float32)
        return out

    def get(self) -> np.ndarray:
        return self.latest

    def stop(self) -> None:
        self._stop.set()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=1.0)
