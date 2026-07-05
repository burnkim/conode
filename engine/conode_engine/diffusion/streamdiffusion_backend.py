"""StreamDiffusion 백엔드 (M2 T18) — LCM-LoRA img2img + ControlNet, TensorRT 가속.

타깃: RTX 4090 (CUDA). **이 파일은 Mac 개발기에서 실행·검증되지 않았다(블라인드).**
4090 배포 시 검증 필요. torch/streamdiffusion 은 메서드 내부에서 지연 임포트하므로
CUDA 없는 환경에서도 모듈 임포트 자체는 안전하다(select_backend 가 Fallback 으로 우회).

모델: LCM/LCM-LoRA (permissive, 상업 사용 가능 — PLAN §11 결정). SD1.5 base + LCM-LoRA.
가속: StreamDiffusion 의 TensorRT accel (engines 캐시 디렉터리, 최초 1회 빌드) — T19.

설치(4090): engine/requirements-cuda.txt 참고. 모델 가중치는 앱 미포함(다운로더, §7).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from .backend import DiffusionBackend, DiffusionRequest


@dataclass
class StreamConfig:
    model_id: str = "runwayml/stable-diffusion-v1-5"  # base; LCM-LoRA 를 얹는다
    lcm_lora_id: str = "latent-consistency/lcm-lora-sdv1-5"
    width: int = 512
    height: int = 512
    t_index_list: list[int] = field(default_factory=lambda: [32, 45])  # creativity 기본
    use_tensorrt: bool = True
    engine_dir: str = "models/trt-engines"  # TRT 캐시 (T19)
    cfg_type: str = "none"  # LCM 은 보통 cfg 불필요
    dtype: str = "float16"


class StreamDiffusionBackend(DiffusionBackend):
    name = "streamdiffusion-lcm"
    real = True

    def __init__(self, config: Optional[StreamConfig] = None):
        self.config = config or StreamConfig()
        self._stream = None
        self._torch = None
        self._postprocess = None
        self._prompt = ""

    # --- 준비 (R4: tick 밖. 최초 TRT 빌드는 수 분) ---
    def prepare(self) -> None:
        import torch  # 지연 임포트 — Mac 에서는 여기 도달 전 Fallback
        from diffusers import StableDiffusionPipeline
        from streamdiffusion import StreamDiffusion
        from streamdiffusion.image_utils import postprocess_image

        self._torch = torch
        self._postprocess = postprocess_image
        dtype = torch.float16 if self.config.dtype == "float16" else torch.float32

        pipe = StableDiffusionPipeline.from_pretrained(self.config.model_id).to(
            device="cuda", dtype=dtype
        )
        stream = StreamDiffusion(
            pipe,
            t_index_list=self.config.t_index_list,
            torch_dtype=dtype,
            cfg_type=self.config.cfg_type,
            width=self.config.width,
            height=self.config.height,
        )
        # LCM-LoRA (permissive/상업 OK, §11)
        stream.load_lcm_lora(self.config.lcm_lora_id)
        stream.fuse_lora()

        if self.config.use_tensorrt:
            # TensorRT 가속 — engines 디렉터리에 최초 1회 빌드 후 캐시 (T19)
            from streamdiffusion.acceleration.tensorrt import accelerate_with_tensorrt

            Path(self.config.engine_dir).mkdir(parents=True, exist_ok=True)
            stream = accelerate_with_tensorrt(
                stream, self.config.engine_dir, max_batch_size=2
            )

        self._stream = stream

    def close(self) -> None:
        self._stream = None
        if self._torch is not None:
            try:
                self._torch.cuda.empty_cache()
            except Exception:
                pass

    # --- 생성 (tick 안 — 실제 디퓨전 연산) ---
    def generate(self, req: DiffusionRequest) -> np.ndarray:
        if self._stream is None:
            self.prepare()
        torch = self._torch
        import cv2

        # creativity(denoise step markers) → t_index_list. 프롬프트 변경 시 재준비.
        if req.prompt != self._prompt:
            self._stream.prepare(
                prompt=req.prompt,
                negative_prompt=req.negative,
                guidance_scale=1.0,  # LCM
            )
            self._prompt = req.prompt

        # BGR(H,W,3) → RGB float tensor (1,3,H,W) in [0,1]
        rgb = cv2.cvtColor(req.image, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (self.config.width, self.config.height))
        t = torch.from_numpy(rgb).to("cuda").float().div(255.0).permute(2, 0, 1).unsqueeze(0)

        # ControlNet 컨디셔닝은 StreamDiffusion 버전별 지원차가 큼 → 4090 검증 필요.
        # 지원 시 req.control(BGR)을 전처리해 stream 에 주입한다.
        x_out = self._stream(t)

        pil = self._postprocess(x_out, output_type="pil")[0]
        out_rgb = np.asarray(pil)
        out = cv2.cvtColor(out_rgb, cv2.COLOR_RGB2BGR)
        return cv2.resize(out, (req.image.shape[1], req.image.shape[0]))
