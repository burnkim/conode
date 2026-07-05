"""엔진 스켈레톤 테스트 (T5) — ParamSpec · LatestWins · Scheduler · WS 서버."""
from __future__ import annotations

import asyncio
import json

import pytest
import websockets

from conode_engine.core import (
    Enum,
    FrameCtx,
    Group,
    LatestWins,
    Processor,
    Scheduler,
    Slider,
    Toggle,
)
from conode_engine.core.param_spec import ParamStore, Text
from conode_engine.protocol.messages import FramePreview
from conode_engine.protocol.server import EngineServer


class DemoNode(Processor):
    category = "input"
    name = "Demo"
    params = {
        "exposure": Slider(0.0, 1.0, default=0.5, modulatable=True),
        "enabled": Toggle(True),
        "mode": Enum(["a", "b", "c"], default="a"),
        "prompt": Text("hi"),
        "controlnet": Group(
            {
                "weight": Slider(0.0, 2.0, default=1.0, modulatable=True),
                "enable": Toggle(True),
            }
        ),
    }

    def process(self, ctx: FrameCtx, inputs: dict):
        return ctx.seq


# ---------------- ParamSpec / ParamStore ----------------
def test_param_defaults_and_flatten():
    s = ParamStore(DemoNode.params)
    assert s.get("exposure") == 0.5
    assert s.get("mode") == "a"
    assert s.get("controlnet.weight") == 1.0  # Group → dotted path
    assert set(s.paths()) == {
        "exposure",
        "enabled",
        "mode",
        "prompt",
        "controlnet.weight",
        "controlnet.enable",
    }


def test_slider_clamps():
    s = ParamStore(DemoNode.params)
    assert s.set("exposure", 5.0) == 1.0  # clamp hi
    assert s.set("exposure", -3) == 0.0  # clamp lo


def test_enum_rejects_unknown():
    s = ParamStore(DemoNode.params)
    with pytest.raises(ValueError):
        s.set("mode", "z")


def test_unknown_path_raises():
    s = ParamStore(DemoNode.params)
    with pytest.raises(KeyError):
        s.set("nope", 1)


def test_modulation_targets_registered():
    # R8: modulatable 파라미터만 ModMatrix 타깃
    s = ParamStore(DemoNode.params)
    assert sorted(s.modulation_targets()) == ["controlnet.weight", "exposure"]


def test_describe_shape():
    d = ParamStore(DemoNode.params).describe()
    assert d["exposure"]["kind"] == "slider"
    assert d["mode"]["kind"] == "enum" and d["mode"]["options"] == ["a", "b", "c"]


# ---------------- LatestWins ----------------
def test_latest_wins_drops_stale():
    q: LatestWins[int] = LatestWins()
    assert q.get() is None
    q.put(1)
    q.put(2)  # 1 을 버림
    q.put(3)  # 2 를 버림
    assert q.dropped == 2
    assert q.get() == 3
    assert q.get() is None  # 소비 후 비어 있음


# ---------------- Scheduler ----------------
def test_scheduler_runs_at_differentiated_fps():
    n30 = DemoNode("n30")
    n60 = DemoNode("n60")
    sched = Scheduler()
    sched.add(n30, fps=30.0)
    sched.add(n60, fps=60.0)
    counts = asyncio.run(sched.run(duration=0.25))
    assert counts["n30"] >= 1 and counts["n60"] >= 1
    # 60fps 노드는 30fps 노드보다 최소한 같거나 더 많이 tick
    assert counts["n60"] >= counts["n30"]
    assert n30.tick_count == counts["n30"]


# ---------------- WS 서버 (계약 왕복) ----------------
def test_ws_handshake_paramset_and_broadcast():
    async def scenario():
        node = DemoNode("cam1", index=1)
        srv = EngineServer(nodes=[node])
        async with websockets.serve(srv.handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
                hello = json.loads(await ws.recv())
                nodelist = json.loads(await ws.recv())
                graphstate = json.loads(await ws.recv())
                scenelist = json.loads(await ws.recv())
                assert hello["type"] == "hello" and hello["role"] == "engine"
                assert nodelist["type"] == "node.list"
                assert nodelist["nodes"][0]["id"] == "cam1"
                assert graphstate["type"] == "graph.state"
                assert scenelist["type"] == "scene.list"

                # UI→engine: param.set
                await ws.send(
                    json.dumps(
                        {"type": "param.set", "v": 0, "node": "cam1", "path": "exposure", "value": 0.7}
                    )
                )
                await asyncio.sleep(0.05)
                assert abs(node.get("exposure") - 0.7) < 1e-6

                # engine→UI: frame.preview broadcast
                fp = FramePreview(
                    node="cam1", w=8, h=8, fps=30.0, ms=1.0, format="jpeg", seq=1, data="AA"
                )
                await srv.broadcast(fp)
                got = json.loads(await ws.recv())
                assert got["type"] == "frame.preview" and got["node"] == "cam1"

    asyncio.run(scenario())


class _InNode(Processor):
    category = "vision"
    name = "In"
    inputs = ("in",)

    def process(self, ctx, inputs):
        return inputs.get("in")


def test_graph_edit_over_ws():
    async def scenario():
        from conode_engine.core.graph import Graph

        g = Graph()
        g.add(DemoNode("cam1", index=1))
        g.add(_InNode("v1", index=2))
        srv = EngineServer(graph=g)
        async with websockets.serve(srv.handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
                for _ in range(4):  # hello, node.list, graph.state, scene.list
                    await ws.recv()

                await ws.send(
                    json.dumps({"type": "node.connect", "v": 0, "src": "cam1", "dst": "v1", "port": "in"})
                )
                got = json.loads(await ws.recv())
                assert got["type"] == "graph.state"
                assert {"src": "cam1", "dst": "v1", "port": "in"} in got["edges"]

                await ws.send(json.dumps({"type": "graph.get", "v": 0}))
                st = json.loads(await ws.recv())
                assert st["type"] == "graph.state" and len(st["nodes"]) == 2

                await ws.send(json.dumps({"type": "node.disconnect", "v": 0, "dst": "v1", "port": "in"}))
                got2 = json.loads(await ws.recv())
                assert got2["type"] == "graph.state" and got2["edges"] == []

    asyncio.run(scenario())


def test_node_add_remove_over_ws():
    async def scenario():
        from conode_engine.core.graph import Graph

        g = Graph()
        g.add(DemoNode("cam1", index=1))
        srv = EngineServer(graph=g)
        async with websockets.serve(srv.handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
                for _ in range(4):  # hello, node.list, graph.state, scene.list
                    await ws.recv()

                await ws.send(
                    json.dumps({"type": "node.add", "v": 0, "node_type": "canny", "id": "canny1"})
                )
                st = json.loads(await ws.recv())
                assert any(n["id"] == "canny1" for n in st["nodes"])

                await ws.send(json.dumps({"type": "node.remove", "v": 0, "node": "canny1"}))
                st2 = json.loads(await ws.recv())
                assert not any(n["id"] == "canny1" for n in st2["nodes"])

    asyncio.run(scenario())
