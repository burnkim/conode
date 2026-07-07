"""ModMatrix 에디터 테스트 — set/clear 셀 · 상태 노출 · WS 왕복 (매트릭스 에디터 UI)."""
from __future__ import annotations

import asyncio
import json

import websockets

from conode_engine.audio.modmatrix import ModMatrix as Matrix
from conode_engine.core.graph import Graph
from conode_engine.core.param_spec import Group, Slider, Toggle
from conode_engine.core.processor import Processor
from conode_engine.nodes.mod_matrix import ModMatrix
from conode_engine.protocol.server import EngineServer


class _Target(Processor):
    category = "generate"
    name = "Target"
    kind = "target"
    params = {
        "gain": Slider(0.0, 2.0, default=1.0, modulatable=True),
        "fixed": Toggle(True),  # 비-modulatable
        "grp": Group({"w": Slider(0.0, 1.0, default=0.5, modulatable=True)}),
    }

    def process(self, ctx, inputs):
        return None


# ---------------- 매트릭스 단위 ----------------
def test_set_cell_upsert():
    m = Matrix()
    m.set_cell("stem0.rms", "n.gain", 0.5, curve="exp", smooth_ms=20)
    assert len(m.cells) == 1
    c = m.find_cell("stem0.rms", "n.gain")
    assert c.amount == 0.5 and c.curve == "exp" and c.smooth_ms == 20
    # 같은 (source,target) → upsert (추가 아님)
    m.set_cell("stem0.rms", "n.gain", -0.3, curve="lin")
    assert len(m.cells) == 1
    assert m.find_cell("stem0.rms", "n.gain").amount == -0.3


def test_clear_cell():
    m = Matrix()
    m.set_cell("lfo0", "n.gain", 0.4)
    assert m.clear_cell("lfo0", "n.gain") is True
    assert m.clear_cell("lfo0", "n.gain") is False  # 이미 없음
    assert m.cells == []


def test_bad_curve_falls_back_lin():
    m = Matrix()
    m.set_cell("stem1.flux", "n.gain", 0.2, curve="bogus")
    assert m.find_cell("stem1.flux", "n.gain").curve == "lin"


def test_cells_state_shape():
    m = Matrix()
    m.set_cell("stem0.rms", "n.gain", 0.5, curve="log", smooth_ms=30)
    st = m.cells_state()
    assert st == [{"source": "stem0.rms", "target": "n.gain", "amount": 0.5, "curve": "log", "smooth_ms": 30}]


# ---------------- 노드 상태 노출 ----------------
def test_node_available_targets_and_sources():
    g = Graph()
    g.add(_Target("t1", index=1))
    mod = ModMatrix("mod1", index=2)
    mod.graph = g
    g.add(mod)
    targets = mod.available_targets()
    assert "t1.gain" in targets
    assert "t1.grp.w" in targets
    assert "t1.fixed" not in targets  # 비-modulatable 제외 (R8)
    sources = mod.available_sources()
    assert "stem0.rms" in sources and "stem11.high" in sources
    assert "gesture.frame" in sources
    st = mod.matrix_state()
    assert st["node"] == "mod1" and st["curves"] == ["lin", "exp", "log"]


# ---------------- WS 왕복 ----------------
def test_modmatrix_over_ws():
    async def scenario():
        g = Graph()
        g.add(_Target("t1", index=1))
        mod = ModMatrix("mod1", index=2)
        mod.graph = g
        g.add(mod)
        srv = EngineServer(graph=g)
        async with websockets.serve(srv.handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
                for _ in range(4):  # hello, node.list, graph.state, scene.list
                    await ws.recv()

                # get → modmatrix.state
                await ws.send(json.dumps({"type": "modmatrix.get", "v": 0}))
                st = json.loads(await ws.recv())
                assert st["type"] == "modmatrix.state" and st["node"] == "mod1"
                assert "t1.gain" in st["targets"]
                assert "stem0.rms" in st["sources"]

                # set cell → broadcast state 에 새 셀
                await ws.send(json.dumps({
                    "type": "modmatrix.cell.set", "v": 0, "node": "mod1",
                    "source": "stem0.rms", "target": "t1.gain", "amount": 0.9,
                    "curve": "exp", "smooth_ms": 20,
                }))
                st2 = json.loads(await ws.recv())
                cell = next((c for c in st2["cells"] if c["source"] == "stem0.rms" and c["target"] == "t1.gain"), None)
                assert cell is not None and abs(cell["amount"] - 0.9) < 1e-6 and cell["curve"] == "exp"

                # clear cell → 사라짐
                await ws.send(json.dumps({
                    "type": "modmatrix.cell.clear", "v": 0, "node": "mod1",
                    "source": "stem0.rms", "target": "t1.gain",
                }))
                st3 = json.loads(await ws.recv())
                assert not any(c["source"] == "stem0.rms" and c["target"] == "t1.gain" for c in st3["cells"])

    asyncio.run(scenario())
