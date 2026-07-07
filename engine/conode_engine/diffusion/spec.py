"""스펙 티어 — 다양한 하드웨어에서 LiveDiffusion 을 돌리기 위한 프로파일.

한 코드베이스로 저사양(이 Mac: cv2 폴백/MPS 소형)부터 고사양(4090 TRT)까지 커버한다.
백엔드·디바이스·해상도(저크기)·스텝을 하나의 SpecProfile 로 묶고, auto_detect() 가
현재 장비에서 실제로 돌릴 수 있는 최적 티어를 고른다. 요청한 티어의 의존성이 없으면
select_backend 가 조용히 potato(폴백)로 내려가 엔진이 죽지 않는다.

티어(하드웨어 힌트):
  potato     — CPU/폴백, 저해상도. 어디서나 동작(이 Mac 포함). "확인용".
  mps_low    — Apple Silicon MPS, 소형 실디퓨전(torch+diffusers 설치 시).
  cuda_3070  — CUDA diffusers LCM, 512px, TRT 불필요(≈8GB VRAM).
  cuda_max   — StreamDiffusion + TensorRT(≈4090). 최고 성능.

모델은 전 티어 공통 SD1.5 + LCM-LoRA (permissive/상업 OK, PLAN §11).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpecProfile:
    tier: str            # 식별자 (registry 키)
    label: str           # UI 표시명
    backend: str         # "fallback" | "diffusers" | "streamdiffusion"
    device: str          # "cpu" | "mps" | "cuda"  (auto 는 resolve 에서 확정)
    width: int           # 디퓨전 작업 해상도 (저크기 = 저비용)
    height: int
    steps: int           # 디노이즈 스텝 수 (작을수록 빠름)
    use_tensorrt: bool
    vram_hint: str       # 대략 VRAM/장비 힌트
    note: str
    model_id: str = "runwayml/stable-diffusion-v1-5"
    lcm_lora_id: str = "latent-consistency/lcm-lora-sdv1-5"


TIERS: dict[str, SpecProfile] = {
    "potato": SpecProfile(
        tier="potato", label="Potato (CPU/폴백)", backend="fallback", device="cpu",
        width=256, height=144, steps=1, use_tensorrt=False,
        vram_hint="≈0GB · CPU 어디서나", note="실디퓨전 아님 — 파라미터 반응 스타일라이즈. 확인용.",
    ),
    "mps_low": SpecProfile(
        tier="mps_low", label="MPS Low (Apple Silicon)", backend="diffusers", device="mps",
        width=384, height=384, steps=2, use_tensorrt=False,
        vram_hint="≈통합메모리 8GB+ · M1/M2/M3", note="MPS 소형 실디퓨전 — torch+diffusers 설치 필요(느림).",
    ),
    "cuda_3070": SpecProfile(
        tier="cuda_3070", label="CUDA Balanced (≈3070)", backend="diffusers", device="cuda",
        width=512, height=512, steps=4, use_tensorrt=False,
        vram_hint="≈8GB VRAM · 3060~3080", note="CUDA diffusers LCM img2img, TRT 불필요.",
    ),
    "cuda_max": SpecProfile(
        tier="cuda_max", label="CUDA Max (≈4090)", backend="streamdiffusion", device="cuda",
        width=512, height=512, steps=2, use_tensorrt=True,
        vram_hint="≈16GB+ VRAM · 4080/4090", note="StreamDiffusion + TensorRT. 최고 처리율.",
    ),
}

#: UI/CLI 에 노출하는 선택지 순서 (auto 우선)
TIER_NAMES: list[str] = ["auto", *TIERS.keys()]

#: 저사양→고사양 자동 폴백 사다리
_FALLBACK_LADDER = ["cuda_max", "cuda_3070", "mps_low", "potato"]


def available_devices() -> set[str]:
    """이 장비에서 실제 사용 가능한 디바이스 집합. torch 미설치면 {'cpu'}."""
    devices = {"cpu"}
    try:
        import torch

        if torch.cuda.is_available():
            devices.add("cuda")
        if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            devices.add("mps")
    except Exception:
        pass
    return devices


def device_ok(device: str) -> bool:
    """요청 디바이스가 이 장비에서 가용한가 (cpu 는 항상 True)."""
    return device in available_devices()


def auto_detect() -> str:
    """현재 장비에서 실제로 돌릴 수 있는 최적 티어 이름.
    cuda_max 는 streamdiffusion+TRT 의존성이 크므로 자동 선택에서는 제외하고
    cuda_3070 을 CUDA 기본으로 둔다(명시적으로 cuda_max 를 골라야 TRT 시도)."""
    devs = available_devices()
    if "cuda" in devs:
        return "cuda_3070"
    if "mps" in devs:
        return "mps_low"
    return "potato"


def resolve(tier: str | None = "auto") -> SpecProfile:
    """티어 이름(또는 'auto'/None) → SpecProfile. device='auto' 개념은 여기서 확정."""
    if not tier or tier == "auto":
        tier = auto_detect()
    return TIERS.get(tier, TIERS["potato"])


def downgrade(profile: SpecProfile) -> SpecProfile:
    """요청 프로파일을 이 장비에서 가용한 아래 티어로 내린다(의존성/디바이스 부재 시)."""
    devs = available_devices()
    start = _FALLBACK_LADDER.index(profile.tier) if profile.tier in _FALLBACK_LADDER else 0
    for name in _FALLBACK_LADDER[start:]:
        cand = TIERS[name]
        if cand.backend == "fallback" or cand.device in devs:
            return cand
    return TIERS["potato"]
