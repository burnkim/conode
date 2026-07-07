# TODO — M0 Skeleton
- [x] T1 모노레포 스캐폴드 (구조=PLAN §9) — 완료조건: pnpm dev로 빈 Tauri 창 기동
      ↳ 2026-07-05 완료: pnpm workspace + apps/studio(Tauri2 + SvelteKit/Svelte5 adapter-static) + engine/packages/skills 골격. `pnpm dev`로 341 crates 컴파일 후 빈 conode-studio 창 기동 확인(프로세스 상주·vite :1420). 이름 kkum→conode. 추가 의존성: @types/node(vite.config.ts process 타입, R7).
- [x] T2 디자인 토큰 + 6종 위젯 구현 — 완료조건: /design 데모 페이지에 전 위젯 렌더, verify-ui 스크린샷
      ↳ 2026-07-05 완료: tokens.css(§5.2)+base.css, 6종 위젯(Slider fill-bar/Toggle/Enum/Text/Seed/MultiMarkerSlider) src/lib/design/에 구현(R1/R6). /design 갤러리에 스와치14+위젯6 렌더, svelte-check 0/0, /browse 스크린샷 docs/verify/T2-design-system.png, 토글·Enum 반응성 실측 확인. 폰트 미번들(시스템 폴백).
- [x] T3 NodeCard 컴포넌트 — 완료조건: 6개 카테고리 색상 변형 데모, 헤더 성능배지 목업 포함
      ↳ 2026-07-05 완료: NodeCard.svelte(§5.3 고정 해부: 헤더 h56 카테고리색→다크 그라디언트, 핀/재생/이름/perf배지/⚡/경로/fps, PARAMETERS(T2 위젯), 16:9 인라인 프리뷰). /nodes 데모 6 카테고리 + 성능배지 ok4/warn1/error1(fps 기준). svelte-check 0/0, 스크린샷 docs/verify/T3-nodecard.png.
- [x] T4 packages/schema v0 (hello, node.list, param.set, frame.preview) + zod/pydantic 생성
      ↳ 2026-07-05 완료: protocol.schema.json(원천, 판별유니온) + generate.mjs로 zod(apps/studio/src/lib/protocol/messages.ts)·pydantic(engine/conode_engine/protocol/messages.py) 생성(R3). 공유 픽스처 examples.json으로 계약 테스트 양쪽 통과(pytest 17, vitest 16). R7 추가 의존성: zod(UI 런타임), vitest(UI dev), pydantic·pytest(engine, py3.12 venv=engine/.venv).
- [x] T5 engine 스켈레톤: WS 서버 + scheduler + ParamSpec — 완료조건: pytest 통과
      ↳ 2026-07-05 완료: core/param_spec(6위젯+Group+ParamStore, R2/R6/R8), processor(tick/process, R4), latest_wins(드랍), scheduler(노드별 fps·지연누적금지), protocol/server(hello→node.list, param.set 적용, frame.preview broadcast, R3/R5). pytest 26 passed(프로토콜17+엔진9, WS 핸드셰이크·param.set·broadcast 왕복 포함). 런타임 의존성 설치(websockets/numpy/opencv/pillow).
- [x] T6 Camera 노드 E2E — 완료조건: 카메라 프리뷰가 NodeCard 안에 15fps+로 표시, 실측 fps 배지 동작
      ↳ 2026-07-05 완료: engine Camera 노드(OpenCV 캡처 스레드=R4, 합성 폴백) → frame.preview(320x180 JPEG over WS) → UI ConodeClient(zod 검증) → /live 의 NodeCard 인라인 프리뷰 + 실측 fps 배지. 실카메라로 확인: source=camera, 28~29fps(>15) 초록 배지, seq 연속 증가, exposure/mirror param.set 배선. 스크린샷 docs/verify/T6-camera-live.png.

## M0 완료 (2026-07-05)
T1~T6 전부 완료·검증·커밋·push. svelte-check 0/0 · vitest 16 · pytest 30.

# TODO — M1 Vision Pipeline
- [x] T7 엔진 그래프 코어 — 노드 입력 포트 + 연결(Graph, topo 평가) + 노드간 프레임 전달 + preview 인코더 분리. 완료조건: pytest — Camera→Canny 연결 시 프레임 전파.
      ↳ 2026-07-05 완료: Processor에 inputs 포트+output+tick(ms 측정), core/graph.Graph(add/connect/remove/topo/evaluate, 사이클 거부), core/preview.encode_jpeg 분리. Camera.process는 numpy 반환으로 리팩터(프레임/프리뷰 경로 분리, R5). pytest 37 passed(test_graph 6 추가).
- [x] T8 Canny 노드 (OpenCV) — Camera→Canny E2E, /live 다중 노드 프리뷰. 완료조건: Canny 엣지 프리뷰가 NodeCard에 표시.
      ↳ 2026-07-05 완료: nodes/canny.py(low/high/invert). app.py 그래프 cam1→canny1, 노드별 preview broadcast. /live를 client.nodes 루프 다중 NodeCard로. E2E: 실카메라 + Canny 엣지 프리뷰 2카드, 28fps 초록 배지, low/high param.set 배선. docs/verify/T8-camera-canny.png. (T7+T8 한 슬라이스로 함께 검증·커밋)
- [x] T9 프로토콜 확장 — graph 메시지(graph.get/node.add/node.connect/node.remove) 스키마 + zod/pydantic 재생성 + 계약 테스트.
      ↳ 2026-07-05 완료: schema에 Edge + graph.get/graph.state/node.add/remove/connect/disconnect 추가, zod/pydantic 재생성. 서버 registry+핸들러(변경 시 graph.state broadcast, 연결 시 hello→node.list→graph.state), 클라이언트 edges 상태 + 편집 메서드. 계약(examples 10↑) + WS 편집(connect/disconnect/add/remove) 테스트. pytest 55 · vitest 26 · svelte-check 0/0.
- [x] T10 Pose 노드 (MediaPipe, 폴백) — 스켈레톤 오버레이 프리뷰.
      ↳ 2026-07-05 완료: nodes/pose.py MediaPipe PoseLandmarker(Tasks API, start()에서 로드=R4), 스켈레톤 오버레이. 모델 실패 시 폴백. E2E 10.5ms/frame.
- [x] T11 Depth 노드 (근사, 폴백) — 뎁스맵 프리뷰.
      ↳ 2026-07-05 완료: nodes/depth.py 밝기/블러 근사 + INFERNO 컬러맵(모델 미사용, 실모델은 M2에서 process 교체). 0.4ms/frame.
- [x] T12 Segmentation 노드 (MediaPipe SelfieSeg, 폴백) — 마스크 프리뷰.
      ↳ 2026-07-05 완료: nodes/segmentation.py MediaPipe ImageSegmenter(confidence mask), cutout/mask/blur_bg 합성. 폴백=중앙근사. 4.7ms/frame.
      ↳ 공통: core/models.py 다운로더(models/ 캐시, PLAN §7), Processor.tick 노드 크래시 격리. mediapipe 의존성(Apache2.0). pytest 44. /live 5노드 28fps. docs/verify/T10-12-vision-pipeline.png.
- [x] T13 쿼드뷰 UI — 4분할 노드 프리뷰 레이아웃.
      ↳ 2026-07-05 완료: /quad 라우트, 비전 4노드 2x2 그리드(16:9 셀 + name/fps health 오버레이). design/gallery.css dg-quad. E2E: 사람 인프레임 시 Canny 엣지·Pose 스켈레톤·Depth·Seg 컷아웃 전부 29fps. docs/verify/T13-quadview.png.
- [x] T14 노드 그래프 편집 UI — 캔버스 노드 배치/연결선/삭제/저장(직렬화 왕복).
      ↳ 2026-07-05 완료: NodeInfo에 node_type+inputs 추가(재생성). /graph 편집기 — 드래그 배치, SVG 점선 연결선(소스 카테고리색 계승 §5.3), 팔레트 추가(node.add), ✕ 삭제(node.remove), 포트 드래그 연결(node.connect), 연결 클릭 해제, localStorage 저장→로드 왕복(구조+위치). lib/graph/serialize.ts, design/graph.css. 세그폴트 수정: node.start/stop는 메인 스레드(MediaPipe GL 스레드 친화성). E2E: 저장→Pose삭제(4)→로드(5 복원), +canny 추가·드래그연결(cam1→canny2) 실측. docs/verify/T14-graph-editor.png.

## M1 완료 (2026-07-05)
T7~T14 전부 완료·검증·커밋·push. 비전 파이프라인(Canny/Pose/Depth/Seg) + 쿼드뷰 + 그래프 편집기.
pytest 56 · vitest 26 · svelte-check 0/0.

# TODO — M2 LiveDiffusion (타깃: RTX 4090 / TRT · Mac 개발기는 폴백으로 검증)
- [x] T15 LiveDiffusion 노드 스캐폴드 — §1.2 ParamSpec 전체 + 포트(in/control/mask) + 백엔드 추상화 + FallbackBackend(스타일라이즈). 그래프 통합. [Mac 검증]
      ↳ 2026-07-05 완료: nodes/live_diffusion.py(§1.2 전체 ParamSpec+Group, 포트 in/control/mask), diffusion/backend.py(DiffusionBackend 추상화 + FallbackBackend cv2.stylization+프롬프트 색조+control 오버레이, select_backend). 그래프 cam1→live1.in, canny1→live1.control. registry+app 통합. E2E /live 6노드 24fps, LiveDiffusion 스타일라이즈 프리뷰. pytest 64.
- [x] T16 Similar Image Filter — 프레임 유사도 스킵(sif_threshold/sif_max_skip). [Mac 검증]
      ↳ 2026-07-05 완료: diffusion/sif.py(연속 프레임 유사도, max_skip 캡). LiveDiffusion advanced에 연결. 결정적 테스트 3.
- [~] T17 RegionApply/Composite — 마스크 영역만 디퓨전 결과로 치환(§2). [부분: LiveDiffusion.process 안에 mask 영역 치환 구현·테스트. 독립 Composite 노드는 추후]
- [x] T18 StreamDiffusion 백엔드 — LCM-LoRA(상업OK §11) + ControlNet (CUDA). [4090, 코드+문서, 배포 검증]
      ↳ 2026-07-05 완료(블라인드): diffusion/streamdiffusion_backend.py(LCM img2img, creativity→t_index_list, TRT accel, torch/streamdiffusion 지연임포트), select_backend가 CUDA시 우선(Mac은 Fallback 확인). requirements-cuda.txt. **Mac 실행검증 불가 — 4090 배포 시 검증**.
- [x] T19 TensorRT 빌드 캐시 + CUDA 스트림 (realtime-perf 스킬). [4090]
      ↳ 2026-07-05 완료: skills/realtime-perf/SKILL.md(§6 예산표, 프로파일링, 지연누적금지 패턴 latest-wins/기한리셋/SIF/크래시격리, TRT 캐시 engine_dir, CUDA 스트림, 백엔드 교체 지점).
- [~] T20 25fps 달성 벤치 (§6 예산) — DoD. [벤치 하네스는 완료·Mac 검증 / 25fps LiveDiffusion은 4090 DoD]
      ↳ 2026-07-05: conode_engine/bench.py(`python -m conode_engine.bench <node|all> [--enforce]`, §6 예산 비교, 초과 시 exit1). Mac 실측: canny 0.44ms·depth 0.29ms·seg 4.78ms(예산내), pose 10.2ms(예산초과=Mac CPU vs 4090 TRT). test 3. **25fps LiveDiffusion 실측은 4090 배포 DoD**.

## M2 상태 (2026-07-05)
포터블 코어(T15~T17 부분·T20 벤치) Mac 검증 완료. 실디퓨전(T18 StreamDiffusion+LCM·T19 TRT·T20 25fps)은 코드+문서 작성, **4090 배포 시 검증 대기**(블라인드). pytest 67.

# TODO — M3 제스처 (시그니처 A: 프레임 제스처 = 영역 디퓨전, PLAN §2)
- [x] T21 HandTracker 노드 — MediaPipe HandLandmarker(21×2 랜드마크) + 오버레이 프리뷰 + 폴백. [Mac 검증]
      ↳ 2026-07-05 완료: nodes/hand_tracker.py(HandLandmarker num_hands=2, 21점, 스켈레톤 오버레이, 구조화 output {hands,w,h}), gesture/one_euro.py. Processor.preview_frame(구조화 output 노드 대응) + encode 가드. hand_landmarker.task 다운로더.
- [x] T22 GestureRecognizer 노드 — 규칙 기반 v1 + 이벤트 + JSON 규칙 확장. [Mac 검증]
      ↳ 2026-07-05 완료: gesture/rules.py(recognize: frame/pinch/point/palm, LM 인덱스맵, eval_json_rules dist/extended/curled→emit), nodes/gesture_recognizer.py(point-hold 지속시간·palm-push 엣지, 주석 프리뷰).
- [x] T23 RegionMask 노드 — 제스처→사각/원형 마스크, feather, one-euro 관성. [Mac 검증]
      ↳ 2026-07-05 완료: nodes/region_mask.py(rect/circle 마스크, OneEuroVec 스무딩, feather, no_gesture full/none). 결정적 테스트.
- [x] T24 파이프라인 통합 + gesture-rules 스킬. [Mac 검증]
      ↳ 2026-07-05 완료: 그래프 cam→hands→gesture→region→live.mask(+cam→live.in, cam→canny→live.control). skills/gesture-rules/SKILL.md. 통합 테스트(합성 프레임 제스처→영역만 디퓨전, 외부 원본 유지) 통과. /live 6노드 30fps. docs/verify/T21-24-gesture-pipeline.png. pytest 78.

## M3 완료 (2026-07-05)
T21~T24 전부 완료·검증(Mac). 시그니처 "프레임 제스처=영역 디퓨전" 동작. pytest 78.

# TODO — M4 오디오 12스템 ModMatrix (시그니처 B, PLAN §3)
- [x] T25 AudioIn 노드 — sounddevice 멀티채널(디바이스) + 12스템 합성, 채널별 최신 블록. [Mac 검증]
- [x] T26 특성 추출 — 채널별 rms/peak/onset/centroid/flux/band(low/mid/high) 정규화 0..1 (numpy FFT, 적응 정규화). [Mac 검증]
- [x] T27 ModMatrix — 소스(스템×특성+LFO)×타깃 매트릭스(amount/curve/smooth/clamp), base+모듈레이션, modulatable만 적용(R8). [Mac 검증]
- [x] T28 프롬프트 바인딩 — (token:{stem.feature}) 파싱+가중치 치환, ModMatrix 노드가 타깃 prompt에 push. [Mac 검증]
- [x] T29 ModMatrix UI — /audio(12스템 미터 + 적용타깃 + modulated) + Slider 모듈레이션 링(도넛 §3.3). [Mac 검증]
      ↳ 2026-07-05 M4 완료: audio/{capture,features,modmatrix,prompt_binding}, nodes/{audio_in,mod_matrix}. 그래프 audio→mod, mod가 live1.prompt_strength·controlnet.weight·cam1.exposure(LFO) 모듈레이션 + prompt 바인딩. Processor.param_range/is_modulatable. /audio·/design mod-ring. pytest 86. docs/verify/T25-29-audio-modmatrix.png.

## M4 완료 (2026-07-05)
T25~T29 전부 완료·검증(Mac). 12스템 ModMatrix 라이브 모듈레이션 동작. pytest 86.

# TODO — M5 출력 (PLAN §4)
- [x] T30 MappedOutput 노드 — 코너핀 4점 homography warp(cv2) + 엣지 블렌드. [Mac 검증]
- [x] T31 Recorder 노드 — 프레임 → 비디오 파일(cv2.VideoWriter, recordings/ gitignore). [Mac 검증]
- [x] T32 매핑 에디터 UI — /output 코너 드래그 → param.set(corners.*), 라이브 워프. [Mac 검증]
- [x] T33 NDI/Spout/Syphon Out + 멀티디스플레이 — docs/output-bridges.md(네이티브, 배포 검증). [문서]
      ↳ 2026-07-05 M5 완료: nodes/{mapped_output,recorder}, 그래프 live→mapped→rec. /output 코너핀 에디터(드래그 워프 실측). NDI/Spout/Syphon/멀티디스플레이는 네이티브라 문서화(배포 검증). pytest 90. docs/verify/T30-33-mapped-output.png.

## M5 상태 (2026-07-05)
포터블 코어(MappedOutput 코너핀·Recorder·에디터 UI) Mac 검증 완료. 네이티브 출력(NDI/Spout/Syphon·멀티디스플레이)은 문서화, 배포 검증 대기. pytest 90.

# TODO — M6 제품화 (PLAN §7)
- [x] T34 라이선스 — Ed25519 서명 라이선스(오프라인), 티어 Personal/Pro/Edu, gen/verify + CLI(python -m conode_engine.licensing). [Mac 검증]
- [x] T35 프리셋 팩 — presets/gesture-diffusion·audio-reactive(SavedGraph 포맷), 검증 테스트. [Mac 검증]
- [x] T36 README + 문서 — README.md(소개/실행/구조/노드/마일스톤/라이선스). [문서]
- [x] T37 인스톨러 — tauri.conf bundle 메타(category/copyright/macOS) + docs/installer.md(dmg/msi·사이닝·사이드카·체크리스트). [설정+문서]
      ↳ 2026-07-05 M6 완료: conode_engine/licensing.py(Ed25519, cryptography 의존), presets/, README.md, docs/installer.md. pytest 96 · vitest 26 · svelte-check 0/0.

## M6 완료 (2026-07-05)
T34~T37 전부 완료·검증(Mac). 라이선스·프리셋·README·인스톨러 문서. pytest 96.

## PLAN §8 마일스톤 종합 (2026-07-05)
M0✅ M1✅ M2🔶(4090 배포검증) M3✅ M4✅ M5✅(코어)/🔶(네이티브 출력) M6✅.
Mac 검증 가능한 전 범위 완료. 남은 검증: 4090(M2 실디퓨전·25fps), 네이티브 출력(NDI/Spout/Syphon·멀티디스플레이).

# TODO — 리뷰 후속 (아키텍처/노드/악기 기능)
- [x] A1 ParamSpec → UI 자동생성 (R2 척추) — node.list/graph.state에 params(스펙+값) 전송, design/ParamPanel(kind→6위젯 자동), /live 하드코딩 제거. ParamValue에 number[] 추가(multimarker). 첫 렌더 undefined 바인딩 크래시 수정(`{#if path in vals}`).
      ↳ 2026-07-05: 10노드 전부 파라미터 자동 렌더(LiveDiffusion 13개 포함, controlnet/advanced Group). Canny invert 토글→param.set→프리뷰 반전 실측. docs/verify/A1-paramspec-autogen.png.
- [x] A2 Scheduler(노드별 fps) + latest-wins 를 라이브 경로에 배선.
      ↳ 2026-07-05 완료(체크 누락, 2026-07-07 정리): graph.evaluate fps-게이팅(target_fps 미달 시 tick 스킵)+measured_fps EMA, app.py live.target_fps=15, FramePreview 노드별 실측 fps. 다운스트림은 latest-wins.
- [x] B §1.3 v1 노드 8종 추가 — Image·Blend·Crossfade·ColorGrade·Switch·MaskCompose·FeedbackLoop·StylePreset (registry 21종, /graph 팔레트 전체). A1 자동 UI 로 파라미터 무료.
      ↳ 2026-07-05: pytest+12(노드 B). 팔레트로 StylePreset 추가→/live 자동 파라미터(enum+slider) 실측. (Video File/EnvelopeFollower/standalone LFO 는 후속.)
- [x] C 제스처 JSON 규칙 배선 + ModMatrix 제스처 소스. (이벤트 버스/씬 트리거→D, 매트릭스 에디터 UI→후속)
      ↳ 2026-07-05: GestureRecognizer custom_rules(JSON)→eval_json_rules 적용. ModMatrix gesture 입력 + gesture.frame/value/point 소스(§3.3), 그래프 gesture→mod, 프레임 제스처가 prompt_strength 밀어올림. pytest+3.
- [x] D 큐/씬 시스템 + crossfade. (MIDI/OSC In 은 후속: 디바이스/deps 의존)
      ↳ 2026-07-05: core/scenes.SceneStore(capture/save/recall+fade 크로스페이드/update). 프로토콜 scene.save/recall/get/list, 서버+브로드캐스터 update, 클라이언트, /scenes UI. Crossfade 노드(B). pytest+8. /scenes E2E: intro/drop 저장→recall 크로스페이드 실측.

# TODO — 후속작업
- [x] 큐 바인딩 (제스처 이벤트 → 씬 recall) — §2 "이벤트는 씬 전환에 바인딩" 완성.
      ↳ 2026-07-05: SceneStore.bind/trigger, 프로토콜 cue.bind, 서버 핸들 + 브로드캐스터가 노드 output.event 엣지검출→scenes.trigger(씬 크로스페이드 recall). /scenes 바인딩 UI(palm_push/point_hold→씬). pytest+1. E2E: 바인딩 저장·엔진 안정 확인.

# TODO — 홈 + 스펙 티어 (2026-07-07, /goal: 우선순위 순 + 다양한 사양 리팩토링)
- [x] H1 루트 홈 랜딩 — `m0.studio shell` 플레이스홀더 교체. 엔진 상태 + 8 라우트 카드 + 실행 안내(2 프로세스) + 스펙 티어 설명. R1(design/ 클래스만).
      ↳ 2026-07-07: routes/+page.svelte 재작성, gallery.css dg-home*/dg-hint 추가. svelte-check 0/0. /browse E2E: 다크 캔버스·8카드·engine:closed 힌트 렌더. docs/verify/home-landing.png.
- [x] H2 스펙 티어 코어 — diffusion/spec.py(SpecProfile + TIERS potato/mps_low/cuda_3070/cuda_max + auto_detect). backend.select_backend(profile) 티어 기반으로. FallbackBackend 저해상도(저크기) 지원. pytest.
      ↳ 2026-07-07: spec.py(SpecProfile + TIERS 4종 + available_devices/device_ok/auto_detect/resolve/downgrade). select_backend(profile) 재작성 — 디바이스/패키지 부재 시 potato 폴백. FallbackBackend(profile) 저해상도 작업→입력크기 복원. test_spec.py 11.
- [x] H3 DiffusersBackend — torch diffusers img2img LCM, device auto(cuda/mps/cpu). 3070(CUDA)·이 Mac(MPS)·CPU 공용. 지연 임포트, 의존성 없으면 select_backend 가 potato 로 폴백. requirements-diffusers.txt.
      ↳ 2026-07-07: diffusers_backend.py(AutoPipelineForImage2Image + LCMScheduler + load_lora_weights/fuse_lora, device별 dtype). torch/diffusers 지연 임포트(미설치도 모듈 임포트 안전). requirements-diffusers.txt(Apple Silicon/CUDA 공용). **실모델 실행은 torch 설치 후/GPU 배포 검증(블라인드)**.
- [x] H4 LiveDiffusion tier 파라미터(Enum) + 엔진 `--tier` 옵션 + auto 감지 배선. A1 자동 UI 로 /live 에서 티어 선택. 이 Mac potato E2E 확인.
      ↳ 2026-07-07: LiveDiffusion.tier Enum(TIER_NAMES), start()가 resolve→select_backend, 런타임 티어변경 재선택. app.py --tier/--host/--port/--fps argparse + 시작 시 티어/디바이스 출력. E2E(Apple M1 Max, --tier potato): /live LiveDiffusion 카드에 tier 드롭다운(potato) 자동 렌더(R2), 14fps latest-wins. docs/verify/H4-tier-live.png.
- [x] H5 문서 — docs/spec-tiers.md(티어별 하드웨어·설치·성능), README 티어 표 반영.
      ↳ 2026-07-07: docs/spec-tiers.md(티어 표·선택·설치·폴백 규칙·검증 상태), README M2 행/라이브 악기 기능/실행안내 티어 반영.

## Questions / 리뷰 대기 (기획 세션)
- Q1 T2에서 인터랙션 파생 토큰(--field-fill/border/hover, --focus-ring, --knob 등) 추가함 → §5.1상 디자인 리뷰 대상. 확정 필요.
- Q2 폰트(Inter/Pretendard/JetBrains Mono) 미번들 → 현재 시스템 폴백. 번들 방식/라이선스 결정 필요(오프라인 공연 도구).
- Q3 카메라 권한: 실카메라는 macOS TCC 그랜트 필요(첫 cap.read()가 블록). 배포 시 Tauri 앱 번들의 카메라 usage 권한/entitlement 설정 필요.
- Q4 프로토콜 v0는 node.list에 ParamSpec 미포함(id/name/category/index만). ParamSpec→UI 자동생성(R2)의 완전한 배선은 M1에서 node.describe 확장 필요.
