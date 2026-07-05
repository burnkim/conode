"""M2 포터블 코어 테스트 (T15/T16) — SIF · FallbackBackend · LiveDiffusion.

실디퓨전(StreamDiffusion/TRT)은 4090 전용이라 여기선 폴백/구조만 검증한다.
"""
from __future__ import annotations

import numpy as np

from conode_engine.core.processor import FrameCtx
from conode_engine.diffusion.backend import DiffusionRequest, FallbackBackend
from conode_engine.diffusion.sif import SimilarImageFilter
from conode_engine.nodes.live_diffusion import LiveDiffusion


def _frame(v=None, h=180, w=320):
    if v is not None:
        return np.full((h, w, 3), v, np.uint8)
    return np.random.default_rng(0).integers(0, 255, (h, w, 3), dtype=np.uint8)


# ---- Similar Image Filter ----
def test_sif_skips_identical_after_first():
    sif = SimilarImageFilter(threshold=0.9, max_skip=5)
    f = _frame(0)
    assert sif.should_skip(f) is False  # 첫 프레임은 기준
    assert sif.should_skip(f) is True  # 동일 → 스킵


def test_sif_no_skip_on_big_change():
    sif = SimilarImageFilter(threshold=0.9, max_skip=5)
    sif.should_skip(_frame(0))
    assert sif.should_skip(_frame(255)) is False


def test_sif_max_skip_cap():
    sif = SimilarImageFilter(threshold=0.0, max_skip=2)  # 항상 유사
    f = _frame(0)
    assert sif.should_skip(f) is False  # 기준
    assert sif.should_skip(f) is True  # skip 1
    assert sif.should_skip(f) is True  # skip 2
    assert sif.should_skip(f) is False  # max 도달 → 리프레시


# ---- FallbackBackend ----
def test_fallback_backend_shape_and_prompt_determinism():
    b = FallbackBackend()
    img = _frame()
    out1 = b.generate(DiffusionRequest(image=img, prompt="stars"))
    out2 = b.generate(DiffusionRequest(image=img, prompt="stars"))
    assert out1.shape == (180, 320, 3) and out1.dtype == np.uint8
    assert np.array_equal(out1, out2)  # 결정적


# ---- LiveDiffusion ----
def test_live_params_flatten_and_modulation():
    n = LiveDiffusion("l")
    assert n.get("controlnet.enable") is True
    assert n.get("advanced.sif_threshold") == 0.9
    assert set(n.modulation_targets()) == {"prompt_strength", "controlnet.weight"}


def test_live_fallback_generate():
    n = LiveDiffusion("l")
    n.start()
    out = n.process(FrameCtx(), {"in": _frame()})
    assert out.shape == (180, 320, 3) and out.dtype == np.uint8
    assert n.backend_name == "fallback-stylize"


def test_live_none_input():
    assert LiveDiffusion("l").process(FrameCtx(), {"in": None}) is None


def test_live_region_apply_keeps_bg():
    n = LiveDiffusion("l")
    n.start()
    n.set("advanced.similar_image_filter", False)
    img = _frame(100, h=20, w=20)
    mask = np.zeros((20, 20), np.uint8)
    mask[:10, :] = 255  # 상단 절반만 디퓨전
    out = n.process(FrameCtx(), {"in": img, "mask": mask})
    assert np.array_equal(out[15, :, :], img[15, :, :])  # 하단은 원본 유지
