<script lang="ts">
	// 루트 홈 (랜딩). 엔진 연결 상태 + 전 라우트 링크 + 실행 안내.
	// R1: 스타일은 design/ 밖에서 선언 금지 — 여기서는 design/gallery.css 클래스만.
	import { onDestroy, onMount } from 'svelte';
	import { ConodeClient } from '$lib/protocol/client.svelte';
	import '$lib/design/gallery.css';

	const client = new ConodeClient();
	onMount(() => client.connect());
	onDestroy(() => client.disconnect());

	// 각 화면 — 엔진 필요 여부/카테고리 액센트로 그룹.
	const ROUTES = [
		{ path: '/live', name: 'live', c: 'var(--cat-generate)', engine: true, desc: '라이브 노드 그래프 — 파라미터 자동 UI + 프리뷰. 시작점.' },
		{ path: '/graph', name: 'graph', c: 'var(--cat-depth)', engine: true, desc: '노드 그래프 편집기 — 21종 팔레트, 드래그 배치·연결.' },
		{ path: '/quad', name: 'quad', c: 'var(--cat-vision)', engine: true, desc: '비전 4분할 뷰 — Canny·Pose·Depth·Segmentation.' },
		{ path: '/audio', name: 'audio', c: 'var(--cat-audio)', engine: true, desc: '오디오 12스템 ModMatrix — 스템×특성으로 파라미터 모듈레이션.' },
		{ path: '/output', name: 'output', c: 'var(--cat-output)', engine: true, desc: '코너핀 매핑 출력 — 4점 드래그 프로젝션 워프.' },
		{ path: '/scenes', name: 'scenes', c: 'var(--cat-output)', engine: true, desc: '씬/큐 — 파라미터 스냅샷 저장·크로스페이드 recall·제스처 바인딩.' },
		{ path: '/design', name: 'design', c: 'var(--cat-input)', engine: false, desc: '디자인 시스템 갤러리 — 토큰·6종 위젯 (엔진 불필요).' },
		{ path: '/nodes', name: 'nodes', c: 'var(--cat-input)', engine: false, desc: 'NodeCard 갤러리 — 6 카테고리 데모 (엔진 불필요).' }
	];
</script>

<div class="dg-page">
	<header>
		<h1 class="dg-h1">conode</h1>
		<p class="dg-sub">실시간 AI 비주얼 퍼포먼스 엔진 · 라이브 영상·오디오·제스처를 하나의 노드 그래프로</p>
		<div
			class="dg-status mono"
			class:open={client.status === 'open'}
			class:closed={client.status === 'closed'}
		>
			<span class="dot"></span>engine: {client.status}{#if client.status === 'open'} · {client.nodes.length} nodes{/if}
		</div>
	</header>

	{#if client.status !== 'open'}
		<section class="dg-section">
			<div class="dg-hint warn mono">
				<strong>엔진이 연결되지 않았습니다.</strong> conode 는 <strong>UI + 엔진 2개 프로세스</strong>로 동작합니다.
				아래 라이브 화면들은 엔진(<code>ws://127.0.0.1:8787</code>)이 떠 있어야 노드가 보입니다.
				<br /><br />
				<strong>터미널 1</strong> — 프론트: <code>pnpm dev</code><br />
				<strong>터미널 2</strong> — 엔진: <code>engine/.venv/bin/python -m conode_engine</code><br />
				저사양 확인용 최소 티어로 강제하려면: <code>… -m conode_engine --tier potato</code>
			</div>
		</section>
	{/if}

	<section class="dg-section">
		<h2 class="dg-section-title">화면</h2>
		<div class="dg-home">
			{#each ROUTES as r (r.path)}
				<a class="dg-home-card" href={r.path} style="--c: {r.c}">
					<span class="dg-home-name">{r.name}</span><span class="dg-home-path mono">{r.path}</span>
					<div class="dg-home-desc">{r.desc}</div>
				</a>
			{/each}
		</div>
	</section>

	<section class="dg-section">
		<h2 class="dg-section-title">스펙 티어</h2>
		<div class="dg-hint mono">
			LiveDiffusion 은 하드웨어별 <strong>스펙 티어</strong>로 동작합니다 — 이 화면에서 선택하거나
			엔진 시작 시 <code>--tier</code> 로 지정. 기본은 자동 감지(<code>auto</code>).<br /><br />
			<strong>potato</strong> — CPU/폴백, 저해상도. 이 Mac 포함 어디서나 동작(확인용).<br />
			<strong>mps_low</strong> — Apple Silicon MPS, 소형 실디퓨전(torch 설치 시).<br />
			<strong>cuda_3070</strong> — CUDA diffusers LCM, 512px, TRT 불필요(≈8GB VRAM).<br />
			<strong>cuda_max</strong> — StreamDiffusion + TensorRT(≈4090). 의존성 없으면 자동으로 potato 로 폴백.
		</div>
	</section>
</div>
