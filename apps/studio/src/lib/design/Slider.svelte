<script lang="ts">
	// Slider · fill-bar (PLAN §0.3.3): 라벨이 채움 영역 안에, 값은 우측 정렬.
	interface Props {
		label?: string;
		value?: number;
		min?: number;
		max?: number;
		step?: number;
		unit?: string;
		/** 채움 색 — 노드 카테고리색 주입용. 기본 파생 토큰. */
		accent?: string;
		/** 모듈레이션 양 0..1 (있으면 우측에 도넛 링 표시, §3.3). */
		mod?: number;
	}
	let {
		label = '',
		value = $bindable(0),
		min = 0,
		max = 1,
		step = 0,
		unit = '',
		accent = 'var(--field-fill)',
		mod = undefined
	}: Props = $props();

	const CIRC = 43.98; // 2πr, r=7
	const modDash = $derived(mod == null ? 0 : Math.max(0, Math.min(1, mod)) * CIRC);

	let track = $state<HTMLDivElement>();
	let dragging = $state(false);

	const clamp = (v: number) => Math.min(max, Math.max(min, v));
	const snap = (v: number) => (step > 0 ? Math.round(v / step) * step : v);
	const pct = $derived(((clamp(value) - min) / (max - min)) * 100);

	const display = $derived.by(() => {
		const v = clamp(value);
		const s = step >= 1 || Number.isInteger(v) ? String(Math.round(v)) : v.toFixed(2);
		return unit ? `${s}${unit}` : s;
	});

	function setFromClientX(clientX: number) {
		if (!track) return;
		const r = track.getBoundingClientRect();
		const t = (clientX - r.left) / r.width;
		value = clamp(snap(min + Math.min(1, Math.max(0, t)) * (max - min)));
	}
	function onpointerdown(e: PointerEvent) {
		dragging = true;
		(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
		setFromClientX(e.clientX);
	}
	function onpointermove(e: PointerEvent) {
		if (dragging) setFromClientX(e.clientX);
	}
	function onpointerup(e: PointerEvent) {
		dragging = false;
		(e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
	}
	function onkeydown(e: KeyboardEvent) {
		const d = step > 0 ? step : (max - min) / 100;
		if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
			value = clamp(value + d);
			e.preventDefault();
		} else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
			value = clamp(value - d);
			e.preventDefault();
		}
	}
</script>

<div
	class="slider"
	class:dragging
	role="slider"
	tabindex="0"
	aria-label={label}
	aria-valuemin={min}
	aria-valuemax={max}
	aria-valuenow={value}
	bind:this={track}
	{onpointerdown}
	{onpointermove}
	{onpointerup}
	{onkeydown}
>
	<div class="fill" style="width: {pct}%; background: {accent};"></div>
	<span class="label">{label}</span>
	<span class="value mono">{display}</span>
	{#if mod != null}
		<svg class="modring" viewBox="0 0 20 20" aria-hidden="true">
			<circle class="mr-track" cx="10" cy="10" r="7" />
			<circle class="mr-arc" cx="10" cy="10" r="7" style="stroke-dasharray: {modDash} {CIRC};" />
		</svg>
	{/if}
</div>

<style>
	.slider {
		position: relative;
		height: var(--param-row-h);
		background: var(--bg-field);
		border-radius: var(--radius-field);
		overflow: hidden;
		cursor: ew-resize;
		user-select: none;
		display: flex;
		align-items: center;
		touch-action: none;
	}
	.slider:focus-visible {
		outline: var(--focus-w) solid var(--focus-ring);
		outline-offset: calc(-1 * var(--focus-w));
	}
	.fill {
		position: absolute;
		inset: 0 auto 0 0;
		opacity: 0.55;
	}
	.label {
		position: relative;
		z-index: 1;
		padding-left: calc(var(--space-unit) * 3);
		color: var(--text-hi);
		font-size: var(--fs-label);
		pointer-events: none;
		white-space: nowrap;
	}
	.value {
		position: relative;
		z-index: 1;
		margin-left: auto;
		padding-right: calc(var(--space-unit) * 2);
		color: var(--text-hi);
		font-size: var(--fs-value);
		pointer-events: none;
	}
	.modring {
		position: relative;
		z-index: 1;
		width: 16px;
		height: 16px;
		margin-right: calc(var(--space-unit) * 2);
		transform: rotate(-90deg);
		flex: none;
		pointer-events: none;
	}
	.mr-track {
		fill: none;
		stroke: var(--bg-canvas);
		stroke-width: 3;
	}
	.mr-arc {
		fill: none;
		stroke: var(--cat-audio);
		stroke-width: 3;
		stroke-linecap: round;
	}
</style>
