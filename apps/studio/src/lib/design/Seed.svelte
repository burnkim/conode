<script lang="ts">
	// Seed — 값 + mode(random/fixed) + 재생성 (PLAN §1.2 `Seed(mode=["random","fixed"])`).
	interface Props {
		label?: string;
		value?: number;
		mode?: 'random' | 'fixed';
	}
	let { label = 'seed', value = $bindable(0), mode = $bindable('random') }: Props = $props();

	const MAX = 2 ** 32 - 1;

	function randomize() {
		const buf = new Uint32Array(1);
		crypto.getRandomValues(buf);
		value = buf[0];
	}
</script>

<div class="row">
	<span class="label">{label}</span>
	<div class="controls">
		<input
			class="value mono"
			type="number"
			min="0"
			max={MAX}
			bind:value
			aria-label="{label} value"
		/>
		<div class="modes" role="group" aria-label="{label} mode">
			<button type="button" class:active={mode === 'fixed'} onclick={() => (mode = 'fixed')}>
				fixed
			</button>
			<button type="button" class:active={mode === 'random'} onclick={() => (mode = 'random')}>
				rnd
			</button>
		</div>
		<button type="button" class="dice" onclick={randomize} aria-label="randomize seed" title="randomize">
			⟳
		</button>
	</div>
</div>

<style>
	.row {
		min-height: var(--param-row-h);
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: calc(var(--space-unit) * 2);
		padding: 0 calc(var(--space-unit) * 3);
	}
	.label {
		color: var(--text-hi);
		font-size: var(--fs-label);
	}
	.controls {
		display: flex;
		align-items: center;
		gap: calc(var(--space-unit) * 1.5);
	}
	.value {
		width: calc(var(--space-unit) * 22);
		background: var(--bg-field);
		color: var(--text-hi);
		border: var(--border-w) solid var(--field-border);
		border-radius: var(--radius-field);
		font-size: var(--fs-value);
		padding: calc(var(--space-unit) * 1) calc(var(--space-unit) * 2);
		text-align: right;
	}
	.value:focus-visible {
		outline: var(--focus-w) solid var(--focus-ring);
		outline-offset: var(--border-w);
	}
	.modes {
		display: inline-flex;
		background: var(--bg-field);
		border: var(--border-w) solid var(--field-border);
		border-radius: var(--radius-field);
		overflow: hidden;
	}
	.modes button {
		border: none;
		background: transparent;
		color: var(--text-lo);
		font-size: var(--fs-value);
		padding: calc(var(--space-unit) * 1) calc(var(--space-unit) * 2);
		cursor: pointer;
		transition: background var(--motion-fast);
	}
	.modes button.active {
		background: var(--field-fill);
		color: var(--text-hi);
	}
	.dice {
		border: var(--border-w) solid var(--field-border);
		background: var(--bg-field);
		color: var(--text-hi);
		border-radius: var(--radius-field);
		width: calc(var(--space-unit) * 6);
		height: calc(var(--space-unit) * 6);
		cursor: pointer;
		font-size: var(--fs-label);
		transition: background var(--motion-fast);
	}
	.dice:hover {
		background: var(--field-hover);
	}
	.dice:focus-visible,
	.modes button:focus-visible {
		outline: var(--focus-w) solid var(--focus-ring);
		outline-offset: var(--border-w);
	}
</style>
