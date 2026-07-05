<script lang="ts">
	// NodeCard — 모든 노드의 고정 해부 구조 (PLAN §5.1 원칙1 / §5.3).
	// 예외 없음: 새 노드의 디자인 결정은 "헤더 색(category) + 파라미터(children)"뿐.
	import type { Snippet } from 'svelte';

	export type Category = 'input' | 'vision' | 'depth' | 'generate' | 'audio' | 'output';

	interface Perf {
		w?: number;
		h?: number;
		fps?: number;
		ms?: number;
		fpsMode?: string; // "auto" | 숫자
	}
	interface Props {
		category?: Category;
		name?: string;
		index?: number; // /processor/N/
		perf?: Perf;
		running?: boolean;
		connected?: boolean;
		children?: Snippet; // PARAMETERS 내용 (T2 위젯)
		preview?: Snippet; // 인라인 프리뷰 내용 (미지정 시 플레이스홀더)
	}
	let {
		category = 'generate',
		name = 'Node',
		index = 0,
		perf = {},
		running = $bindable(true),
		connected = true,
		children,
		preview
	}: Props = $props();

	// 성능 배지 상태 — fps 기준 (§5.1 원칙3: 병목은 앰버→레드).
	const health = $derived.by(() => {
		const f = perf.fps ?? 0;
		if (f >= 24) return 'ok';
		if (f >= 15) return 'warn';
		return 'error';
	});
	const perfText = $derived.by(() => {
		const res = perf.w && perf.h ? `${perf.w}x${perf.h}` : '—';
		const fps = perf.fps != null ? `${perf.fps}fps` : '';
		const ms = perf.ms != null ? `${perf.ms}ms` : '';
		return [res, fps, ms].filter(Boolean).join(' ');
	});
</script>

<div class="node" style="--cat: var(--cat-{category});">
	<header class="head">
		<div class="head-row top">
			<button
				class="icon pin"
				type="button"
				title="pin"
				aria-label="pin {name}">◆</button
			>
			<button
				class="icon play"
				type="button"
				title={running ? 'pause' : 'play'}
				aria-label={running ? 'pause' : 'play'}
				aria-pressed={running}
				onclick={() => (running = !running)}>{running ? '❚❚' : '▶'}</button
			>
			<span class="name">{name}</span>
			<span class="perf mono {health}" title="resolution · fps · frame time">{perfText}</span>
			<span class="conn" class:on={connected} title={connected ? 'connected' : 'idle'}>⚡</span>
		</div>
		<div class="head-row sub">
			<span class="path mono">/processor/{index}/</span>
			<span class="fpsmode mono">fps {perf.fpsMode ?? 'auto'}</span>
		</div>
	</header>

	<section class="params">
		<div class="section-label">PARAMETERS</div>
		<div class="rows">
			{#if children}{@render children()}{/if}
		</div>
	</section>

	<div class="preview">
		{#if preview}
			{@render preview()}
		{:else}
			<div class="preview-empty mono">no signal</div>
		{/if}
		<span class="monitor" aria-hidden="true" title="pop out">&#9707;</span>
	</div>
</div>

<style>
	.node {
		width: 100%;
		background: var(--bg-card);
		border-radius: var(--radius-card);
		overflow: hidden;
		border: var(--border-w) solid var(--field-border);
		display: flex;
		flex-direction: column;
	}

	/* --- 헤더 (h=56, 카테고리색 → 다크 그라디언트, §0.3.2) --- */
	.head {
		height: 56px;
		padding: 0 calc(var(--space-unit) * 3);
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: calc(var(--space-unit) * 1);
		background: linear-gradient(
			100deg,
			color-mix(in srgb, var(--cat) 60%, var(--bg-card)) 0%,
			var(--bg-card) 62%
		);
	}
	.head-row {
		display: flex;
		align-items: center;
		gap: calc(var(--space-unit) * 2);
	}
	.icon {
		border: none;
		background: transparent;
		color: var(--text-hi);
		cursor: pointer;
		font-size: 11px;
		padding: 0;
		line-height: 1;
		opacity: 0.85;
	}
	.icon:hover {
		opacity: 1;
	}
	.icon:focus-visible {
		outline: var(--focus-w) solid var(--focus-ring);
		outline-offset: var(--space-unit);
	}
	.play {
		color: var(--cat);
	}
	.name {
		color: var(--text-hi);
		font-size: var(--fs-label);
		font-weight: 600;
		margin-right: auto;
	}
	.perf {
		font-size: 11px;
		padding: calc(var(--space-unit) * 0.5) calc(var(--space-unit) * 1.5);
		border-radius: var(--radius-field);
		background: color-mix(in srgb, var(--bg-canvas) 70%, transparent);
	}
	.perf.ok {
		color: var(--state-ok);
	}
	.perf.warn {
		color: var(--state-warn);
	}
	.perf.error {
		color: var(--state-error);
	}
	.conn {
		font-size: 11px;
		color: var(--text-lo);
	}
	.conn.on {
		color: var(--state-warn);
	}
	.sub {
		opacity: 0.75;
	}
	.path {
		color: var(--text-lo);
		font-size: 11px;
		margin-right: auto;
	}
	.fpsmode {
		color: var(--text-lo);
		font-size: 11px;
	}

	/* --- PARAMETERS --- */
	.params {
		padding: calc(var(--space-unit) * 2) 0 calc(var(--space-unit) * 2);
		border-top: var(--border-w) solid var(--field-border);
	}
	.section-label {
		color: var(--text-lo);
		font-size: 10px;
		letter-spacing: 0.1em;
		padding: 0 calc(var(--space-unit) * 3) calc(var(--space-unit) * 2);
	}
	.rows {
		display: flex;
		flex-direction: column;
		gap: calc(var(--space-unit) * 1);
	}

	/* --- 인라인 프리뷰 16:9 --- */
	.preview {
		position: relative;
		aspect-ratio: 16 / 9;
		background: var(--bg-canvas);
		border-top: var(--border-w) solid var(--field-border);
		overflow: hidden;
	}
	.preview-empty {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-lo);
		font-size: 11px;
		opacity: 0.5;
	}
	.monitor {
		position: absolute;
		right: calc(var(--space-unit) * 2);
		bottom: calc(var(--space-unit) * 1);
		color: var(--text-lo);
		font-size: 12px;
		opacity: 0.6;
		pointer-events: none;
	}
</style>
