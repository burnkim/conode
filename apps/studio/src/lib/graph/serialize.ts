// 그래프 직렬화 (PLAN §9 src/lib/graph). 구조(node_type+edges) + UI 위치를
// localStorage 에 저장/복원. 저장→로드 왕복이 T14 완료조건.
import type { Edge, NodeInfo } from '$lib/protocol/messages';

export interface Pos {
	x: number;
	y: number;
}

export interface SavedGraph {
	version: 0;
	nodes: { id: string; node_type: string; x: number; y: number }[];
	edges: { src: string; dst: string; port: string }[];
}

const KEY = 'conode.graph.v0';

export function serialize(
	nodes: NodeInfo[],
	edges: Edge[],
	positions: Record<string, Pos>
): SavedGraph {
	return {
		version: 0,
		nodes: nodes.map((n) => ({
			id: n.id,
			node_type: n.node_type ?? '',
			x: positions[n.id]?.x ?? 0,
			y: positions[n.id]?.y ?? 0
		})),
		edges: edges.map((e) => ({ src: e.src, dst: e.dst, port: e.port }))
	};
}

export function saveGraph(nodes: NodeInfo[], edges: Edge[], positions: Record<string, Pos>): SavedGraph {
	const data = serialize(nodes, edges, positions);
	localStorage.setItem(KEY, JSON.stringify(data));
	return data;
}

export function loadGraph(): SavedGraph | null {
	const raw = localStorage.getItem(KEY);
	if (!raw) return null;
	try {
		return JSON.parse(raw) as SavedGraph;
	} catch {
		return null;
	}
}

export function savedPositions(saved: SavedGraph): Record<string, Pos> {
	const p: Record<string, Pos> = {};
	for (const n of saved.nodes) p[n.id] = { x: n.x, y: n.y };
	return p;
}
