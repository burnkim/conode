<script lang="ts">
	// /audio (T29) — 오디오 12스템 ModMatrix. AudioIn 미터 → ModMatrix 적용 → LiveDiffusion.
	// R1: 스타일 미선언 → design/ 클래스만.
	import { onDestroy, onMount } from 'svelte';
	import { ConodeClient } from '$lib/protocol/client.svelte';
	import '$lib/design/gallery.css';

	const client = new ConodeClient();
	onMount(() => client.connect());
	onDestroy(() => client.disconnect());

	const ORDER = ['audio1', 'mod1', 'live1'];
	const LABELS: Record<string, string> = {
		audio1: 'AudioIn · 12 stems (rms 미터)',
		mod1: 'ModMatrix · applied targets',
		live1: 'LiveDiffusion · modulated'
	};
	const panes = $derived(
		ORDER.map((id) => client.nodes.find((n) => n.id === id)).filter((n) => n != null)
	);
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode · audio</h1>
		<p class="dg-sub mono">M4 — 12스템 ModMatrix · AudioIn → 특성 → ModMatrix → 파라미터 모듈레이션 (§3)</p>
		<nav class="dg-nav mono">
			<a href="/design">design</a>
			<a href="/nodes">nodes</a>
			<a href="/live">live</a>
			<a href="/quad">quad</a>
			<a href="/graph">graph</a>
			<a href="/audio">audio</a>
		</nav>
		<div class="dg-status mono" class:open={client.status === 'open'} class:closed={client.status === 'closed'}>
			<span class="dot"></span>engine: {client.status}
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
						<span class="dg-quad-label">{LABELS[node.id] ?? node.name}</span>
						{#if f}<span class="dg-quad-fps mono ok">{Math.round(f.fps)}fps</span>{/if}
					</div>
				</div>
			{/each}
			{#if panes.length === 0}
				<p class="dg-sub mono">엔진 연결 대기…</p>
			{/if}
		</div>
	</section>
</div>
