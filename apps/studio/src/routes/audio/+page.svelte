<script lang="ts">
	// /audio (T29 + 매트릭스 에디터) — 12스템 ModMatrix. 미터 프리뷰 + 셀 편집.
	// R1: 스타일 미선언 → design/ 클래스만. R3: 편집은 modmatrix.* 스키마로만.
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

	// 엔진 연결되면 매트릭스 상태 1회 요청
	$effect(() => {
		if (client.status === 'open' && client.modMatrix === null) client.getModMatrix();
	});

	const mm = $derived(client.modMatrix);
	const shortTarget = (t: string) => t; // 'nodeId.path' 그대로

	// 새 셀 입력 상태
	let nSource = $state('');
	let nTarget = $state('');
	let nAmount = $state(0.5);
	let nCurve = $state('lin');

	function addCell() {
		if (!mm || !nSource || !nTarget) return;
		client.setModCell(mm.node, nSource, nTarget, nAmount, nCurve, 50);
		nSource = '';
		nTarget = '';
	}
	function editAmount(source: string, target: string, curve: string, v: number) {
		if (!mm) return;
		client.setModCell(mm.node, source, target, v, curve, 50);
	}
	function editCurve(source: string, target: string, amount: number, curve: string) {
		if (!mm) return;
		client.setModCell(mm.node, source, target, amount, curve, 50);
	}
	function remove(source: string, target: string) {
		if (!mm) return;
		client.clearModCell(mm.node, source, target);
	}
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode · audio</h1>
		<p class="dg-sub mono">M4 — 12스템 ModMatrix · 소스(스템×특성/LFO/제스처) → modulatable 파라미터 (§3)</p>
		<nav class="dg-nav mono">
			<a href="/live">live</a>
			<a href="/quad">quad</a>
			<a href="/graph">graph</a>
			<a href="/audio">audio</a>
			<a href="/output">output</a>
			<a href="/scenes">scenes</a>
		</nav>
		<div class="dg-status mono" class:open={client.status === 'open'} class:closed={client.status === 'closed'}>
			<span class="dot"></span>engine: {client.status}
			{#if mm}· {mm.cells.length} cells · {mm.sources.length} src × {mm.targets.length} tgt{/if}
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

	<section class="dg-section">
		<h2 class="dg-section-title">매트릭스 에디터 — 셀 (source → target)</h2>
		{#if !mm}
			<p class="dg-sub mono">엔진 연결 대기 — ModMatrix 노드 필요.</p>
		{:else}
			<div class="mm-editor">
				<div class="mm-row mm-head mono">
					<span>source</span><span>target</span><span>amount</span><span>curve</span><span></span>
				</div>

				{#each mm.cells as c (c.source + '→' + c.target)}
					<div class="mm-row card mono">
						<span class="mm-src">{c.source}</span>
						<span class="mm-tgt">{shortTarget(c.target)}</span>
						<input
							class="mm-num"
							type="number"
							min="-1"
							max="1"
							step="0.05"
							value={c.amount}
							onchange={(e) => editAmount(c.source, c.target, c.curve, parseFloat(e.currentTarget.value))}
						/>
						<select class="mm-select" value={c.curve} onchange={(e) => editCurve(c.source, c.target, c.amount, e.currentTarget.value)}>
							{#each mm.curves as cv (cv)}<option value={cv}>{cv}</option>{/each}
						</select>
						<button class="mm-rm" onclick={() => remove(c.source, c.target)}>✕</button>
					</div>
				{/each}
				{#if mm.cells.length === 0}
					<p class="dg-sub mono">셀 없음 — 아래에서 소스→타깃 추가.</p>
				{/if}

				<div class="mm-row card mono">
					<select class="mm-select" bind:value={nSource}>
						<option value="" disabled>source…</option>
						{#each mm.sources as s (s)}<option value={s}>{s}</option>{/each}
					</select>
					<select class="mm-select" bind:value={nTarget}>
						<option value="" disabled>target…</option>
						{#each mm.targets as t (t)}<option value={t}>{t}</option>{/each}
					</select>
					<input class="mm-num" type="number" min="-1" max="1" step="0.05" bind:value={nAmount} />
					<select class="mm-select" bind:value={nCurve}>
						{#each mm.curves as cv (cv)}<option value={cv}>{cv}</option>{/each}
					</select>
					<button class="mm-btn" onclick={addCell} disabled={!nSource || !nTarget}>+ add</button>
				</div>
			</div>
		{/if}
	</section>
</div>
