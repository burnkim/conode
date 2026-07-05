<script lang="ts">
	// /output (T32) — 코너핀 매핑 에디터. MappedOutput 프리뷰 위 4코너 드래그 → param.set.
	// R1: 스타일 미선언 → design/ 클래스만.
	import { onDestroy, onMount } from 'svelte';
	import { ConodeClient } from '$lib/protocol/client.svelte';
	import '$lib/design/gallery.css';
	import '$lib/design/graph.css';

	const NODE = 'mapped1';
	const client = new ConodeClient();
	onMount(() => client.connect());
	onDestroy(() => client.disconnect());

	type C = { x: number; y: number };
	const ORDER = ['tl', 'tr', 'br', 'bl'] as const;
	let corners = $state<Record<string, C>>({
		tl: { x: 0, y: 0 },
		tr: { x: 1, y: 0 },
		br: { x: 1, y: 1 },
		bl: { x: 0, y: 1 }
	});
	let box = $state<HTMLDivElement>();
	let drag = $state<string | null>(null);

	const frame = $derived(client.frames[NODE]);
	const quad = $derived(ORDER.map((k) => `${corners[k].x * 100},${corners[k].y * 100}`).join(' '));

	function down(e: PointerEvent, key: string) {
		drag = key;
		box!.setPointerCapture(e.pointerId);
	}
	function move(e: PointerEvent) {
		if (!drag || !box) return;
		const r = box.getBoundingClientRect();
		const x = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
		const y = Math.max(0, Math.min(1, (e.clientY - r.top) / r.height));
		corners = { ...corners, [drag]: { x, y } };
		if (client.status === 'open') {
			client.setParam(NODE, `corners.${drag}_x`, x);
			client.setParam(NODE, `corners.${drag}_y`, y);
		}
	}
	function up() {
		drag = null;
	}
	function reset() {
		corners = { tl: { x: 0, y: 0 }, tr: { x: 1, y: 0 }, br: { x: 1, y: 1 }, bl: { x: 0, y: 1 } };
		for (const k of ORDER) {
			client.setParam(NODE, `corners.${k}_x`, corners[k].x);
			client.setParam(NODE, `corners.${k}_y`, corners[k].y);
		}
	}
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode · output</h1>
		<p class="dg-sub mono">M5 — 프로젝션 매핑 · 코너핀 4점 (드래그) (§4)</p>
		<nav class="dg-nav mono">
			<a href="/design">design</a>
			<a href="/live">live</a>
			<a href="/graph">graph</a>
			<a href="/audio">audio</a>
			<a href="/output">output</a>
		</nav>
		<div class="dg-status mono" class:open={client.status === 'open'} class:closed={client.status === 'closed'}>
			<span class="dot"></span>engine: {client.status}
			<button class="gx-btn" style="margin-left:8px" onclick={reset}>reset corners</button>
		</div>
	</header>

	<section class="dg-section">
		<h2 class="dg-section-title">MappedOutput · 코너를 드래그해 워프</h2>
		<div
			class="dg-map"
			bind:this={box}
			role="application"
			aria-label="corner-pin editor"
			onpointermove={move}
			onpointerup={up}
		>
			{#if frame}
				<img src={frame.url} alt="mapped output" />
			{/if}
			<svg class="dg-map-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
				<polygon class="dg-map-quad" points={quad} />
			</svg>
			{#each ORDER as k (k)}
				<div
					class="dg-map-handle"
					style="left: {corners[k].x * 100}%; top: {corners[k].y * 100}%;"
					role="button"
					tabindex="-1"
					aria-label="corner {k}"
					onpointerdown={(e) => down(e, k)}
					onkeydown={() => {}}
				></div>
			{/each}
		</div>
	</section>
</div>
