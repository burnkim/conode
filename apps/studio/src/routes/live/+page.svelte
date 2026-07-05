<script lang="ts">
	// /live — 라이브 그래프. 엔진의 모든 노드를 NodeCard 로 렌더하고, 파라미터는
	// ParamPanel 로 ParamSpec 에서 자동 생성(R2). 하드코딩 컨트롤 없음.
	import { onDestroy, onMount } from 'svelte';
	import { NodeCard, ParamPanel } from '$lib/design';
	import { ConodeClient } from '$lib/protocol/client.svelte';
	import '$lib/design/gallery.css';

	const client = new ConodeClient();
	onMount(() => client.connect());
	onDestroy(() => client.disconnect());

	const specs = (n: { params?: Record<string, unknown> }) =>
		(n.params ?? {}) as Record<string, Record<string, unknown>>;
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode · live</h1>
		<p class="dg-sub mono">파라미터는 ParamSpec 에서 자동 생성 (R2) · Camera → 비전/제스처 → 디퓨전 → 오디오/출력</p>
		<nav class="dg-nav mono">
			<a href="/design">design</a>
			<a href="/nodes">nodes</a>
			<a href="/live">live</a>
			<a href="/quad">quad</a>
			<a href="/graph">graph</a>
			<a href="/audio">audio</a>
			<a href="/output">output</a>
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
		<h2 class="dg-section-title">Graph — 노드 {client.nodes.length}개 (파라미터 자동 생성)</h2>
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
					<ParamPanel params={specs(node)} node={node.id} {client} accent="var(--cat-{node.category})" />
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
