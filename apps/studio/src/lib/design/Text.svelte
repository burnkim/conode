<script lang="ts">
	// Text — 단문/장문(프롬프트). multiline=true 시 textarea.
	interface Props {
		label?: string;
		value?: string;
		placeholder?: string;
		multiline?: boolean;
	}
	let {
		label = '',
		value = $bindable(''),
		placeholder = '',
		multiline = false
	}: Props = $props();
</script>

<div class="field" class:multiline>
	{#if label}<span class="label">{label}</span>{/if}
	{#if multiline}
		<textarea bind:value {placeholder} rows="3" aria-label={label}></textarea>
	{:else}
		<input type="text" bind:value {placeholder} aria-label={label} />
	{/if}
</div>

<style>
	.field {
		display: flex;
		align-items: center;
		gap: calc(var(--space-unit) * 2);
		min-height: var(--param-row-h);
		padding: 0 calc(var(--space-unit) * 3);
	}
	.field.multiline {
		align-items: flex-start;
		padding-top: calc(var(--space-unit) * 1.5);
		padding-bottom: calc(var(--space-unit) * 1.5);
	}
	.label {
		color: var(--text-lo);
		font-size: var(--fs-label);
		white-space: nowrap;
		padding-top: calc(var(--space-unit) * 1.5);
	}
	.field:not(.multiline) .label {
		padding-top: 0;
	}
	input,
	textarea {
		flex: 1;
		width: 100%;
		background: var(--bg-field);
		color: var(--text-hi);
		border: var(--border-w) solid var(--field-border);
		border-radius: var(--radius-field);
		font-family: var(--font-ui);
		font-size: var(--fs-value);
		padding: calc(var(--space-unit) * 1.5) calc(var(--space-unit) * 2);
		resize: vertical;
	}
	input:focus-visible,
	textarea:focus-visible {
		outline: var(--focus-w) solid var(--focus-ring);
		outline-offset: var(--border-w);
	}
	input::placeholder,
	textarea::placeholder {
		color: var(--text-lo);
	}
</style>
