"""EngineServer — WS 서버 (PLAN §1.1). UI 와의 유일한 계약은 packages/schema (R3).

연결 시: hello(engine) → node.list → graph.state. 수신: param.set 적용,
graph.get/node.add/node.remove/node.connect/node.disconnect 로 그래프 편집(T9).
그래프 변경 시 graph.state 를 브로드캐스트한다. engine→UI 프레임은 broadcast(FramePreview).
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Iterable, Optional

import websockets

from ..core.graph import Graph
from ..core.processor import Processor
from ..core.scenes import SceneStore
from .messages import (
    Edge,
    FramePreview,
    GraphGet,
    GraphState,
    Hello,
    NodeAdd,
    NodeConnect,
    NodeDisconnect,
    NodeInfo,
    NodeList,
    NodeRemove,
    ParamSet,
    CueBind,
    SceneGet,
    SceneList,
    SceneRecall,
    SceneSave,
    dump_message,
    parse_message,
)


def node_registry() -> dict:
    """node_type → 클래스. 무거운 임포트(cv2/mediapipe)를 지연."""
    from ..nodes import (
        AudioIn, Blend, Camera, Canny, ColorGrade, Crossfade, Depth, FeedbackLoop,
        GestureRecognizer, HandTracker, Image, LiveDiffusion, MappedOutput, MaskCompose,
        ModMatrix, Pose, Recorder, RegionMask, Segmentation, StylePreset, Switch,
    )

    return {
        "camera": Camera, "image": Image, "canny": Canny, "pose": Pose,
        "depth": Depth, "segmentation": Segmentation, "hand_tracker": HandTracker,
        "gesture_recognizer": GestureRecognizer, "region_mask": RegionMask,
        "live_diffusion": LiveDiffusion, "audio_in": AudioIn, "mod_matrix": ModMatrix,
        "blend": Blend, "crossfade": Crossfade, "color_grade": ColorGrade,
        "switch": Switch, "mask_compose": MaskCompose, "feedback": FeedbackLoop,
        "style_preset": StylePreset, "mapped_output": MappedOutput, "recorder": Recorder,
    }


class EngineServer:
    def __init__(
        self,
        nodes: Optional[Iterable[Processor]] = None,
        graph: Optional[Graph] = None,
        host: str = "127.0.0.1",
        port: int = 8787,
    ):
        self.host = host
        self.port = port
        if graph is None:
            graph = Graph()
            for n in nodes or []:
                graph.add(n)
        self.graph = graph
        self.clients: set = set()
        self.scenes = SceneStore()  # D: 씬/큐

    @property
    def nodes(self) -> dict[str, Processor]:
        return self.graph.nodes

    def node_infos(self) -> list[NodeInfo]:
        return [
            NodeInfo(
                id=n.id,
                name=n.name,
                category=n.category,
                index=n.index,
                node_type=n.kind,
                inputs=list(n.inputs),
                params=n.store.describe(),  # R2: UI 자동생성용 ParamSpec + 현재값
            )
            for n in self.graph.nodes.values()
        ]

    def graph_state(self) -> GraphState:
        edges = [
            Edge(src=src, dst=dst, port=port)
            for dst, ports in self.graph.edges.items()
            for port, src in ports.items()
        ]
        return GraphState(nodes=self.node_infos(), edges=edges)

    async def handler(self, ws) -> None:
        self.clients.add(ws)
        try:
            await self._send(ws, Hello(role="engine", app="conode-engine/0.0.0"))
            await self._send(ws, NodeList(nodes=self.node_infos()))
            await self._send(ws, self.graph_state())
            await self._send(ws, SceneList(names=self.scenes.names()))
            async for raw in ws:
                await self._on_message(ws, raw)
        except websockets.ConnectionClosed:
            pass
        finally:
            self.clients.discard(ws)

    async def _send(self, ws, msg) -> None:
        await ws.send(json.dumps(dump_message(msg)))

    async def _on_message(self, ws, raw: str) -> None:
        try:
            msg = parse_message(json.loads(raw))
        except Exception:
            return  # 스키마 위반 메시지는 무시 (R3)

        if isinstance(msg, ParamSet):
            node = self.graph.nodes.get(msg.node)
            if node is not None:
                try:
                    node.set(msg.path, msg.value)
                except (KeyError, ValueError):
                    pass
        elif isinstance(msg, GraphGet):
            await self._send(ws, self.graph_state())
        elif isinstance(msg, NodeAdd):
            await self._add_node(msg)
        elif isinstance(msg, NodeRemove):
            await self._remove_node(msg)
        elif isinstance(msg, NodeConnect):
            try:
                self.graph.connect(msg.src, msg.dst, msg.port)
            except (KeyError, ValueError):
                return
            await self.broadcast(self.graph_state())
        elif isinstance(msg, NodeDisconnect):
            self.graph.disconnect(msg.dst, msg.port)
            await self.broadcast(self.graph_state())
        elif isinstance(msg, SceneSave):
            self.scenes.save(msg.name, self.graph)
            await self.broadcast(SceneList(names=self.scenes.names()))
        elif isinstance(msg, SceneRecall):
            self.scenes.recall(msg.name, self.graph, fade=float(msg.fade or 0.0), now=time.monotonic())
        elif isinstance(msg, SceneGet):
            await self._send(ws, SceneList(names=self.scenes.names()))
        elif isinstance(msg, CueBind):
            self.scenes.bind(msg.event, msg.scene, float(msg.fade or 0.0))

    async def _add_node(self, msg: NodeAdd) -> None:
        cls = node_registry().get(msg.node_type)
        if cls is None:
            return
        nid = msg.id or self._unique_id(msg.node_type)
        if nid in self.graph.nodes:
            return
        node = cls(nid, index=len(self.graph.nodes) + 1)
        if hasattr(node, "graph"):
            node.graph = self.graph  # ModMatrix 등 그래프 참조 노드
        # start()/stop()는 메인(이벤트 루프) 스레드에서 호출한다. MediaPipe/GL 객체는
        # 스레드 친화성이 있어 to_thread 로 생성/해제하면 세그폴트가 난다. 모델 로드
        # 블록(≈1s)은 허용.
        node.start()
        self.graph.add(node)
        await self.broadcast(self.graph_state())

    async def _remove_node(self, msg: NodeRemove) -> None:
        node = self.graph.nodes.get(msg.node)
        if node is None:
            return
        try:
            node.stop()
        except Exception:
            pass
        self.graph.remove(msg.node)
        await self.broadcast(self.graph_state())

    def _unique_id(self, node_type: str) -> str:
        n = 1
        while f"{node_type}{n}" in self.graph.nodes:
            n += 1
        return f"{node_type}{n}"

    async def broadcast(self, msg) -> None:
        if not self.clients:
            return
        raw = json.dumps(dump_message(msg))
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send(raw)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.clients.discard(d)

    async def serve_forever(self) -> None:
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()
