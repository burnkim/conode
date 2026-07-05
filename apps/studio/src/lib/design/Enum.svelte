<script lang="ts">
	// Enum — 드롭다운 (§5.3 `[Enum ▾]`). 네이티브 select 를 토큰으로 스타일.
	interface Props {
		label?: string;
		value?: string;
		options?: string[];
	}
	let { label = '', value = $bindable(''), options = [] }: Props = $props();
</script>

<div class="row">
	<span class="label">{label}</span>
	<div class="select-wrap">
		<select bind:value aria-label={label}>
			{#each options as opt (opt)}
				<option value={opt}>{opt}</option>
			{/each}
		</select>
		<span class="chevron" aria-hidden="true">▾</span>
	</div>
</div>

<style>
	.row {
		height: var(--param-row-h);
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
	.select-wrap {
		position: relative;
		display: inline-flex;
		align-items: center;
	}
	select {
		appearance: none;
		-webkit-appearance: none;
		background: var(--bg-field);
		color: var(--text-hi);
		border: var(--border-w) solid var(--field-border);
		border-radius: var(--radius-field);
		height: calc(var(--space-unit) * 6);
		padding: 0 calc(var(--space-unit) * 6) 0 calc(var(--space-unit) * 2);
		font-family: var(--font-ui);
		font-size: var(--fs-value);
		cursor: pointer;
	}
	select:hover {
		background: var(--field-hover);
	}
	select:focus-visible {
		outline: var(--focus-w) solid var(--focus-ring);
		outline-offset: var(--border-w);
	}
	.chevron {
		position: absolute;
		right: calc(var(--space-unit) * 2);
		color: var(--text-lo);
		font-size: var(--fs-value);
		pointer-events: none;
	}
</style>
