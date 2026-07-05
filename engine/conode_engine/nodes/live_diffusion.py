"""LiveDiffusion 노드 (M2, PLAN §1.2 CkDiffusion 상당 / §1.3 Generate).

포트: in(베이스), control(ControlNet 컨디셔닝), mask(RegionMask — 마스크 영역만 치환, §2).
백엔드는 추상화(diffusion.backend): 4090=StreamDiffusion+TRT, Mac=Fallback 스타일라이즈.
SIF(advanced)로 유사 프레임은 디퓨전 스킵. 모델/백엔드 준비는 start()(R4).
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from ..core.param_spec import (
    Enum,
    Group,
    IntSlider,
    MultiMarkerSlider,
    Seed,
    Slider,
    Text,
    Toggle,
)
from ..core.processor import FrameCtx, Processor
from ..diffusion.backend import DiffusionRequest, select_backend
from ..diffusion.sif import SimilarImageFilter


class LiveDiffusion(Processor):
    category = "generate"
    name = "LiveDiffusion"
    kind = "live_diffusion"
    inputs = ("in", "control", "mask")
    params = {
        "prompt": Text(default="a field of stars, geometric", multiline=True),
        "negative": Text(default="blurry, low quality"),
        "prompt_strength": Slider(0.0, 2.0, default=1.0, modulatable=True),
        "seed": Seed(mode=["random", "fixed"], default=1234),
        "creativity": MultiMarkerSlider(0, 50, markers=[10, 35, 49]),  # denoise steps
        "controlnet": Group(
            {
                "enable": Toggle(True),
                "type": Enum(["self", "pose", "depth", "canny", "seg"], default="canny"),
                "weight": Slider(0.0, 2.0, default=1.0, modulatable=True),
            }
        ),
        "advanced": Group(
            {
                "noise": Toggle(False),
                "denoising_batch": Toggle(True),
                "similar_image_filter": Toggle(True),
                "sif_threshold": Slider(0.0, 1.0, default=0.9),
                "sif_max_skip": IntSlider(1, 60, default=15),
            }
        ),
    }

    def __init__(self, node_id: str = "live1", index: int = 0):
        super().__init__(node_id, index)
        self._backend = None
        self._sif = SimilarImageFilter()
        self._last: Optional[np.ndarray] = None

    def start(self) -> None:
        self._backend = select_backend()
        self._backend.prepare()

    def stop(self) -> None:
        if self._backend is not None:
            self._backend.close()

    @property
    def backend_name(self) -> str:
        return self._backend.name if self._backend else "(none)"

    def process(self, ctx: FrameCtx, inputs: dict) -> Optional[np.ndarray]:
        img = inputs.get("in")
        if img is None:
            return None
        if self._backend is None:
            self.start()

        # Similar Image Filter — 유사 프레임이면 직전 결과 재사용
        if self.get("advanced.similar_image_filter"):
            self._sif.threshold = float(self.get("advanced.sif_threshold"))
            self._sif.max_skip = int(self.get("advanced.sif_max_skip"))
            if self._last is not None and self._sif.should_skip(img):
                return self._last

        control = inputs.get("control") if self.get("controlnet.enable") else None
        markers = self.get("creativity")
        req = DiffusionRequest(
            image=img,
            prompt=self.get("prompt"),
            negative=self.get("negative"),
            strength=float(self.get("prompt_strength")),
            steps=len(markers) if markers else 1,
            seed=int(self.get("seed")),
            control=control,
            control_type=self.get("controlnet.type"),
            control_weight=float(self.get("controlnet.weight")),
        )
        out = self._backend.generate(req)

        # RegionApply — mask 영역만 디퓨전 결과로 치환 (§2)
        mask = inputs.get("mask")
        if mask is not None:
            m = mask if mask.ndim == 2 else cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
            m = cv2.resize(m, (img.shape[1], img.shape[0]))
            sel = (m > 127)[:, :, None]
            out = np.where(sel, out, img).astype(np.uint8)

        self._last = out
        return out
