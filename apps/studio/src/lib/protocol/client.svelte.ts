// conode WS 클라이언트 (T6). engine 과의 계약은 zod 스키마로만 검증 (R3).
// Svelte 5 룬 모듈(.svelte.ts) — 상태는 반응형.
import { Message, type Edge, type NodeInfo } from './messages';

export interface FrameState {
	url: string; // data:image/<fmt>;base64,...
	w: number;
	h: number;
	fps: number;
	ms: number;
	seq: number;
}

export type ConnStatus = 'idle' | 'connecting' | 'open' | 'closed';

export class ConodeClient {
	status = $state<ConnStatus>('idle');
	nodes = $state<NodeInfo[]>([]);
	edges = $state<Edge[]>([]);
	scenes = $state<string[]>([]);
	frames = $state<Record<string, FrameState>>({});
	rejected = $state(0); // 스키마 위반으로 버린 메시지 수

	#ws?: WebSocket;
	#url: string;

	constructor(url = 'ws://127.0.0.1:8787') {
		this.#url = url;
	}

	connect(): void {
		if (this.#ws) return;
		this.status = 'connecting';
		const ws = new WebSocket(this.#url);
		this.#ws = ws;
		ws.onopen = () => (this.status = 'open');
		ws.onclose = () => (this.status = 'closed');
		ws.onerror = () => (this.status = 'closed');
		ws.onmessage = (ev) => this.#onMessage(ev.data);
	}

	#onMessage(raw: string): void {
		let data: unknown;
		try {
			data = JSON.parse(raw);
		} catch {
			this.rejected++;
			return;
		}
		const r = Message.safeParse(data);
		if (!r.success) {
			this.rejected++;
			return;
		}
		const msg = r.data;
		if (msg.type === 'node.list') {
			this.nodes = msg.nodes;
		} else if (msg.type === 'graph.state') {
			this.nodes = msg.nodes;
			this.edges = msg.edges;
		} else if (msg.type === 'scene.list') {
			this.scenes = msg.names;
		} else if (msg.type === 'frame.preview') {
			this.frames = {
				...this.frames,
				[msg.node]: {
					url: `data:image/${msg.format};base64,${msg.data}`,
					w: msg.w,
					h: msg.h,
					fps: msg.fps,
					ms: msg.ms,
					seq: msg.seq
				}
			};
		}
	}

	setParam(node: string, path: string, value: number | string | boolean | number[]): void {
		this.#send({ type: 'param.set', v: 0, node, path, value });
	}

	// --- 그래프 편집 (T9) — T14 UI 가 사용 ---
	getGraph(): void {
		this.#send({ type: 'graph.get', v: 0 });
	}
	addNode(nodeType: string, id?: string): void {
		this.#send(id ? { type: 'node.add', v: 0, node_type: nodeType, id } : { type: 'node.add', v: 0, node_type: nodeType });
	}
	removeNode(node: string): void {
		this.#send({ type: 'node.remove', v: 0, node });
	}
	connectNodes(src: string, dst: string, port = 'in'): void {
		this.#send({ type: 'node.connect', v: 0, src, dst, port });
	}
	disconnectNode(dst: string, port = 'in'): void {
		this.#send({ type: 'node.disconnect', v: 0, dst, port });
	}

	// --- 씬/큐 (D) ---
	saveScene(name: string): void {
		this.#send({ type: 'scene.save', v: 0, name });
	}
	recallScene(name: string, fade = 0): void {
		this.#send({ type: 'scene.recall', v: 0, name, fade });
	}

	#send(obj: unknown): void {
		if (this.#ws?.readyState === WebSocket.OPEN) {
			this.#ws.send(JSON.stringify(obj));
		}
	}

	disconnect(): void {
		this.#ws?.close();
		this.#ws = undefined;
	}
}
