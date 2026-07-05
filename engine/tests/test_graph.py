"""Graph 코어 테스트 (T7) — 연결/전파/사이클/삭제 + Canny 엣지."""
from __future__ import annotations

import numpy as np
import pytest

from conode_engine.core.graph import Graph
from conode_engine.core.processor import FrameCtx, Processor
from conode_engine.nodes.canny import Canny


class _Src(Processor):
    category = "input"
    name = "Src"
    inputs = ()

    def __init__(self, node_id, frame):
        super().__init__(node_id)
        self._frame = frame

    def process(self, ctx, inputs):
        return self._frame


def _edge_image(n=32):
    img = np.zeros((n, n, 3), dtype=np.uint8)
    img[:, n // 2 :] = 255  # 수직 엣지
    return img


def test_graph_propagates_frames_and_canny_detects_edges():
    g = Graph()
    g.add(_Src("s", _edge_image()))
    g.add(Canny("c", index=1))
    g.connect("s", "c", "in")
    g.evaluate(FrameCtx())
    out = g.nodes["c"].output
    assert out is not None
    assert out.shape[:2] == (32, 32)
    assert int((out > 0).sum()) > 0  # 엣지 픽셀 검출


def test_topo_order_source_before_downstream():
    g = Graph()
    g.add(_Src("s", _edge_image()))
    g.add(Canny("c"))
    g.connect("s", "c", "in")
    order = g.topo()
    assert order.index("s") < order.index("c")


def test_connect_unknown_port_rejected():
    g = Graph()
    g.add(_Src("s", _edge_image()))
    g.add(Canny("c"))
    with pytest.raises(ValueError):
        g.connect("s", "c", "nope")


def test_cycle_rejected():
    g = Graph()
    g.add(Canny("a"))
    g.add(Canny("b"))
    g.connect("a", "b", "in")
    with pytest.raises(ValueError):
        g.connect("b", "a", "in")  # a→b→a 사이클


def test_remove_node_cleans_edges():
    g = Graph()
    g.add(_Src("s", _edge_image()))
    g.add(Canny("c"))
    g.connect("s", "c", "in")
    g.remove("s")
    assert "s" not in g.nodes
    assert g.edges["c"] == {}


class _Boom(Processor):
    inputs = ("in",)

    def process(self, ctx, inputs):
        raise RuntimeError("boom")


def test_tick_isolates_node_errors():
    g = Graph()
    g.add(_Src("s", _edge_image()))
    g.add(_Boom("b"))
    g.connect("s", "b", "in")
    g.evaluate(FrameCtx())  # 예외가 그래프를 멈추면 안 됨
    assert g.nodes["b"].output is None
    assert "boom" in (g.nodes["b"].last_error or "")


def test_describe_has_nodes_and_edges():
    g = Graph()
    g.add(_Src("s", _edge_image()))
    g.add(Canny("c", index=1))
    g.connect("s", "c", "in")
    d = g.describe()
    assert {n["id"] for n in d["nodes"]} == {"s", "c"}
    assert d["edges"] == [{"src": "s", "dst": "c", "port": "in"}]
