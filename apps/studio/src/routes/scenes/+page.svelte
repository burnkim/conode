<script lang="ts">
	// /scenes (D) — 씬/큐. 현재 파라미터 상태를 씬으로 저장, fade 초 크로스페이드 recall.
	// R1: 스타일 미선언 → design/ 클래스만.
	import { onDestroy, onMount } from 'svelte';
	import { Slider, Text } from '$lib/design';
	import { ConodeClient } from '$lib/protocol/client.svelte';
	import '$lib/design/gallery.css';
	import '$lib/design/graph.css';

	const client = new ConodeClient();
	onMount(() => client.connect());
	onDestroy(() => client.disconnect());

	let name = $state('');
	let fade = $state(1.0);

	function save() {
		if (name.trim()) {
			client.saveScene(name.trim());
			name = '';
		}
	}
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode · scenes</h1>
		<p class="dg-sub mono">M-D — 씬/큐 · 파라미터 스냅샷 + 크로스페이드 recall (§0.2)</p>
		<nav class="dg-nav mono">
			<a href="/live">live</a>
			<a href="/graph">graph</a>
			<a href="/audio">audio</a>
			<a href="/output">output</a>
			<a href="/scenes">scenes</a>
		</nav>
		<div class="dg-status mono" class:open={client.status === 'open'} class:closed={client.status === 'closed'}>
			<span class="dot"></span>engine: {client.status} · {client.scenes.length} scenes
		</div>
	</header>

	<section class="dg-section">
		<h2 class="dg-section-title">저장</h2>
		<div class="dg-widget">
			<Text label="scene name" bind:value={name} placeholder="예: intro, drop, outro" />
			<Slider label="fade (s)" bind:value={fade} min={0} max={5} step={0.1} accent="var(--cat-output)" />
			<div class="gx-actions">
				<button class="gx-btn" onclick={save}>save current params</button>
			</div>
		</div>
	</section>

	<section class="dg-section">
		<h2 class="dg-section-title">Recall (fade {fade.toFixed(1)}s)</h2>
		<div class="gx-actions">
			{#each client.scenes as s (s)}
				<button class="gx-btn" onclick={() => client.recallScene(s, fade)}>▶ {s}</button>
			{/each}
			{#if client.scenes.length === 0}
				<span class="dg-sub mono">저장된 씬 없음 — /live 에서 파라미터 조정 후 여기서 save.</span>
			{/if}
		</div>
	</section>
</div>
