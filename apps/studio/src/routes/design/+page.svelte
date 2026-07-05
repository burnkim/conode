<script lang="ts">
	// /design — 디자인 시스템 갤러리 (T2 verify-ui 대상).
	// R1: 이 라우트는 스타일을 선언하지 않는다 → design/gallery.css 클래스만 사용.
	// R2: 노드 파라미터 패널은 ParamSpec 자동생성이지만, 여긴 위젯 카탈로그(원시 인스턴스화 허용).
	import { Slider, Toggle, Enum, Text, Seed, MultiMarkerSlider } from '$lib/design';
	import '$lib/design/gallery.css';

	let strength = $state(0.3);
	let weight = $state(1.0);
	let denoise = $state(0.75);
	let sifThreshold = $state(0.9);

	let cnEnable = $state(true);
	let noise = $state(false);
	let sif = $state(true);

	let cnType = $state('depth');
	let stylePreset = $state('none');

	let prompt = $state('a field of stars, geometric, (glow:1.2)');
	let negative = $state('blurry, low quality, watermark');

	let seed = $state(1234567);
	let seedMode = $state<'random' | 'fixed'>('random');

	let creativity = $state([10, 35, 49]);

	const swatches: Array<[string, string]> = [
		['--bg-canvas', 'bg-canvas'],
		['--bg-card', 'bg-card'],
		['--bg-field', 'bg-field'],
		['--text-hi', 'text-hi'],
		['--text-lo', 'text-lo'],
		['--cat-input', 'cat-input'],
		['--cat-vision', 'cat-vision'],
		['--cat-depth', 'cat-depth'],
		['--cat-generate', 'cat-generate'],
		['--cat-audio', 'cat-audio'],
		['--cat-output', 'cat-output'],
		['--state-warn', 'state-warn'],
		['--state-error', 'state-error'],
		['--state-ok', 'state-ok']
	];
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode · design system</h1>
		<p class="dg-sub mono">M0 · T2 — tokens + 6 primitive widgets (PLAN §5.1–5.2)</p>
		<nav class="dg-nav mono">
			<a href="/design">design system</a>
			<a href="/nodes">nodes →</a>
		</nav>
	</header>

	<section class="dg-section">
		<h2 class="dg-section-title">Color tokens</h2>
		<div class="dg-swatches">
			{#each swatches as [tok, name] (tok)}
				<div class="dg-swatch">
					<div class="dg-swatch-chip" style="background: var({tok});"></div>
					<div class="dg-swatch-name mono">{name}</div>
					<div class="dg-swatch-tok mono">{tok}</div>
				</div>
			{/each}
		</div>
	</section>

	<section class="dg-section">
		<h2 class="dg-section-title">Widgets — 6종 고정 (R6)</h2>
		<div class="dg-grid">
			<div class="dg-widget">
				<div class="dg-widget-name mono">Slider · fill-bar</div>
				<Slider label="prompt_strength" bind:value={strength} min={0} max={2} step={0.01} />
				<Slider
					label="controlnet.weight"
					bind:value={weight}
					min={0}
					max={2}
					step={0.01}
					accent="var(--cat-depth)"
				/>
				<Slider
					label="denoise"
					bind:value={denoise}
					min={0}
					max={1}
					step={0.01}
					accent="var(--cat-generate)"
				/>
				<Slider label="sif_threshold" bind:value={sifThreshold} min={0} max={1} step={0.01} />
			</div>

			<div class="dg-widget">
				<div class="dg-widget-name mono">Toggle</div>
				<Toggle label="controlnet.enable" bind:value={cnEnable} />
				<Toggle label="advanced.noise" bind:value={noise} />
				<Toggle label="similar_image_filter" bind:value={sif} />
			</div>

			<div class="dg-widget">
				<div class="dg-widget-name mono">Enum · dropdown</div>
				<Enum
					label="controlnet.type"
					bind:value={cnType}
					options={['self', 'pose', 'depth', 'canny', 'seg']}
				/>
				<Enum
					label="style_preset"
					bind:value={stylePreset}
					options={['none', 'neon', 'ink', 'chrome', 'vapor']}
				/>
			</div>

			<div class="dg-widget">
				<div class="dg-widget-name mono">Text</div>
				<Text label="prompt" bind:value={prompt} multiline />
				<Text label="negative" bind:value={negative} placeholder="negative prompt…" />
			</div>

			<div class="dg-widget">
				<div class="dg-widget-name mono">Seed · mode</div>
				<Seed label="seed" bind:value={seed} bind:mode={seedMode} />
			</div>

			<div class="dg-widget">
				<div class="dg-widget-name mono">MultiMarkerSlider · creativity</div>
				<MultiMarkerSlider label="creativity (denoise steps)" bind:markers={creativity} min={0} max={50} />
			</div>
		</div>
	</section>
</div>
