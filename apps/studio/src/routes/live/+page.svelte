<script lang="ts">
	// /live (T6/T8) — 그래프 라이브. engine(ws://127.0.0.1:8787) 의 모든 노드를
	// NodeCard 로 렌더(Camera→Canny). 각 노드 frame.preview → 인라인 프리뷰 + 실측 fps.
	// R1: 스타일 미선언 → design/ 클래스만. R5: 프리뷰 전용(최종 출력 아님).
	import { onDestroy, onMount } from 'svelte';
	import { NodeCard, Slider, Toggle } from '$lib/design';
	import { ConodeClient } from '$lib/protocol/client.svelte';
	import '$lib/design/gallery.css';

	const client = new ConodeClient();

	// camera controls
	let exposure = $state(0.5);
	let mirror = $state(true);
	// canny controls
	let cannyLow = $state(80);
	let cannyHigh = $state(160);

	onMount(() => client.connect());
	onDestroy(() => client.disconnect());

	// UI→engine param.set (연결 후에만)
	$effect(() => {
		const v = exposure;
		if (client.status === 'open') client.setParam('cam1', 'exposure', v);
	});
	$effect(() => {
		const v = mirror;
		if (client.status === 'open') client.setParam('cam1', 'mirror', v);
	});
	$effect(() => {
		const v = cannyLow;
		if (client.status === 'open') client.setParam('canny1', 'low', v);
	});
	$effect(() => {
		const v = cannyHigh;
		if (client.status === 'open') client.setParam('canny1', 'high', v);
	});
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode · live</h1>
		<p class="dg-sub mono">M1 — Vision pipeline · Camera → Canny · Pose · Depth · Segmentation</p>
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
			<span class="dot"></span>engine: {client.status} · {client.nodes.length} nodes
			{#if client.rejected}· rejected {client.rejected}{/if}
		</div>
	</header>

	<section class="dg-section">
		<h2 class="dg-section-title">Graph — Camera → 4 vision nodes</h2>
		<div class="dg-nodes">
			{#each client.nodes as node (node.id)}
				{@const f = client.frames[node.id]}
				<NodeCard
					category={node.category}
					name={node.name}
					index={node.index}
					connected={client.status === 'open'}
					perf={{
						w: f?.w,
						h: f?.h,
						fps: f ? Math.round(f.fps) : undefined,
						ms: f?.ms,
						fpsMode: 'auto'
					}}
				>
					{#if node.id === 'cam1'}
						<Slider label="exposure" bind:value={exposure} min={0} max={1} step={0.01} accent="var(--cat-input)" />
						<Toggle label="mirror" bind:value={mirror} />
					{:else if node.id === 'canny1'}
						<Slider label="low" bind:value={cannyLow} min={0} max={255} step={1} accent="var(--cat-vision)" />
						<Slider label="high" bind:value={cannyHigh} min={0} max={255} step={1} accent="var(--cat-vision)" />
					{/if}
					{#snippet preview()}
						{#if f}
							<img class="dg-preview-img" src={f.url} alt="{node.name} preview" />
						{/if}
					{/snippet}
				</NodeCard>
			{/each}
			{#if client.nodes.length === 0}
				<p class="dg-sub mono">엔진 연결 대기… (engine/.venv/bin/python -m conode_engine)</p>
			{/if}
		</div>
	</section>
</div>
