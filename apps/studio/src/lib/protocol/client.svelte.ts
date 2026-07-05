// conode WS 클라이언트 (T6). engine 과의 계약은 zod 스키마로만 검증 (R3).
// Svelte 5 룬 모듈(.svelte.ts) — 상태는 반응형.
import { Message, type NodeInfo } from './messages';

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

	setParam(node: string, path: string, value: number | string | boolean): void {
		if (this.#ws?.readyState === WebSocket.OPEN) {
			this.#ws.send(JSON.stringify({ type: 'param.set', v: 0, node, path, value }));
		}
	}

	disconnect(): void {
		this.#ws?.close();
		this.#ws = undefined;
	}
}
