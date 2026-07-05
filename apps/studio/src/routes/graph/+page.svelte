<script lang="ts">
	// /graph (T14) — 노드 그래프 편집기. 드래그 배치 + 포트 연결 + 삭제 + 저장/로드.
	// 엔진 그래프(client.nodes/edges)가 구조의 원천, 위치는 UI(localStorage). R1: design/graph.css 만.
	import { onDestroy, onMount } from 'svelte';
	import { ConodeClient } from '$lib/protocol/client.svelte';
	import { loadGraph, saveGraph, savedPositions, type Pos } from '$lib/graph/serialize';
	import '$lib/design/graph.css';

	const NODE_W = 184;
	const PORT_Y = 30; // 노드 상단에서 포트 중심까지(px)
	const PALETTE = ['camera', 'canny', 'pose', 'depth', 'segmentation'];

	const client = new ConodeClient();
	let canvasEl = $state<HTMLDivElement>();

	let positions = $state<Record<string, Pos>>({});
	let selected = $state<string | null>(null);
	let drag = $state<{ id: string; dx: number; dy: number } | null>(null);
	let link = $state<{ src: string; x: number; y: number } | null>(null);
	let status = $state('');

	onMount(() => {
		const saved = loadGraph();
		if (saved) positions = savedPositions(saved);
		client.connect();
	});
	onDestroy(() => client.disconnect());

	// 새 노드는 자동 배치
	$effect(() => {
		const nodes = client.nodes;
		let changed = false;
		const next = { ...positions };
		nodes.forEach((n, i) => {
			if (!next[n.id]) {
				next[n.id] =
					n.category === 'input'
						? { x: 40, y: 80 }
						: { x: 340, y: 30 + (i - 1) * 108 };
				changed = true;
			}
		});
		if (changed) positions = next;
	});

	function rel(e: PointerEvent): Pos {
		const r = canvasEl!.getBoundingClientRect();
		return { x: e.clientX - r.left, y: e.clientY - r.top };
	}
	const catVar = (cat: string) => `var(--cat-${cat})`;
	const catOf = (id: string) => client.nodes.find((n) => n.id === id)?.category ?? 'generate';
	const outAnchor = (id: string): Pos => {
		const p = positions[id];
		return p ? { x: p.x + NODE_W, y: p.y + PORT_Y } : { x: 0, y: 0 };
	};
	const inAnchor = (id: string): Pos => {
		const p = positions[id];
		return p ? { x: p.x, y: p.y + PORT_Y } : { x: 0, y: 0 };
	};
	function edgePath(a: Pos, b: Pos): string {
		const dx = Math.max(40, Math.abs(b.x - a.x) * 0.5);
		return `M ${a.x} ${a.y} C ${a.x + dx} ${a.y}, ${b.x - dx} ${b.y}, ${b.x} ${b.y}`;
	}

	function nodeDown(e: PointerEvent, id: string) {
		e.stopPropagation();
		selected = id;
		const p = positions[id];
		const m = rel(e);
		drag = { id, dx: m.x - p.x, dy: m.y - p.y };
		canvasEl!.setPointerCapture(e.pointerId);
	}
	function portDown(e: PointerEvent, id: string) {
		e.stopPropagation();
		const m = rel(e);
		link = { src: id, x: m.x, y: m.y };
		canvasEl!.setPointerCapture(e.pointerId);
	}
	function canvasMove(e: PointerEvent) {
		if (drag) {
			const m = rel(e);
			positions = { ...positions, [drag.id]: { x: m.x - drag.dx, y: m.y - drag.dy } };
		} else if (link) {
			const m = rel(e);
			link = { ...link, x: m.x, y: m.y };
		}
	}
	function canvasUp(e: PointerEvent) {
		if (link) {
			const el = document.elementFromPoint(e.clientX, e.clientY);
			const port = el?.closest('.gx-in') as HTMLElement | null;
			const dst = port?.getAttribute('data-node');
			const p = port?.getAttribute('data-port') ?? 'in';
			if (dst && dst !== link.src) client.connectNodes(link.src, dst, p);
		}
		drag = null;
		link = null;
	}

	function removeNode(id: string) {
		client.removeNode(id);
		const next = { ...positions };
		delete next[id];
		positions = next;
		if (selected === id) selected = null;
	}
	function save() {
		const d = saveGraph(client.nodes, client.edges, positions);
		status = `saved ${d.nodes.length} nodes / ${d.edges.length} edges`;
	}
	async function load() {
		const saved = loadGraph();
		if (!saved) {
			status = 'no saved graph';
			return;
		}
		for (const n of [...client.nodes]) client.removeNode(n.id);
		await new Promise((r) => setTimeout(r, 200));
		for (const n of saved.nodes) client.addNode(n.node_type, n.id);
		await new Promise((r) => setTimeout(r, 500));
		for (const e of saved.edges) client.connectNodes(e.src, e.dst, e.port);
		positions = savedPositions(saved);
		status = `loaded ${saved.nodes.length} nodes / ${saved.edges.length} edges`;
	}
</script>

<div class="gx-page">
	<div class="gx-header">
		<div>
			<h1 class="dg-h1">conode · graph</h1>
			<p class="dg-sub mono">M1 · T14 — node graph editor</p>
		</div>
		<nav class="dg-nav mono">
			<a href="/design">design</a>
			<a href="/nodes">nodes</a>
			<a href="/live">live</a>
			<a href="/quad">quad</a>
			<a href="/graph">graph</a>
		</nav>
	</div>

	<div class="gx-toolbar">
		<div class="gx-palette">
			{#each PALETTE as t (t)}
				<button class="gx-btn" onclick={() => client.addNode(t)}>+ {t}</button>
			{/each}
		</div>
		<div class="gx-actions">
			<button class="gx-btn" onclick={save}>save</button>
			<button class="gx-btn" onclick={load}>load</button>
			{#if selected}
				<button class="gx-btn gx-danger" onclick={() => removeNode(selected!)}>delete “{selected}”</button>
			{/if}
			<span class="gx-status mono">{status || `engine: ${client.status} · ${client.nodes.length} nodes`}</span>
		</div>
	</div>

	<div
		class="gx-canvas"
		bind:this={canvasEl}
		onpointermove={canvasMove}
		onpointerup={canvasUp}
		onpointerdown={() => (selected = null)}
		role="application"
		aria-label="node graph canvas"
	>
		<svg class="gx-edges">
			{#each client.edges as e (e.src + '>' + e.dst + ':' + e.port)}
				{@const a = outAnchor(e.src)}
				{@const b = inAnchor(e.dst)}
				<path class="gx-edge" d={edgePath(a, b)} style="stroke: {catVar(catOf(e.src))}" />
				<path
					class="gx-edge-hit"
					d={edgePath(a, b)}
					role="button"
					aria-label="disconnect {e.dst}"
					tabindex="-1"
					onclick={() => client.disconnectNode(e.dst, e.port)}
					onkeydown={(ev) => ev.key === 'Enter' && client.disconnectNode(e.dst, e.port)}
				/>
			{/each}
			{#if link}
				{@const a = outAnchor(link.src)}
				<path class="gx-edge gx-edge-live" d={edgePath(a, { x: link.x, y: link.y })} style="stroke: {catVar(catOf(link.src))}" />
			{/if}
		</svg>

		{#each client.nodes as node (node.id)}
			{@const p = positions[node.id]}
			{#if p}
				<div
					class="gx-node"
					class:sel={selected === node.id}
					style="left: {p.x}px; top: {p.y}px; width: {NODE_W}px; --cat: {catVar(node.category)}; --port-y: {PORT_Y}px;"
				>
					<div class="gx-node-head" onpointerdown={(e) => nodeDown(e, node.id)} role="presentation">
						<span class="gx-node-name">{node.name}</span>
						<button
							class="gx-x"
							aria-label="delete {node.id}"
							onpointerdown={(e) => e.stopPropagation()}
							onclick={() => removeNode(node.id)}>✕</button
						>
					</div>
					<div class="gx-node-body mono">/processor/{node.index}/</div>
					{#if (node.inputs ?? []).length}
						<div class="gx-port gx-in" data-node={node.id} data-port={(node.inputs ?? ['in'])[0]}></div>
					{/if}
					<div
						class="gx-port gx-out"
						role="button"
						aria-label="connect from {node.id}"
						tabindex="-1"
						onpointerdown={(e) => portDown(e, node.id)}
					></div>
				</div>
			{/if}
		{/each}
	</div>
</div>
