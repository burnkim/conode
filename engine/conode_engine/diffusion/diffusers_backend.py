"""Diffusers 백엔드 — device 이식성 img2img (LCM-LoRA).

한 백엔드로 CUDA(3070급)·Apple Silicon MPS(이 Mac)·CPU 를 모두 돌린다(device 는
SpecProfile 이 지정). TensorRT/StreamDiffusion 없이 순수 diffusers 라 설치가 가볍고
Mac 에서도(느리지만) 실디퓨전이 가능하다 — cuda_max(StreamDiffusion+TRT) 로 가기 전의
"중간 사양" 경로.

모델: SD1.5 + LCM-LoRA (permissive/상업 OK, PLAN §11). guidance≈1.0, 2~4 step.
torch/diffusers 는 메서드 내부 지연 임포트 — 미설치 환경에서도 모듈 임포트는 안전하다
(select_backend 가 potato 폴백으로 우회). **Mac 개발기(torch 미설치)에서 실행 검증 불가 —
torch+diffusers 설치 후 / 배포 장비에서 검증.**
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from .backend import DiffusionBackend, DiffusionRequest
from .spec import SpecProfile, TIERS


class DiffusersBackend(DiffusionBackend):
    name = "diffusers-lcm"
    real = True

    def __init__(self, profile: Optional[SpecProfile] = None):
        self.profile = profile or TIERS["cuda_3070"]
        self._pipe = None
        self._torch = None
        self._prompt = None

    # --- 준비 (R4: tick 밖. 모델 로드 수 초~) ---
    def prepare(self) -> None:
        import torch
        from diffusers import AutoPipelineForImage2Image, LCMScheduler

        self._torch = torch
        device = self.profile.device
        # MPS/CPU 는 float16 불안정 가능 → float32, CUDA 만 float16.
        dtype = torch.float16 if device == "cuda" else torch.float32

        pipe = AutoPipelineForImage2Image.from_pretrained(
            self.profile.model_id, torch_dtype=dtype, safety_checker=None
        )
        # LCM 스케줄러 + LCM-LoRA (2~4 step 저지연)
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
        pipe.load_lora_weights(self.profile.lcm_lora_id)
        pipe.fuse_lora()
        pipe = pipe.to(device)
        pipe.set_progress_bar_config(disable=True)
        self._pipe = pipe

    def close(self) -> None:
        self._pipe = None
        if self._torch is not None:
            try:
                if self.profile.device == "cuda":
                    self._torch.cuda.empty_cache()
            except Exception:
                pass

    # --- 생성 (tick 안 — 실제 디퓨전) ---
    def generate(self, req: DiffusionRequest) -> np.ndarray:
        if self._pipe is None:
            self.prepare()
        import cv2
        from PIL import Image

        w, h = self.profile.width, self.profile.height
        rgb = cv2.cvtColor(req.image, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (w, h))
        pil = Image.fromarray(rgb)

        # img2img: strength(0..1) = 원본 보존 vs 재생성. req.strength(0..2)를 매핑.
        strength = max(0.05, min(1.0, req.strength / 2.0))
        steps = max(1, min(8, req.steps))
        gen = self._torch.Generator(
            device=self.profile.device if self.profile.device != "mps" else "cpu"
        ).manual_seed(int(req.seed))

        out_pil = self._pipe(
            prompt=req.prompt or "",
            negative_prompt=req.negative or None,
            image=pil,
            num_inference_steps=steps,
            strength=strength,
            guidance_scale=1.0,  # LCM
            generator=gen,
        ).images[0]

        out_rgb = np.asarray(out_pil)
        out = cv2.cvtColor(out_rgb, cv2.COLOR_RGB2BGR)
        return cv2.resize(out, (req.image.shape[1], req.image.shape[0]))
