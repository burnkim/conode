"""EngineServer — WS 서버 (PLAN §1.1). UI 와의 유일한 계약은 packages/schema (R3).

연결 시: hello(engine) → node.list → graph.state. 수신: param.set 적용,
graph.get/node.add/node.remove/node.connect/node.disconnect 로 그래프 편집(T9).
그래프 변경 시 graph.state 를 브로드캐스트한다. engine→UI 프레임은 broadcast(FramePreview).
"""
from __future__ import annotations

import asyncio
import json
from typing import Iterable, Optional

import websockets

from ..core.graph import Graph
from ..core.processor import Processor
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
    dump_message,
    parse_message,
)


def node_registry() -> dict:
    """node_type → 클래스. 무거운 임포트(cv2/mediapipe)를 지연."""
    from ..nodes.camera import Camera
    from ..nodes.canny import Canny
    from ..nodes.depth import Depth
    from ..nodes.gesture_recognizer import GestureRecognizer
    from ..nodes.hand_tracker import HandTracker
    from ..nodes.live_diffusion import LiveDiffusion
    from ..nodes.pose import Pose
    from ..nodes.region_mask import RegionMask
    from ..nodes.segmentation import Segmentation

    return {
        "camera": Camera,
        "canny": Canny,
        "depth": Depth,
        "pose": Pose,
        "segmentation": Segmentation,
        "live_diffusion": LiveDiffusion,
        "hand_tracker": HandTracker,
        "gesture_recognizer": GestureRecognizer,
        "region_mask": RegionMask,
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

    async def _add_node(self, msg: NodeAdd) -> None:
        cls = node_registry().get(msg.node_type)
        if cls is None:
            return
        nid = msg.id or self._unique_id(msg.node_type)
        if nid in self.graph.nodes:
            return
        node = cls(nid, index=len(self.graph.nodes) + 1)
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
