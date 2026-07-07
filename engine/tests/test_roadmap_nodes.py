"""로드맵 노드 테스트 (E2~E4) — VideoFile · LFO · EnvelopeFollower + ModMatrix sig 통합."""
from __future__ import annotations

import time

import numpy as np

from conode_engine.audio.modmatrix import ModMatrix as Matrix
from conode_engine.core.graph import Graph
from conode_engine.core.param_spec import Slider
from conode_engine.core.processor import FrameCtx, Processor
from conode_engine.nodes.envelope_follower import EnvelopeFollower
from conode_engine.nodes.lfo import LFO
from conode_engine.nodes.mod_matrix import ModMatrix
from conode_engine.nodes.video_file import VideoFile


# ---------------- VideoFile ----------------
def test_video_file_synthetic_fallback():
    n = VideoFile("v1")  # path="" → 합성 폴백
    n.start()
    try:
        frame = None
        for _ in range(60):  # ~0.6s 폴링
            frame = n.process(FrameCtx(t=0.0), {})
            if frame is not None:
                break
            time.sleep(0.01)
        assert frame is not None
        assert frame.shape == (180, 320, 3) and frame.dtype == np.uint8
        assert n.is_real is False  # 파일 없음
    finally:
        n.stop()


def test_video_file_params():
    n = VideoFile("v1")
    assert n.kind == "video_file" and n.category == "input"
    assert set(n.store.paths()) == {"path", "speed", "loop", "mirror"}


# ---------------- LFO ----------------
def test_lfo_output_and_bounds():
    n = LFO("lfo1")
    assert n.signal_name() == "lfo1"
    for t in (0.0, 0.1, 0.25, 0.5, 0.9, 1.3):
        out = n.process(FrameCtx(t=t), {})
        assert out["signal"] == "lfo1"
        assert 0.0 <= out["value"] <= 1.0
    assert isinstance(n.preview, np.ndarray)


def test_lfo_amount_scales():
    n = LFO("lfo1")
    n.set("amount", 0.5)
    n.set("shape", "saw")
    vals = [n.process(FrameCtx(t=t / 10.0), {})["value"] for t in range(20)]
    assert max(vals) <= 0.5 + 1e-6


def test_lfo_shapes_run():
    for shape in ("sine", "tri", "saw", "square"):
        n = LFO("l")
        n.set("shape", shape)
        out = n.process(FrameCtx(t=0.3), {})
        assert 0.0 <= out["value"] <= 1.0


# ---------------- EnvelopeFollower ----------------
def _audio(rms: float):
    return {"stems": [{"rms": rms, "peak": rms, "onset": 0, "centroid": 0, "flux": 0, "low": 0, "mid": 0, "high": 0}], "n": 1}


def test_envelope_attack_and_release():
    n = EnvelopeFollower("env1")
    assert n.signal_name() == "env1"
    # 어택: 높은 입력 → env 상승
    t = 0.0
    for _ in range(4):
        t += 1.0 / 30.0
        out = n.process(FrameCtx(t=t), {"audio": _audio(1.0)})
    assert out["value"] > 0.8 and out["signal"] == "env1"
    peak = out["value"]
    # 릴리스: 입력 0 → env 하강
    for _ in range(4):
        t += 1.0 / 30.0
        out = n.process(FrameCtx(t=t), {"audio": _audio(0.0)})
    assert out["value"] < peak


def test_envelope_no_audio_is_zero():
    n = EnvelopeFollower("env1")
    out = n.process(FrameCtx(t=0.1), {})
    assert out["value"] == 0.0


# ---------------- ModMatrix sig 통합 ----------------
class _Tgt(Processor):
    category = "generate"
    name = "Tgt"
    kind = "tgt"
    params = {"gain": Slider(0.0, 2.0, default=1.0, modulatable=True)}

    def process(self, ctx, inputs):
        return None


def test_modmatrix_exposes_signal_sources():
    g = Graph()
    g.add(LFO("lfo1", index=1))
    g.add(EnvelopeFollower("env1", index=2))
    g.add(_Tgt("t1", index=3))
    mod = ModMatrix("mod1", index=4)
    mod.graph = g
    g.add(mod)
    sources = mod.available_sources()
    assert "sig.lfo1" in sources
    assert "sig.env1" in sources


def test_modmatrix_resolves_sig_source():
    m = Matrix()
    assert m.resolve("sig.lfo1", {"signals": {"lfo1": 0.7}}, 0.0) == 0.7
    assert m.resolve("sig.missing", {"signals": {}}, 0.0) == 0.0


def test_modmatrix_collect_signals_from_graph():
    g = Graph()
    lfo = LFO("lfo1", index=1)
    g.add(lfo)
    mod = ModMatrix("mod1", index=2)
    mod.graph = g
    g.add(mod)
    lfo.process(FrameCtx(t=0.25), {})  # LFO 출력 생성
    sigs = mod._collect_signals()
    assert "lfo1" in sigs and 0.0 <= sigs["lfo1"] <= 1.0
