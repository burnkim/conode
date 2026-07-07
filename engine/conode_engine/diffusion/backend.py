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
    """CPU/저사양 프리뷰용(potato 티어). 실디퓨전이 아니라 파라미터에 반응하는
    스타일라이즈. profile.width/height 저해상도로 작업해 "아주 저크기·저비용"으로
    돌린 뒤 입력 크기로 업스케일한다. 상위 티어에서는 Diffusers/StreamDiffusion 으로 교체."""

    name = "fallback-stylize"
    real = False

    def __init__(self, profile=None):
        self.profile = profile

    def generate(self, req: DiffusionRequest) -> np.ndarray:
        img = req.image
        H, W = img.shape[:2]
        # 저크기 작업 해상도 (profile 있으면 그 크기, 없으면 입력 그대로)
        if self.profile is not None:
            wk = cv2.resize(img, (self.profile.width, self.profile.height))
        else:
            wk = img
        try:
            styl = cv2.stylization(wk, sigma_s=60, sigma_r=0.45)
        except Exception:
            styl = cv2.bilateralFilter(wk, 9, 120, 120)
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
        out = cv2.addWeighted(tinted, a, wk, 1.0 - a, 0)
        # 입력 크기로 복원 (저크기 작업 → 원본 해상도 프리뷰)
        if out.shape[:2] != (H, W):
            out = cv2.resize(out, (W, H))
        return out


def select_backend(profile=None) -> DiffusionBackend:
    """스펙 티어(SpecProfile) 기반 백엔드 선택. profile 없으면 자동 감지.
    요청 티어의 디바이스/의존성이 이 장비에 없으면 조용히 아래 티어로 내려가
    (최종 potato=Fallback) 엔진이 죽지 않는다. R4: 무거운 준비는 prepare()."""
    from . import spec

    if profile is None:
        profile = spec.resolve("auto")

    backend = profile.backend
    # 디바이스 부재 시 다운그레이드 (예: cuda 티어를 Mac 에서 선택)
    if backend != "fallback" and not spec.device_ok(profile.device):
        profile = spec.downgrade(profile)
        backend = profile.backend

    if backend == "diffusers":
        try:
            import importlib.util

            if importlib.util.find_spec("torch") and importlib.util.find_spec("diffusers"):
                from .diffusers_backend import DiffusersBackend

                return DiffusersBackend(profile)
        except Exception:
            pass
        return FallbackBackend(spec.TIERS["potato"])

    if backend == "streamdiffusion":
        try:
            import importlib.util

            if importlib.util.find_spec("torch") and importlib.util.find_spec("streamdiffusion"):
                from .streamdiffusion_backend import StreamConfig, StreamDiffusionBackend

                cfg = StreamConfig(
                    model_id=profile.model_id,
                    lcm_lora_id=profile.lcm_lora_id,
                    width=profile.width,
                    height=profile.height,
                    use_tensorrt=profile.use_tensorrt,
                )
                return StreamDiffusionBackend(cfg)
        except Exception:
            pass
        # streamdiffusion 미설치 → diffusers 시도 후 최종 potato
        if profile.device == "cuda":
            try:
                import importlib.util

                if importlib.util.find_spec("torch") and importlib.util.find_spec("diffusers"):
                    from .diffusers_backend import DiffusersBackend

                    return DiffusersBackend(spec.TIERS["cuda_3070"])
            except Exception:
                pass
        return FallbackBackend(spec.TIERS["potato"])

    return FallbackBackend(profile)
