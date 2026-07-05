"""오디오/ModMatrix 테스트 (M4, T25-T28)."""
from __future__ import annotations

import numpy as np

from conode_engine.audio.features import FEATURES, FeatureExtractor
from conode_engine.audio.modmatrix import LFO, ModCell, ModMatrix
from conode_engine.audio.prompt_binding import bind_prompt, parse_bindings
from conode_engine.core.graph import Graph
from conode_engine.core.param_spec import Slider
from conode_engine.core.processor import FrameCtx, Processor
from conode_engine.nodes.audio_in import AudioIn
from conode_engine.nodes.mod_matrix import ModMatrix as ModMatrixNode


# ---- features ----
def test_features_keys_and_range():
    ex = FeatureExtractor(samplerate=48000)
    t = np.arange(1024) / 48000
    sine = (0.8 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    f = ex.extract(sine)
    assert set(f) == set(FEATURES)
    assert f["rms"] > 0.1
    assert all(0.0 <= v <= 1.0 for v in f.values())


def test_features_silence():
    f = FeatureExtractor().extract(np.zeros(1024, np.float32))
    assert f["rms"] == 0.0 and f["peak"] == 0.0


# ---- LFO / ModMatrix ----
def test_lfo_range():
    lfo = LFO(rate=1.0)
    assert all(0.0 <= lfo.value(i / 10) <= 1.0 for i in range(20))


def test_modmatrix_apply_base_plus_offset():
    mm = ModMatrix()
    mm.add_cell(ModCell("stem0.rms", "n.p", amount=1.0, smooth_ms=0))
    store = {"n.p": 0.0}
    mm.apply(
        {"stems": [{"rms": 0.5}]}, t=0.0, dt=0.033,
        get=lambda k: store[k], set_=lambda k, v: store.__setitem__(k, v),
        rng=lambda k: (0.0, 2.0), modulatable=lambda k: True,
    )
    assert abs(store["n.p"] - 1.0) < 1e-6  # 0 + 1.0*0.5*(2-0)


def test_modmatrix_gate_non_modulatable():
    mm = ModMatrix()
    mm.add_cell(ModCell("stem0.rms", "n.p", amount=1.0, smooth_ms=0))
    store = {"n.p": 0.0}
    mm.apply(
        {"stems": [{"rms": 1.0}]}, 0.0, 0.033,
        get=lambda k: store[k], set_=lambda k, v: store.__setitem__(k, v),
        rng=lambda k: (0.0, 1.0), modulatable=lambda k: False,
    )
    assert store["n.p"] == 0.0  # R8: modulatable 아니면 미적용


# ---- prompt binding ----
def test_prompt_binding():
    assert parse_bindings("(star:{stem0.rms})") == [("star", "stem0.rms")]
    out = bind_prompt("(star:{stem0.rms}), plain text", lambda s: 0.7)
    assert "(star:0.70)" in out and "plain text" in out


# ---- nodes ----
def test_audio_in_synth_structure():
    n = AudioIn("a")
    n.start()
    out = n.process(FrameCtx(), {})
    n.stop()
    assert out["n"] == 12 and len(out["stems"]) == 12
    assert all(set(s) == set(FEATURES) for s in out["stems"])
    assert n.preview_frame().shape == (180, 320, 3)


class _Target(Processor):
    inputs = ()
    params = {"p": Slider(0.0, 2.0, default=1.0, modulatable=True)}


def test_modmatrix_gesture_frame_source():
    mm = ModMatrix()
    mm.add_cell(ModCell("gesture.frame", "n.p", amount=1.0, smooth_ms=0))
    store = {"n.p": 0.0}
    kw = dict(get=lambda k: store[k], set_=lambda k, v: store.__setitem__(k, v), rng=lambda k: (0.0, 2.0), modulatable=lambda k: True)
    mm.apply({"stems": [], "gesture": {"type": "frame"}}, 0.0, 0.033, **kw)
    assert abs(store["n.p"] - 2.0) < 1e-6  # frame=1 → 1*1*2


def test_modmatrix_gesture_value_source():
    mm = ModMatrix()
    mm.add_cell(ModCell("gesture.value", "n.p", amount=1.0, smooth_ms=0))
    store = {"n.p": 0.0}
    mm.apply(
        {"stems": [], "gesture": {"type": "pinch", "value": 0.5}}, 0.0, 0.033,
        get=lambda k: store[k], set_=lambda k, v: store.__setitem__(k, v),
        rng=lambda k: (0.0, 2.0), modulatable=lambda k: True,
    )
    assert abs(store["n.p"] - 1.0) < 1e-6  # 0.5*2


def test_modmatrix_node_modulates_graph():
    g = Graph()
    g.add(_Target("live1"))
    mm = ModMatrixNode("mod1")
    g.add(mm)
    mm.graph = g
    mm.matrix.cells.clear()
    mm.matrix.add_cell(ModCell("stem0.rms", "live1.p", amount=1.0, smooth_ms=0))
    mm.process(FrameCtx(t=0.0), {"audio": {"stems": [{"rms": 0.5}]}})
    assert abs(g.nodes["live1"].get("p") - 2.0) < 1e-6  # base1 + 0.5*2 clamp→2
