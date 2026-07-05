<script lang="ts">
	// /quad (T13) — 쿼드뷰. 비전 노드 4개 프리뷰를 2x2 모니터링 레이아웃으로.
	// R1: 스타일 미선언 → design/ 클래스만.
	import { onDestroy, onMount } from 'svelte';
	import { ConodeClient } from '$lib/protocol/client.svelte';
	import '$lib/design/gallery.css';

	const client = new ConodeClient();
	onMount(() => client.connect());
	onDestroy(() => client.disconnect());

	// 소스(camera) 제외한 처리 노드 4개
	const panes = $derived(client.nodes.filter((n) => n.category !== 'input').slice(0, 4));
	const pad = $derived(Array.from({ length: Math.max(0, 4 - panes.length) }));

	function health(fps?: number): string {
		if (fps == null) return '';
		return fps >= 24 ? 'ok' : fps >= 15 ? 'warn' : 'error';
	}
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode · quad</h1>
		<p class="dg-sub mono">M1 · T13 — 쿼드뷰 (vision 4-up)</p>
		<nav class="dg-nav mono">
			<a href="/design">design</a>
			<a href="/nodes">nodes</a>
			<a href="/live">live</a>
			<a href="/quad">quad</a>
		</nav>
		<div
			class="dg-status mono"
			class:open={client.status === 'open'}
			class:closed={client.status === 'closed'}
		>
			<span class="dot"></span>engine: {client.status} · {panes.length}/4 vision nodes
		</div>
	</header>

	<section class="dg-section">
		<div class="dg-quad">
			{#each panes as node (node.id)}
				{@const f = client.frames[node.id]}
				<div class="dg-quad-cell">
					{#if f}
						<img src={f.url} alt="{node.name} preview" />
					{:else}
						<div class="dg-quad-empty mono">no signal</div>
					{/if}
					<div class="dg-quad-overlay">
						<span class="dg-quad-label">{node.name}</span>
						{#if f}
							<span class="dg-quad-fps mono {health(f.fps)}">{Math.round(f.fps)}fps</span>
						{/if}
					</div>
				</div>
			{/each}
			{#each pad as _, i (i)}
				<div class="dg-quad-cell"><div class="dg-quad-empty mono">—</div></div>
			{/each}
		</div>
	</section>
</div>
