"""디퓨전 백엔드 추상화 (M2). 타깃은 RTX 4090(StreamDiffusion+TRT)이지만
개발기(Mac)에서는 FallbackBackend(비-ML 스타일라이즈)로 파이프라인을 검증한다.

실백엔드(T18, CUDA)는 같은 generate() 계약으로 교체된다 — 노드 코드 무변경.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np


@dataclass
class DiffusionRequest:
    image: np.ndarray  # BGR base image (img2img)
    prompt: str = ""
    negative: str = ""
    strength: float = 1.0
    steps: int = 1
    seed: int = 0
    control: Optional[np.ndarray] = None  # ControlNet conditioning (BGR)
    control_type: str = "canny"
    control_weight: float = 1.0


class DiffusionBackend:
    name = "base"
    real = False  # 실디퓨전 여부 (False = 프리뷰 스타일라이즈)

    def prepare(self) -> None:
        """모델 로드/TRT 빌드 등 무거운 준비. tick 밖에서 호출 (R4)."""

    def close(self) -> None:
        pass

    def generate(self, req: DiffusionRequest) -> np.ndarray:
        raise NotImplementedError


class FallbackBackend(DiffusionBackend):
    """Mac/CPU 프리뷰용. 실디퓨전이 아니라 파라미터에 반응하는 스타일라이즈.
    4090 배포 시 StreamDiffusionBackend 로 교체된다."""

    name = "fallback-stylize"
    real = False

    def generate(self, req: DiffusionRequest) -> np.ndarray:
        img = req.image
        try:
            styl = cv2.stylization(img, sigma_s=60, sigma_r=0.45)
        except Exception:
            styl = cv2.bilateralFilter(img, 9, 120, 120)
        # 프롬프트 → 결정적 색조 시프트 (hash 대신 ord 합: 프로세스 간 안정)
        hue = (sum(ord(c) for c in req.prompt) % 180) if req.prompt else 0
        hsv = cv2.cvtColor(styl, cv2.COLOR_BGR2HSV).astype(np.int16)
        hsv[..., 0] = (hsv[..., 0] + hue) % 180
        tinted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        # ControlNet 프리뷰: control 엣지를 밝게 오버레이
        if req.control is not None and req.control_weight > 0:
            c = req.control if req.control.ndim == 3 else cv2.cvtColor(req.control, cv2.COLOR_GRAY2BGR)
            c = cv2.resize(c, (tinted.shape[1], tinted.shape[0]))
            tinted = cv2.addWeighted(tinted, 1.0, c, min(0.6, req.control_weight * 0.3), 0)
        a = min(1.0, req.strength / 2.0 + 0.3)
        return cv2.addWeighted(tinted, a, img, 1.0 - a, 0)


def select_backend(config=None) -> DiffusionBackend:
    """가용 백엔드 선택. CUDA(4090)면 StreamDiffusion+LCM, 아니면 Fallback(Mac).
    torch/CUDA 미존재 시 조용히 Fallback 으로 우회한다."""
    try:
        import torch  # Mac 개발기엔 미설치 → ImportError → Fallback

        if torch.cuda.is_available():
            from .streamdiffusion_backend import StreamDiffusionBackend

            return StreamDiffusionBackend(config)
    except Exception:
        pass
    return FallbackBackend()
