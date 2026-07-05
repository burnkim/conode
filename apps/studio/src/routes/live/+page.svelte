<script lang="ts">
	// /live (T6) — Camera E2E. engine(ws://127.0.0.1:8787) → frame.preview →
	// NodeCard 인라인 프리뷰 + 실측 fps 배지. exposure/mirror 는 param.set 로 즉시 반영.
	// R1: 스타일 미선언 → design/ 클래스만. R5: 프리뷰 전용(최종 출력 아님).
	import { onDestroy, onMount } from 'svelte';
	import { NodeCard, Slider, Toggle } from '$lib/design';
	import { ConodeClient } from '$lib/protocol/client.svelte';
	import '$lib/design/gallery.css';

	const client = new ConodeClient();

	let exposure = $state(0.5);
	let mirror = $state(true);

	onMount(() => client.connect());
	onDestroy(() => client.disconnect());

	// UI→engine: 파라미터 변경을 param.set 으로 송신 (연결 후에만)
	$effect(() => {
		const v = exposure;
		if (client.status === 'open') client.setParam('cam1', 'exposure', v);
	});
	$effect(() => {
		const v = mirror;
		if (client.status === 'open') client.setParam('cam1', 'mirror', v);
	});

	const cam = $derived(client.nodes.find((n) => n.id === 'cam1'));
	const frame = $derived(client.frames['cam1']);
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode · live</h1>
		<p class="dg-sub mono">M0 · T6 — Camera E2E (engine → WS → NodeCard 프리뷰 · 실측 fps)</p>
		<nav class="dg-nav mono">
			<a href="/design">design</a>
			<a href="/nodes">nodes</a>
			<a href="/live">live</a>
		</nav>
		<div class="dg-status mono" class:open={client.status === 'open'} class:closed={client.status === 'closed'}>
			<span class="dot"></span>engine: {client.status}
			{#if frame}· {frame.fps}fps · seq {frame.seq}{/if}
			{#if client.rejected}· rejected {client.rejected}{/if}
		</div>
	</header>

	<section class="dg-section">
		<h2 class="dg-section-title">Camera</h2>
		<div class="dg-nodes">
			<NodeCard
				category="input"
				name={cam?.name ?? 'Camera'}
				index={cam?.index ?? 1}
				connected={client.status === 'open'}
				perf={{
					w: frame?.w,
					h: frame?.h,
					fps: frame ? Math.round(frame.fps) : undefined,
					ms: frame?.ms,
					fpsMode: 'auto'
				}}
			>
				<Slider label="exposure" bind:value={exposure} min={0} max={1} step={0.01} accent="var(--cat-input)" />
				<Toggle label="mirror" bind:value={mirror} />
				{#snippet preview()}
					{#if frame}
						<img class="dg-preview-img" src={frame.url} alt="camera preview" />
					{/if}
				{/snippet}
			</NodeCard>
		</div>
	</section>
</div>
