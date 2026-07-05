<script lang="ts">
	// ParamPanel — 노드의 ParamSpec(와이어)에서 파라미터 UI 를 자동 생성한다 (R2).
	// 손으로 파라미터 UI 를 만들지 않는다 — kind → 6종 위젯 매핑 + param.set 배선.
	import type { ConodeClient } from '$lib/protocol/client.svelte';
	import Enum from './Enum.svelte';
	import MultiMarkerSlider from './MultiMarkerSlider.svelte';
	import Seed from './Seed.svelte';
	import Slider from './Slider.svelte';
	import Text from './Text.svelte';
	import Toggle from './Toggle.svelte';

	interface Props {
		params: Record<string, Record<string, unknown>>;
		node: string;
		client: ConodeClient;
		accent?: string;
	}
	let { params, node, client, accent = 'var(--field-fill)' }: Props = $props();

	let vals = $state<Record<string, unknown>>({});
	const sent: Record<string, string> = {};

	// 스펙 도착/변경 시 현재값으로 초기화 (엔진 기준)
	$effect(() => {
		for (const [path, spec] of Object.entries(params)) {
			if (!(path in vals)) {
				vals[path] = spec.value ?? spec.default;
				sent[path] = JSON.stringify(vals[path]);
			}
		}
	});

	// 사용자 변경 → param.set (배열은 JSON 비교)
	$effect(() => {
		if (client.status !== 'open') return;
		for (const [path, v] of Object.entries(vals)) {
			const key = JSON.stringify(v);
			if (sent[path] !== key) {
				sent[path] = key;
				client.setParam(node, path, v as number | string | boolean | number[]);
			}
		}
	});

	const num = (v: unknown, d = 0) => (typeof v === 'number' ? v : d);
</script>

{#each Object.entries(params) as [path, spec] (path)}
	{#if path in vals}
		{#if spec.kind === 'slider'}
		<Slider
			label={path}
			bind:value={vals[path] as number}
			min={num(spec.min, 0)}
			max={num(spec.max, 1)}
			step={spec.integer ? 1 : 0.01}
			{accent}
		/>
	{:else if spec.kind === 'toggle'}
		<Toggle label={path} bind:value={vals[path] as boolean} />
	{:else if spec.kind === 'enum'}
		<Enum label={path} bind:value={vals[path] as string} options={(spec.options as string[]) ?? []} />
	{:else if spec.kind === 'text'}
		<Text label={path} bind:value={vals[path] as string} multiline={spec.multiline === true} />
	{:else if spec.kind === 'seed'}
		<Seed label={path} bind:value={vals[path] as number} />
		{:else if spec.kind === 'multimarker'}
			<MultiMarkerSlider
				label={path}
				bind:markers={vals[path] as number[]}
				min={num(spec.min, 0)}
				max={num(spec.max, 50)}
			/>
		{/if}
	{/if}
{/each}
