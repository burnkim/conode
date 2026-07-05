"""출력 노드 테스트 (M5, T30/T31) — MappedOutput 코너핀 + Recorder."""
from __future__ import annotations

import numpy as np

from conode_engine.core.processor import FrameCtx
from conode_engine.nodes.mapped_output import MappedOutput
from conode_engine.nodes.recorder import Recorder


def test_mapped_identity_shape():
    m = MappedOutput("m")
    img = np.random.default_rng(0).integers(0, 255, (180, 320, 3), np.uint8)
    out = m.process(FrameCtx(), {"in": img})
    assert out.shape == (180, 320, 3) and out.dtype == np.uint8


def test_mapped_cornerpin_warps():
    m = MappedOutput("m")
    m.set("corners.tl_x", 0.3)
    m.set("corners.tl_y", 0.3)
    img = np.full((180, 320, 3), 200, np.uint8)
    out = m.process(FrameCtx(), {"in": img})
    assert int(out[3, 3].sum()) < 60  # 좌상단은 워프로 비워져 검정


def test_mapped_none_input():
    assert MappedOutput("m").process(FrameCtx(), {"in": None}) is None


def test_recorder_writes_and_closes():
    from conode_engine.nodes.recorder import _REC_DIR

    r = Recorder("rec")
    r.set("record", True)
    r.set("filename", "test_clip.mp4")
    r.set("fps", 10)
    img = np.random.default_rng(1).integers(0, 255, (64, 64, 3), np.uint8)
    for i in range(8):
        out = r.process(FrameCtx(seq=i), {"in": img})
    assert out.shape == (64, 64, 3)  # passthrough
    r.set("record", False)
    r.process(FrameCtx(), {"in": img})  # close

    f = _REC_DIR / "test_clip.mp4"
    try:
        assert f.exists() and f.stat().st_size > 0
    finally:
        if f.exists():
            f.unlink()
