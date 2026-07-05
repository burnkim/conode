"""Segmentation 노드 (T12) — PLAN §1.3 Vision. MediaPipe SelfieSegmenter(Tasks API).

모델 로드는 start()(R4). 실패 시 폴백(중앙 가중 근사 마스크). person confidence 마스크로
mask/cutout/blur_bg 합성.
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.models import ensure_model
from ..core.param_spec import Enum, Slider
from ..core.processor import FrameCtx, Processor


class Segmentation(Processor):
    category = "vision"
    name = "Segmentation"
    inputs = ("in",)
    params = {
        "threshold": Slider(0.1, 0.9, default=0.5),
        "mode": Enum(["cutout", "mask", "blur_bg"], default="cutout"),
    }

    def __init__(self, node_id: str = "seg1", index: int = 0):
        super().__init__(node_id, index)
        self._seg = None
        self._mp = None
        self._ready = False

    def start(self) -> None:
        try:
            import mediapipe as mp
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision

            path = ensure_model("selfie_segmenter.tflite")
            if path is None:
                return
            opts = vision.ImageSegmenterOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(path)),
                running_mode=vision.RunningMode.IMAGE,
                output_confidence_masks=True,
            )
            self._seg = vision.ImageSegmenter.create_from_options(opts)
            self._mp = mp
            self._ready = True
        except Exception:
            self._ready = False

    def stop(self) -> None:
        try:
            if self._seg is not None:
                self._seg.close()
        except Exception:
            pass

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        src = inputs.get("in")
        if src is None:
            return None
        thr = float(self.get("threshold"))
        if not self._ready or self._seg is None:
            person = self._fallback_mask(src)
        else:
            rgb = np.ascontiguousarray(src[:, :, ::-1])
            mp_img = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
            res = self._seg.segment(mp_img)
            mask = np.asarray(res.confidence_masks[0].numpy_view())
            if mask.ndim == 3:
                mask = mask[:, :, 0]  # (H,W,1) → (H,W)
            person = (mask >= thr).astype(np.uint8)
        return self._composite(src, person, self.get("mode"))

    def _composite(self, src: np.ndarray, person: np.ndarray, mode: str) -> np.ndarray:
        if mode == "mask":
            return cv2.cvtColor((person * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        m3 = person[:, :, None]
        if mode == "blur_bg":
            bg = cv2.GaussianBlur(src, (0, 0), 8)
        else:  # cutout
            bg = (src.astype(np.float32) * 0.15).astype(np.uint8)
        return np.where(m3 == 1, src, bg).astype(np.uint8)

    def _fallback_mask(self, src: np.ndarray) -> np.ndarray:
        h, w = src.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        d = ((xx - w / 2) / (w * 0.4)) ** 2 + ((yy - h / 2) / (h * 0.5)) ** 2
        return (d < 1.0).astype(np.uint8)
