"""Graph — 노드 + 연결. topo 순서로 평가하며 노드간 프레임을 전달 (PLAN §1.2).

edges: dst_id → {port: src_id}. 사이클은 거부한다. evaluate() 는 매 tick 마다
위상 순서로 각 노드에 업스트림 output 을 inputs 로 넣어 tick 한다.
"""
from __future__ import annotations

from collections import deque

from .processor import FrameCtx, Processor


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, Processor] = {}
        self.edges: dict[str, dict[str, str]] = {}  # dst → {port: src}

    def add(self, node: Processor) -> Processor:
        self.nodes[node.id] = node
        self.edges.setdefault(node.id, {})
        return node

    def remove(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)
        self.edges.pop(node_id, None)
        for ports in self.edges.values():
            for port, src in list(ports.items()):
                if src == node_id:
                    del ports[port]

    def connect(self, src_id: str, dst_id: str, port: str = "in") -> None:
        if src_id not in self.nodes or dst_id not in self.nodes:
            raise KeyError("unknown node")
        if port not in self.nodes[dst_id].inputs:
            raise ValueError(f"{dst_id} has no input port {port!r}")
        self.edges[dst_id][port] = src_id
        if self._has_cycle():
            del self.edges[dst_id][port]
            raise ValueError("connection would create a cycle")

    def disconnect(self, dst_id: str, port: str = "in") -> None:
        self.edges.get(dst_id, {}).pop(port, None)

    def topo(self) -> list[str]:
        indeg = {nid: 0 for nid in self.nodes}
        for dst, ports in self.edges.items():
            for src in ports.values():
                if src in self.nodes:
                    indeg[dst] += 1
        queue = deque(nid for nid, d in indeg.items() if d == 0)
        order: list[str] = []
        while queue:
            n = queue.popleft()
            order.append(n)
            for dst, ports in self.edges.items():
                if n in ports.values():
                    indeg[dst] -= 1
                    if indeg[dst] == 0:
                        queue.append(dst)
        return order

    def _has_cycle(self) -> bool:
        return len(self.topo()) != len(self.nodes)

    def evaluate(self, ctx: FrameCtx) -> None:
        for nid in self.topo():
            node = self.nodes[nid]
            inputs = {}
            for port, src in self.edges.get(nid, {}).items():
                src_node = self.nodes.get(src)
                inputs[port] = src_node.output if src_node else None
            node.tick(ctx, inputs)

    def describe(self) -> dict:
        return {
            "nodes": [n.describe() for n in self.nodes.values()],
            "edges": [
                {"src": src, "dst": dst, "port": port}
                for dst, ports in self.edges.items()
                for port, src in ports.items()
            ],
        }
