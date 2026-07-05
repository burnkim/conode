"""씬/큐 테스트 (D) — SceneStore capture/save/recall/crossfade."""
from __future__ import annotations

from conode_engine.core.graph import Graph
from conode_engine.core.param_spec import Slider
from conode_engine.core.processor import Processor
from conode_engine.core.scenes import SceneStore


class _N(Processor):
    inputs = ()
    params = {"p": Slider(0.0, 2.0, default=1.0)}


def test_scene_save_recall_instant():
    g = Graph()
    g.add(_N("a"))
    s = SceneStore()
    g.nodes["a"].set("p", 0.5)
    s.save("s1", g)
    g.nodes["a"].set("p", 2.0)
    assert s.recall("s1", g, fade=0.0) is True
    assert g.nodes["a"].get("p") == 0.5


def test_scene_recall_crossfade():
    g = Graph()
    g.add(_N("a"))
    s = SceneStore()
    g.nodes["a"].set("p", 0.0)
    s.save("s1", g)  # target p=0
    g.nodes["a"].set("p", 2.0)
    s.recall("s1", g, fade=1.0, now=0.0)  # 2 → 0 over 1s
    s.update(g, 0.5)
    assert abs(g.nodes["a"].get("p") - 1.0) < 1e-6  # 중간
    s.update(g, 1.0)
    assert abs(g.nodes["a"].get("p") - 0.0) < 1e-6  # 완료


def test_scene_recall_unknown():
    g = Graph()
    g.add(_N("a"))
    assert SceneStore().recall("nope", g) is False


def test_scene_names():
    g = Graph()
    g.add(_N("a"))
    s = SceneStore()
    s.save("intro", g)
    s.save("drop", g)
    assert set(s.names()) == {"intro", "drop"}
