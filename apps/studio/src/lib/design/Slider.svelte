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
	}
	let {
		label = '',
		value = $bindable(0),
		min = 0,
		max = 1,
		step = 0,
		unit = '',
		accent = 'var(--field-fill)'
	}: Props = $props();

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
		padding-right: calc(var(--space-unit) * 3);
		color: var(--text-hi);
		font-size: var(--fs-value);
		pointer-events: none;
	}
</style>
