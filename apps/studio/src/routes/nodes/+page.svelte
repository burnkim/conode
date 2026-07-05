<script lang="ts">
	// /nodes — NodeCard 해부 데모 (T3). 6 카테고리 변형 + 성능배지 상태(ok/warn/error).
	// R1: 이 라우트는 스타일 미선언 → design/ 클래스만. R2: 데모용 정적 위젯 인스턴스.
	import { NodeCard, Slider, Toggle, Enum, Text, MultiMarkerSlider } from '$lib/design';
	import '$lib/design/gallery.css';
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode · nodes</h1>
		<p class="dg-sub mono">M0 · T3 — NodeCard 고정 해부 (PLAN §5.3) · 6 카테고리 · 성능배지</p>
		<nav class="dg-nav mono">
			<a href="/design">← design system</a>
			<a href="/nodes">nodes</a>
		</nav>
	</header>

	<section class="dg-section">
		<h2 class="dg-section-title">Nodes — 카테고리 변형 + 성능배지</h2>
		<div class="dg-nodes">
			<!-- Input (coral) · ok -->
			<NodeCard category="input" name="Camera" index={1} perf={{ w: 640, h: 480, fps: 30, ms: 2, fpsMode: 'auto' }}>
				<Enum label="device" value="FaceTime HD" options={['FaceTime HD', 'USB Cam']} />
				<Slider label="exposure" value={0.5} min={0} max={1} step={0.01} accent="var(--cat-input)" />
				{#snippet preview()}
					<div class="dg-preview-fill" style="--c: var(--cat-input);"></div>
				{/snippet}
			</NodeCard>

			<!-- Vision (cream) · ok -->
			<NodeCard category="vision" name="Pose" index={2} perf={{ w: 640, h: 480, fps: 25, ms: 4 }}>
				<Enum label="model" value="RTMPose-s" options={['RTMPose-s', 'MediaPipe']} />
				<Slider label="threshold" value={0.4} min={0} max={1} step={0.01} accent="var(--cat-vision)" />
				{#snippet preview()}
					<div class="dg-preview-fill" style="--c: var(--cat-vision);"></div>
				{/snippet}
			</NodeCard>

			<!-- Depth (blue) · warn (22fps) -->
			<NodeCard category="depth" name="DepthMap" index={3} perf={{ w: 640, h: 480, fps: 22, ms: 6 }}>
				<Enum label="model" value="DA-V2-S" options={['DA-V2-S', 'DA-V2-B']} />
				<Slider label="near" value={0.1} min={0} max={1} step={0.01} accent="var(--cat-depth)" />
				<Slider label="far" value={0.9} min={0} max={1} step={0.01} accent="var(--cat-depth)" />
				{#snippet preview()}
					<div class="dg-preview-fill" style="--c: var(--cat-depth);"></div>
				{/snippet}
			</NodeCard>

			<!-- Generate (green) · error (14fps 병목) -->
			<NodeCard
				category="generate"
				name="LiveDiffusion"
				index={4}
				perf={{ w: 512, h: 512, fps: 14, ms: 48 }}
			>
				<Text label="prompt" value="a field of stars, geometric" multiline />
				<Slider label="prompt_strength" value={1.0} min={0} max={2} step={0.01} accent="var(--cat-generate)" />
				<MultiMarkerSlider label="creativity" markers={[10, 35, 49]} min={0} max={50} />
				<Toggle label="controlnet.enable" value={true} />
				{#snippet preview()}
					<div class="dg-preview-fill" style="--c: var(--cat-generate);"></div>
				{/snippet}
			</NodeCard>

			<!-- Audio (purple) · ok (60Hz) -->
			<NodeCard category="audio" name="ModMatrix" index={5} perf={{ w: 12, h: 8, fps: 60, ms: 1, fpsMode: '60' }}>
				<Enum label="curve" value="exp" options={['lin', 'exp', 'log']} />
				<Slider label="amount" value={0.75} min={-1} max={1} step={0.01} accent="var(--cat-audio)" />
				<Toggle label="smooth" value={true} />
				{#snippet preview()}
					<div class="dg-preview-fill" style="--c: var(--cat-audio);"></div>
				{/snippet}
			</NodeCard>

			<!-- Output (amber) · ok -->
			<NodeCard
				category="output"
				name="MappedOutput"
				index={6}
				perf={{ w: 1920, h: 1080, fps: 30, ms: 3 }}
			>
				<Enum label="display" value="Display 2" options={['Display 1', 'Display 2', 'NDI']} />
				<Toggle label="ndi.out" value={false} />
				<Slider label="edge_blend" value={0.2} min={0} max={1} step={0.01} accent="var(--cat-output)" />
				{#snippet preview()}
					<div class="dg-preview-fill" style="--c: var(--cat-output);"></div>
				{/snippet}
			</NodeCard>
		</div>
	</section>
</div>
