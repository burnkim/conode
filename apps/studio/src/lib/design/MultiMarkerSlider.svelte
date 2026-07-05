<script lang="ts">
	// MultiMarkerSlider (PLAN §0.3.5 / §1.2 creativity): denoise step 구간을
	// 마커(예: 10/35/49)로 표기. 드래그는 track 이 처리(가장 가까운 마커), 키보드는
	// 각 마커 버튼에서. 마커는 이웃을 넘지 못한다(정렬 불변).
	interface Props {
		label?: string;
		min?: number;
		max?: number;
		markers?: number[];
		accent?: string;
	}
	let {
		label = '',
		min = 0,
		max = 50,
		markers = $bindable([10, 35, 49]),
		accent = 'var(--cat-generate)'
	}: Props = $props();

	let track = $state<HTMLDivElement>();
	let active = $state(-1);

	const posPct = (v: number) => ((v - min) / (max - min)) * 100;
	const segOpacity = (i: number) => Math.min(0.9, 0.2 + i * 0.22);

	function nearestMarker(clientX: number): number {
		if (!track) return -1;
		const r = track.getBoundingClientRect();
		const x = clientX - r.left;
		let best = 0;
		let bestD = Infinity;
		markers.forEach((m, i) => {
			const mx = ((m - min) / (max - min)) * r.width;
			const d = Math.abs(mx - x);
			if (d < bestD) {
				bestD = d;
				best = i;
			}
		});
		return best;
	}
	function moveActive(clientX: number) {
		if (active < 0 || !track) return;
		const r = track.getBoundingClientRect();
		const t = (clientX - r.left) / r.width;
		let v = Math.round(min + Math.min(1, Math.max(0, t)) * (max - min));
		const lo = active > 0 ? markers[active - 1] : min;
		const hi = active < markers.length - 1 ? markers[active + 1] : max;
		v = Math.min(hi, Math.max(lo, v));
		const next = [...markers];
		next[active] = v;
		markers = next;
	}
	function onpointerdown(e: PointerEvent) {
		active = nearestMarker(e.clientX);
		(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
		moveActive(e.clientX);
	}
	function onpointermove(e: PointerEvent) {
		if (active >= 0) moveActive(e.clientX);
	}
	function onpointerup(e: PointerEvent) {
		if (active >= 0) {
			(e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
			active = -1;
		}
	}
	function markerKeydown(i: number, e: KeyboardEvent) {
		const lo = i > 0 ? markers[i - 1] : min;
		const hi = i < markers.length - 1 ? markers[i + 1] : max;
		let v = markers[i];
		if (e.key === 'ArrowRight' || e.key === 'ArrowUp') v = Math.min(hi, v + 1);
		else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') v = Math.max(lo, v - 1);
		else return;
		e.preventDefault();
		const next = [...markers];
		next[i] = v;
		markers = next;
	}
</script>

<div class="mm">
	<div class="head">
		<span class="label">{label}</span>
		<span class="value mono">{markers.join(' / ')}</span>
	</div>
	<div
		class="track"
		role="group"
		aria-label="{label} markers"
		bind:this={track}
		{onpointerdown}
		{onpointermove}
		{onpointerup}
	>
		{#each markers as m, i (i)}
			<div
				class="seg"
				style="left: {i === 0 ? 0 : posPct(markers[i - 1])}%; width: {posPct(m) -
					(i === 0 ? 0 : posPct(markers[i - 1]))}%; background: {accent}; opacity: {segOpacity(i)};"
			></div>
		{/each}
		{#each markers as m, i (i)}
			<button
				type="button"
				class="marker"
				class:active={active === i}
				style="left: {posPct(m)}%;"
				role="slider"
				aria-label="{label} marker {i + 1}"
				aria-valuenow={m}
				aria-valuemin={min}
				aria-valuemax={max}
				onkeydown={(e) => markerKeydown(i, e)}
			>
				<span class="num mono">{m}</span>
			</button>
		{/each}
	</div>
</div>

<style>
	.mm {
		padding: calc(var(--space-unit) * 1.5) calc(var(--space-unit) * 3);
		user-select: none;
	}
	.head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		margin-bottom: calc(var(--space-unit) * 4);
	}
	.label {
		color: var(--text-hi);
		font-size: var(--fs-label);
	}
	.value {
		color: var(--text-lo);
		font-size: var(--fs-value);
	}
	.track {
		position: relative;
		height: calc(var(--space-unit) * 7);
		background: var(--bg-field);
		border-radius: var(--radius-field);
		touch-action: none;
		cursor: pointer;
	}
	.seg {
		position: absolute;
		top: 0;
		bottom: 0;
	}
	.seg:first-of-type {
		border-top-left-radius: var(--radius-field);
		border-bottom-left-radius: var(--radius-field);
	}
	.marker {
		position: absolute;
		top: calc(-1 * var(--space-unit));
		bottom: calc(-1 * var(--space-unit));
		transform: translateX(-50%);
		width: calc(var(--space-unit) * 0.75);
		background: var(--knob);
		border: none;
		border-radius: var(--space-unit);
		padding: 0;
		/* 드래그는 track 가 처리 — 마커는 시각+키보드 포커스만 */
		pointer-events: none;
	}
	.marker .num {
		position: absolute;
		top: calc(-4 * var(--space-unit));
		left: 50%;
		transform: translateX(-50%);
		font-size: var(--fs-value);
		color: var(--text-hi);
		background: var(--bg-card);
		border-radius: var(--radius-field);
		padding: 0 calc(var(--space-unit) * 1);
	}
	.marker.active {
		background: var(--focus-ring);
	}
	.marker.active .num {
		color: var(--focus-ring);
	}
	.marker:focus-visible {
		outline: var(--focus-w) solid var(--focus-ring);
	}
</style>
