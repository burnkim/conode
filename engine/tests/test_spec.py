"""스펙 티어 테스트 (H2~H4) — 프로파일·자동감지·안전 폴백·저해상도.

이 CI 는 torch 미설치(Mac 개발기) 전제 — cuda/mps 티어는 potato 로 폴백해야 한다.
"""
from __future__ import annotations

import numpy as np

from conode_engine.diffusion import spec
from conode_engine.diffusion.backend import (
    DiffusionRequest,
    FallbackBackend,
    select_backend,
)


def test_tiers_wellformed():
    assert set(spec.TIERS) == {"potato", "mps_low", "cuda_3070", "cuda_max"}
    for name, p in spec.TIERS.items():
        assert p.tier == name
        assert p.backend in {"fallback", "diffusers", "streamdiffusion"}
        assert p.device in {"cpu", "mps", "cuda"}
        assert p.width > 0 and p.height > 0 and p.steps >= 1
    assert spec.TIER_NAMES[0] == "auto"


def test_potato_always_available():
    assert "cpu" in spec.available_devices()
    assert spec.device_ok("cpu") is True


def test_auto_detect_without_torch_is_potato():
    # torch 미설치 → cpu 만 가용 → potato
    if spec.available_devices() == {"cpu"}:
        assert spec.auto_detect() == "potato"
        assert spec.resolve("auto").tier == "potato"


def test_resolve_named_and_unknown():
    assert spec.resolve("cuda_3070").tier == "cuda_3070"
    assert spec.resolve("bogus").tier == "potato"  # 미지의 티어 → 안전 기본
    assert spec.resolve(None).tier == spec.auto_detect()


def test_cuda_tier_downgrades_on_cpu_only_machine():
    if "cuda" not in spec.available_devices():
        assert spec.device_ok("cuda") is False
        b = select_backend(spec.TIERS["cuda_3070"])
        # torch/diffusers 없음 → potato 폴백
        assert isinstance(b, FallbackBackend)
        assert b.profile.tier == "potato"


def test_cuda_max_downgrades_on_cpu_only_machine():
    if "cuda" not in spec.available_devices():
        b = select_backend(spec.TIERS["cuda_max"])
        assert isinstance(b, FallbackBackend)


def test_select_backend_auto_is_fallback_here():
    b = select_backend()  # profile None → auto
    if spec.available_devices() == {"cpu"}:
        assert isinstance(b, FallbackBackend)


def test_fallback_lowres_roundtrip():
    # potato 저해상도 작업 → 입력 크기로 복원
    img = np.full((240, 320, 3), 128, np.uint8)
    b = FallbackBackend(spec.TIERS["potato"])
    out = b.generate(DiffusionRequest(image=img, prompt="stars", strength=1.0))
    assert out.shape == img.shape  # 입력 해상도 유지
    assert out.dtype == np.uint8


def test_fallback_no_profile_keeps_size():
    img = np.full((180, 240, 3), 64, np.uint8)
    out = FallbackBackend().generate(DiffusionRequest(image=img, prompt="x"))
    assert out.shape == img.shape


def test_live_diffusion_tier_param_and_backend_name():
    from conode_engine.nodes.live_diffusion import LiveDiffusion

    n = LiveDiffusion("live1")
    assert "tier" in n.params
    assert n.get("tier") == "auto"
    n.start()  # torch 없음 → potato 폴백
    assert n._backend is not None
    assert "potato" in n.backend_name or "fallback" in n.backend_name
    n.stop()


def test_downgrade_ladder():
    # cuda_max → (cpu-only machine) → potato
    if spec.available_devices() == {"cpu"}:
        assert spec.downgrade(spec.TIERS["cuda_max"]).tier == "potato"
        assert spec.downgrade(spec.TIERS["mps_low"]).tier == "potato"
