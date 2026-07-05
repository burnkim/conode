"""EngineServer — WS 서버 (PLAN §1.1). UI 와의 유일한 계약은 packages/schema (R3).

연결 시: hello(engine) → node.list 전송. 수신: param.set 을 노드에 적용.
engine→UI 프레임은 broadcast(FramePreview) (T6). 최종 출력은 UI 경유 금지(R5) —
여긴 프리뷰 전용 저지연 채널.
"""
from __future__ import annotations

import asyncio
import json
from typing import Iterable, Optional

import websockets

from ..core.processor import Processor
from .messages import (
    FramePreview,
    Hello,
    NodeInfo,
    NodeList,
    ParamSet,
    dump_message,
    parse_message,
)


class EngineServer:
    def __init__(
        self,
        nodes: Optional[Iterable[Processor]] = None,
        host: str = "127.0.0.1",
        port: int = 8787,
    ):
        self.host = host
        self.port = port
        self.nodes: dict[str, Processor] = {n.id: n for n in (nodes or [])}
        self.clients: set = set()

    def node_infos(self) -> list[NodeInfo]:
        return [
            NodeInfo(id=n.id, name=n.name, category=n.category, index=n.index)
            for n in self.nodes.values()
        ]

    async def handler(self, ws) -> None:
        self.clients.add(ws)
        try:
            await ws.send(json.dumps(dump_message(Hello(role="engine", app="conode-engine/0.0.0"))))
            await ws.send(json.dumps(dump_message(NodeList(nodes=self.node_infos()))))
            async for raw in ws:
                self._on_message(raw)
        except websockets.ConnectionClosed:
            pass
        finally:
            self.clients.discard(ws)

    def _on_message(self, raw: str) -> None:
        try:
            msg = parse_message(json.loads(raw))
        except Exception:
            return  # 스키마 위반 메시지는 무시 (R3)
        if isinstance(msg, ParamSet):
            node = self.nodes.get(msg.node)
            if node is not None:
                try:
                    node.set(msg.path, msg.value)
                except (KeyError, ValueError):
                    pass  # 알 수 없는 path/값은 조용히 무시

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
            await asyncio.Future()  # 영원히
