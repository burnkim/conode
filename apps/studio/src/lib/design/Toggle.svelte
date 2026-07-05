<script lang="ts">
	// Toggle — 파라미터 행 우측 정렬 스위치 (§5.3 `[ ○]`). 150ms ease-out.
	interface Props {
		label?: string;
		value?: boolean;
	}
	let { label = '', value = $bindable(false) }: Props = $props();

	function toggle() {
		value = !value;
	}
</script>

<div class="row">
	<span class="label">{label}</span>
	<button
		type="button"
		class="switch"
		class:on={value}
		role="switch"
		aria-checked={value}
		aria-label={label}
		onclick={toggle}
	>
		<span class="knob"></span>
	</button>
</div>

<style>
	.row {
		height: var(--param-row-h);
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 calc(var(--space-unit) * 3);
	}
	.label {
		color: var(--text-hi);
		font-size: var(--fs-label);
	}
	.switch {
		--sw-w: calc(var(--space-unit) * 9);
		--sw-h: calc(var(--space-unit) * 5);
		width: var(--sw-w);
		height: var(--sw-h);
		flex: none;
		border: none;
		border-radius: var(--sw-h);
		background: var(--bg-field);
		position: relative;
		cursor: pointer;
		padding: 0;
		transition: background var(--motion-fast);
	}
	.switch.on {
		background: var(--state-ok);
	}
	.switch:focus-visible {
		outline: var(--focus-w) solid var(--focus-ring);
		outline-offset: var(--space-unit);
	}
	.knob {
		position: absolute;
		top: 50%;
		left: calc(var(--space-unit) * 0.5);
		width: calc(var(--sw-h) - var(--space-unit));
		height: calc(var(--sw-h) - var(--space-unit));
		border-radius: 50%;
		background: var(--knob);
		transform: translateY(-50%);
		transition: transform var(--motion-fast);
	}
	.switch.on .knob {
		transform: translate(calc(var(--sw-w) - var(--sw-h)), -50%);
	}
</style>
