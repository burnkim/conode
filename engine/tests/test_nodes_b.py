"""§1.3 나머지 v1 노드 테스트 (M-B)."""
from __future__ import annotations

import numpy as np
import pytest

from conode_engine.core.processor import FrameCtx
from conode_engine.nodes import (
    Blend,
    ColorGrade,
    Crossfade,
    FeedbackLoop,
    Image,
    MaskCompose,
    StylePreset,
    Switch,
)


def _f():
    return np.random.default_rng(0).integers(0, 255, (180, 320, 3), np.uint8)


def test_image_test_pattern():
    out = Image("i").process(FrameCtx(), {})
    assert out.shape == (180, 320, 3) and out.dtype == np.uint8


@pytest.mark.parametrize(
    "node,inp",
    [
        (ColorGrade("c"), {"in": _f()}),
        (FeedbackLoop("f"), {"in": _f()}),
        (StylePreset("s"), {"in": _f()}),
        (Blend("b"), {"a": _f(), "b": _f()}),
        (Crossfade("x"), {"a": _f(), "b": _f()}),
        (MaskCompose("m"), {"a": _f(), "b": _f()}),
        (Switch("w"), {"in0": _f()}),
    ],
    ids=lambda x: getattr(x, "kind", "in"),
)
def test_node_outputs_bgr(node, inp):
    out = node.process(FrameCtx(), inp)
    assert out is not None and out.shape == (180, 320, 3) and out.dtype == np.uint8


def test_style_preset_all():
    n = StylePreset("s")
    img = _f()
    for p in ["ink", "neon", "posterize", "pencil", "none"]:
        n.set("preset", p)
        assert n.process(FrameCtx(), {"in": img}).shape == (180, 320, 3)


def test_blend_modes():
    n = Blend("b")
    a, b = _f(), _f()
    for mode in ["mix", "add", "multiply", "screen"]:
        n.set("mode", mode)
        assert n.process(FrameCtx(), {"a": a, "b": b}).dtype == np.uint8


def test_mask_compose_ops():
    n = MaskCompose("m")
    a = np.zeros((20, 20, 3), np.uint8)
    a[:10] = 255
    b = np.zeros((20, 20, 3), np.uint8)
    b[:, :10] = 255
    for op in ["union", "intersect", "subtract"]:
        n.set("op", op)
        out = n.process(FrameCtx(), {"a": a, "b": b})
        assert out.shape == (20, 20, 3)


def test_registry_has_all_new():
    from conode_engine.protocol.server import node_registry

    reg = node_registry()
    for k in ["image", "blend", "crossfade", "color_grade", "switch", "mask_compose", "feedback", "style_preset"]:
        assert k in reg
    assert len(reg) == 21
