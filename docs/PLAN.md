# PLAN.md — 실시간 AI 비주얼 퍼포먼스 엔진 1차 기획안
> 코드네임: **KKUM** (가칭 — "꿈틀"에서. 확정 전까지 코드/패키지명은 `kkum` 사용)
> 작성일: 2026-07-05 · 대상: Claude Code 초기 컨텍스트 문서
> 한 줄 정의: **라이브 영상·오디오·제스처를 실시간 디퓨전과 프로젝션 매핑까지 하나의 노드 그래프로 잇는 퍼포먼스 악기(instrument)**

---

## 0. 비전과 포지셔닝

### 0.1 무엇을 만드는가
카메라(또는 NDI/Spout) 입력 → 비전 분석(포즈/뎁스/세그/캐니/핸드) → 실시간 디퓨전(ControlNet 컨디셔닝) → 컴포지팅 → 프로젝션 매핑 출력까지를 **하나의 실시간 DAG**로 처리하는 데스크톱 앱. 오디오 12스템 분석이 모든 파라미터를 모듈레이션할 수 있고, 손 제스처가 디퓨전의 공간적 마스크를 실시간으로 정의한다.

### 0.2 ComfyUI와의 차별화 — "배치 그래프"가 아니라 "라이브 악기"
| 축 | ComfyUI | KKUM |
|---|---|---|
| 실행 모델 | 큐 기반 배치 실행 (실행→대기→결과) | **상시 스트리밍**: 모든 노드가 지정 fps로 계속 돎 |
| 시간 개념 | 없음 (프레임=독립) | 1급 시민: temporal coherence, crossfade, cue 시스템 |
| 노드 생태 | 무한 노드, 무한 비일관성 | **큐레이션된 코어 노드 + 엄격한 SDK 규격** 플러그인 |
| UI | 기능적, 비일관 | 디자인 토큰 강제, 모든 노드가 동일 해부 구조 |
| 퍼포먼스 컨트롤 | 없음 | MIDI/OSC 학습, 오디오 모듈레이션 매트릭스, 큐/씬 |
| 출력 | 파일 | **매핑된 라이브 출력** (멀티 디스플레이/NDI/Spout/Syphon) |
| 대상 | 테크니컬 유저 | VJ, 미디어 아티스트, 무대/공연 디자이너 |

핵심 명제: *ComfyUI는 이미지를 "만들고", KKUM은 이미지를 "연주한다".*
확장성은 노드 수가 아니라 **모듈레이션 가능성**(모든 파라미터가 오디오/제스처/MIDI/LFO의 타깃)에서 나온다.

### 0.3 레퍼런스 스크린샷에서 채택하는 문법
1. 노드 = 카드. 카드 해부는 완전히 고정: `헤더(핀·재생·이름·/processor/N/ 경로·성능배지·연결아이콘)` → `PARAMETERS 섹션` → `인라인 프리뷰`
2. 헤더 색 = 카테고리: Input(코랄), Vision(크림), Depth/Analysis(블루), Generate(그린), Audio(퍼플), Output/Mapping(앰버) — 색은 좌→우 그라디언트로 다크로 스며듦
3. 슬라이더 = **fill-bar 스타일** (라벨이 채움 영역 안에 들어감, 값은 우측 정렬)
4. 노드 헤더에 실시간 성능 표시: `640x480 25fps 2ms · fps auto` — 병목을 즉시 시각화
5. Creativity형 **멀티마커 슬라이더**: denoising step 구간을 마커(예: 10/35/49)로 표기
6. 연결선은 점선 + 소스 노드 색상 계승

---

## 1. 시스템 아키텍처

### 1.1 2-프로세스 구조 (확정 제안)
```
┌─────────────────────────────────────────────┐
│  KKUM App (Tauri 2 + Svelte 5)              │
│  - 노드 그래프 UI / 파라미터 / 프리뷰        │
│  - 매핑 에디터(출력 창은 WebGL2/WebGPU)      │
│  - 라이선스, 프로젝트 파일, 설정              │
└───────────────┬─────────────────────────────┘
                │ WebSocket(제어/상태, JSON) +
                │ SharedMemory or WebRTC(프레임, 저지연)
┌───────────────┴─────────────────────────────┐
│  kkum-engine (Python, 별도 프로세스)          │
│  - PyTorch + TensorRT (RTX 4090 타깃)        │
│  - StreamDiffusion 계열 실시간 SD 파이프라인   │
│  - 비전: RTMPose/MediaPipe, DepthAnythingV2, │
│    YOLOv8-seg or RVM, OpenCV Canny           │
│  - 오디오: 12ch 캡처 + 특성 추출              │
│  - 그래프 스케줄러 (프레임 클록, 노드별 fps)   │
└─────────────────────────────────────────────┘
```
- **왜 Tauri**: Svelte 선호 반영 + 경량 배포 + Rust 사이드에서 SharedMemory/Spout·NDI 브리지, 라이선스 검증 같은 네이티브 작업 처리. Electron 대비 판매용 바이너리 품질 우위.
- **왜 엔진 분리**: GPU 파이프라인 크래시가 UI를 죽이지 않음. 향후 원격 엔진(랜더 머신 분리, 공연장 세팅)으로 자연 확장. ComfyUI 백엔드를 *임포트 브리지*로 붙일 여지도 남김(차별점이자 호환 전략).
- **프레임 전송**: 프리뷰는 다운샘플(예: 320px) JPEG/WebP over WS로 충분. 최종 출력은 엔진이 직접 Spout/NDI/전용 출력창으로 — UI를 경유하지 않음(지연 최소화).

### 1.2 그래프 실행 모델
- 각 노드는 `tick(frame_ctx)` 를 갖는 프로세서. 노드별 target fps 독립 설정(`fps auto` = 업스트림 따름).
- 무거운 노드(디퓨전)는 최신 프레임만 소비하는 **latest-wins 큐** (프레임 드랍 허용, 지연 누적 금지).
- 모든 파라미터는 `ParamSpec`으로 선언 → 자동으로 (a) UI 생성 (b) 모듈레이션 타깃 등록 (c) OSC/MIDI 주소 부여 (d) 프로젝트 파일 직렬화. **이 단일 선언이 제품 전체의 척추.**

```python
# ParamSpec 예시 (엔진 측 선언 → UI 자동 생성)
class CkDiffusionNode(Processor):
    category = "generate"
    params = {
        "prompt":          Text(default=""),
        "negative":        Text(default=""),
        "prompt_strength": Slider(0.0, 2.0, default=1.0, modulatable=True),
        "seed":            Seed(mode=["random", "fixed"]),
        "creativity":      MultiMarkerSlider(0, 50, markers=[10, 35, 49]),  # denoise steps
        "controlnet":      Group({
            "enable": Toggle(True),
            "type":   Enum(["self", "pose", "depth", "canny", "seg"]),
            "weight": Slider(0.0, 2.0, default=1.0, modulatable=True),
        }),
        "advanced": Group({
            "noise": Toggle(False),
            "denoising_batch": Toggle(True),
            "similar_image_filter": Toggle(True),
            "sif_threshold": Slider(0.0, 1.0, default=0.9),
            "sif_max_skip":  IntSlider(1, 60, default=15),
        }),
    }
```

### 1.3 코어 노드 세트 (v1)
**Input**: Camera, Video File, NDI In, Spout/Syphon In, Image, Audio In(12ch)
**Vision**: Pose(OpenPose 포맷 출력), DepthMap, Segmentation(마스크/박스), Canny, HandTracker(21 landmarks ×2), FaceMesh(v1.5)
**Logic**: GestureRecognizer, MaskCompose(합/차/페더), Crossfade, Switch, LFO, EnvelopeFollower, ModMatrix(오디오→파라미터 라우터), OSC/MIDI In
**Generate**: CkDiffusion 상당(가칭 **LiveDiffusion**: SD-Turbo/LCM + TensorRT + Multi-ControlNet + Region Mask 입력 포트), StylePreset
**Composite**: Blend, RegionApply(마스크 영역만 디퓨전 결과로 치환), FeedbackLoop, ColorGrade
**Output**: MappedOutput(매핑 에디터 내장), NDI Out, Spout/Syphon Out, Recorder

---

## 2. 제스처 → 영역 디퓨전 (시그니처 기능 A)

목표 시나리오: *두 손가락(양손 검지·엄지)이 프레임을 만들면 그 사각형 내부만 디퓨전이 적용된다.*

파이프라인:
```
HandTracker ──▶ GestureRecognizer ──▶ RegionMask ──▶ LiveDiffusion(mask port)
 (21×2 lm)      (규칙 기반 v1)        (사각형/자유형,      └▶ RegionApply로 원본과 합성
                                      feather, 관성)
```
- **v1 제스처 셋(규칙 기반, ML 불필요)**: ① frame(양손 L자 대각 → 사각 마스크) ② pinch-spread(한손 핀치 거리 → 파라미터 값) ③ palm-push(손바닥 z 접근 → 씬 트리거) ④ point-hold(포인팅 1.5s → 해당 지점 원형 마스크)
- 마스크에는 **관성/스무딩**(one-euro filter)과 feather를 기본 적용 — 퍼포먼스에서 마스크가 떨리면 바로 티가 남.
- GestureRecognizer의 출력은 (a) 마스크 텍스처 (b) 이벤트(OSC처럼 내부 버스로 발행) 둘 다 — 이벤트는 씬 전환·프리셋 트리거에 바인딩 가능.
- 확장: 제스처 정의를 JSON 규칙(랜드마크 간 거리/각도 조건)으로 선언 → 사용자가 커스텀 제스처 추가 가능. 이것도 ComfyUI 대비 차별점.

## 3. 오디오 12스템 모듈레이션 매트릭스 (시그니처 기능 B)

### 3.1 입력 전략 (현실적 순서)
1. **v1: 멀티채널 입력 수신** — DAW/Ableton에서 12ch를 loopback(ASIO/BlackHole/VB-Matrix)으로 받음. 실시간 스템 분리는 하지 않음. VJ 실전에서는 어차피 스템을 미리 갖고 있거나 DAW에서 보냄.
2. **v1.5: 파일 스템 자동 분리** — 트랙 파일 드롭 시 HTDemucs(6-stem)로 오프라인 분리 → 내부 12트랙 슬롯에 배치.
3. **v2: 준실시간 분리** — 지연 허용 버퍼(2~4초) 모드. 공연보다는 리허설/설치용.

### 3.2 트랙별 특성 추출 (per stem, 60Hz)
`rms, peak, onset(transient), spectral centroid, flux, band energy(low/mid/high), pitch(옵션)` → 각각 정규화된 0..1 시그널.

### 3.3 ModMatrix — 제품의 심장
- 소스(12스템 × 8특성 + LFO + 제스처 + MIDI/OSC) × 타깃(**모든 modulatable 파라미터**) 매트릭스.
- 셀 단위: amount(-1..1), curve(lin/exp/log), smooth(ms), min/max clamp.
- **프롬프트 모듈레이션**: 프롬프트를 토큰 그룹으로 나누고 각 그룹에 weight를 모듈레이션 — `(star:{kick.rms}), (geometric:{hats.flux})` 식의 인라인 바인딩 문법. 임계값 크로스 시 프롬프트 프리셋 A/B 전환도 지원.
- UI는 슬라이더 우측에 작은 모듈레이션 링(현재 모듈레이션 양이 도넛으로 표시) — Ableton/Vital 신스의 문법 차용.

## 4. 프로젝션 매핑 출력

- MappedOutput 노드 안에 매핑 에디터: **v1 = 코너핀(4점 homography) + 다중 서피스 + 엣지 블렌딩 기초**, v1.5 = 베지어 메쉬 워프, 마스크 레이어.
- 서피스별 소스 노드 지정 가능(그래프의 어떤 노드 출력이든 서피스에 배정) → 한 그래프에서 멀티 서피스 설치 대응.
- 출력: 전용 풀스크린 창(멀티 모니터 지정), NDI Out, Spout/Syphon Out(→ Resolume/MadMapper 연동도 허용: 초기엔 "함께 쓰는" 포지션이 판매에 유리).
- 매핑 상태는 프로젝트와 별도 저장 슬롯(공연장 프리셋) — 장소가 바뀌어도 그래프는 유지.

## 5. 디자인 시스템 — "미니멀·규칙적"의 구체화

### 5.1 원칙 3개
1. **하나의 해부 구조**: 모든 노드는 동일한 카드 레이아웃. 예외 없음. 새 노드를 만들 때 디자인 결정은 "헤더 색 + 파라미터 선언"뿐이어야 함.
2. **파라미터는 6종 위젯으로만**: Slider(fill-bar) / Toggle / Enum(드롭다운) / Text / Seed / MultiMarkerSlider. 위젯 추가는 디자인 리뷰 필수.
3. **성능의 시각화는 UI의 일부**: 모든 노드 헤더에 해상도·fps·처리시간 배지. 병목 노드는 헤더 배지가 앰버→레드로.

### 5.2 토큰 (초안)
```css
/* color */
--bg-canvas: #0B0E14;      --bg-card: #1C2230;    --bg-field: #141926;
--text-hi: #F2F4F8;        --text-lo: #8A93A6;
--cat-input: #F26D6D;      --cat-vision: #F2D5B8;  --cat-depth: #9CC7F2;
--cat-generate: #7DF2A8;   --cat-audio: #B89CF2;   --cat-output: #F2B84D;
--state-warn: #F2B84D;     --state-error: #F26D6D; --state-ok: #7DF2A8;
/* geometry */
--radius-card: 12px; --radius-field: 8px;
--space-unit: 4px;   /* 모든 간격은 4의 배수 */
--param-row-h: 36px; /* 파라미터 행 높이 고정 */
/* type */
--font-ui: "Inter", "Pretendard", sans-serif;
--font-mono: "JetBrains Mono", monospace;  /* 값·경로·성능배지 */
```

### 5.3 노드 카드 해부 (고정 스펙)
```
┌─[핀][▶] NodeName            640x480 25fps 2ms ─[⚡]┐  ← 헤더 h=56, 카테고리색→다크 그라디언트
│        /processor/N/                    fps auto   │
├────────────────────────────────────────────────────┤
│ PARAMETERS ─ 탭형 섹션 라벨                          │
│  [라벨이 fill 안에 있는 슬라이더············]  0.30  │  ← 행 높이 36px 고정
│  Label                              [Enum      ▾]  │
│  Label                                      [ ○]   │
├────────────────────────────────────────────────────┤
│  (인라인 프리뷰 16:9, 클릭=팝아웃, 우하단 모니터아이콘) │
└────────────────────────────────────────────────────┘
```
- 연결선: 점선, 소스 카테고리 색, 흐름 방향 애니메이션(느린 dash offset).
- 다크 온리(v1). 밝은 무대 뒤 부스 환경 기준으로 대비 설계.
- 모션: 등장/접힘 150ms ease-out만. 장식 애니메이션 금지.

## 6. 성능 예산 (RTX 4090 / 640×480 기준 목표)

| 스테이지 | 목표 | 비고 |
|---|---|---|
| Camera capture | <2ms | |
| Pose (RTMPose-s TRT) | ~4ms | MediaPipe 폴백 |
| Depth (DA-V2-S TRT) | ~6ms | |
| Canny | <1ms | GPU |
| Seg (YOLOv8n-seg TRT) | ~5ms | person 한정이면 RVM 고려 |
| Diffusion (SD-Turbo 1step + CN, TRT) | 20~35ms | Similar Image Filter로 스킵 활용 |
| Composite + Mapping | <3ms | |
| **End-to-end** | **글래스-투-글래스 <100ms, 출력 20~30fps** | 스크린샷의 25fps와 정합 |

병렬화: 비전 노드들은 CUDA 스트림 분리, 디퓨전은 latest-wins. 해상도 프리셋: 512/640/768/1024(퀄리티 모드).

## 7. 라이선스·판매 전략 (초안)

- **모델**: 유료 영구 라이선스 + 1년 업데이트(Rive/Sublime 방식) 또는 구독. v1은 영구+업데이트권 권장(공연 도구는 오프라인 신뢰가 생명).
- **티어**: Personal(1석) / Pro(2석+상업공연+NDI/Spout 출력) / Edu(할인).
- **기술**: Keygen.sh 또는 자체 Ed25519 서명 라이선스 파일. **오프라인 활성화 필수**(공연장 인터넷 없음 전제). Tauri Rust 사이드에서 검증. 크랙 방어에 과투자하지 않기 — 가치는 업데이트와 프리셋 생태계에 둠.
- 모델 가중치는 앱에 미포함(다운로더 제공) — 배포 라이선스 리스크 회피. SD-Turbo/LCM 계열의 상업적 사용 조건은 릴리즈 전 법률 확인 항목으로 명시.
- 초기 GTM: VJ/미디어아트 커뮤니티 베타 → 공연 레퍼런스(본인 mid-2026 전시가 첫 쇼케이스) → 판매.

## 8. 마일스톤

- **M0 (2주) 스켈레톤**: Tauri+Svelte 셸, WS 프로토콜, ParamSpec→UI 자동생성, Camera 노드 1개가 프리뷰까지 도달. *여기서 디자인 시스템을 먼저 완성한다.*
- **M1 (3주) 비전 파이프라인**: Pose/Depth/Canny/Seg 노드 + 쿼드뷰, 노드 그래프 편집(연결/삭제/저장).
- **M2 (4주) LiveDiffusion**: StreamDiffusion 통합, TRT 빌드, ControlNet 멀티, Similar Image Filter, 25fps 달성.
- **M3 (2주) 제스처**: HandTracker + GestureRecognizer + RegionApply — "프레임 제스처 = 영역 디퓨전" 데모 완성.
- **M4 (3주) 오디오**: 12ch 입력, 특성 추출, ModMatrix UI, 프롬프트 바인딩.
- **M5 (3주) 출력**: MappedOutput(코너핀), 멀티 디스플레이, NDI/Spout, Recorder.
- **M6 (2주) 제품화**: 라이선스, 인스톨러, 프리셋 팩, 문서.
- 이후: 플러그인 SDK 공개, FaceMesh, 메쉬 워프, 준실시간 스템 분리.

각 마일스톤의 Definition of Done은 §10의 검증 룰을 따른다.

---

## 9. 리포지토리 구조 (모노레포)

```
kkum/
├── CLAUDE.md                  # §10.1 내용
├── TODO.md                    # 작업 루프의 단일 진실
├── apps/
│   └── studio/                # Tauri 2 + Svelte 5 (SvelteKit adapter-static)
│       ├── src/lib/design/    # 토큰, 6종 위젯, NodeCard — 여기만 스타일 존재
│       ├── src/lib/graph/     # 그래프 캔버스, 연결, 직렬화
│       ├── src/lib/protocol/  # WS 스키마 (zod, engine과 계약)
│       └── src-tauri/         # Rust: 창관리, Spout/NDI 브리지, 라이선스
├── engine/                    # Python
│   ├── kkum_engine/
│   │   ├── core/              # scheduler, ParamSpec, graph, frame bus
│   │   ├── nodes/             # 노드당 1파일, ParamSpec 선언 필수
│   │   ├── diffusion/         # streamdiffusion 래퍼, TRT 캐시
│   │   ├── audio/             # capture, features, modmatrix
│   │   └── protocol/          # WS 서버, 스키마 (pydantic, zod와 미러)
│   └── tests/
├── packages/
│   └── schema/                # 프로토콜 JSON Schema — zod/pydantic 양쪽의 원천
├── skills/                    # §10.2 Claude Code 스킬들
└── docs/
```

## 10. Harness 엔지니어링 — Claude Code 운용 설계

### 10.1 CLAUDE.md (초안 — 리포 루트에 그대로 사용)
```markdown
# KKUM — Claude Code 운용 규칙

## 프로젝트
실시간 AI 비주얼 퍼포먼스 엔진. UI=Tauri+Svelte5(apps/studio), 엔진=Python(engine/).
아키텍처·기능 정의는 docs/PLAN.md가 원천. PLAN과 충돌하는 구현 금지, 충돌 발견 시 TODO.md에 질문 기록.

## 작업 루프
1. TODO.md 최상단 미완료 항목 1개만 수행. 임의 확장 금지.
2. 구현 → 검증(아래) → TODO.md 체크 + 한 줄 결과 기록 → 커밋(prefix: feat/fix/refactor/design).
3. 검증 실패 상태로 다음 항목 이동 금지.

## 불변 규칙 (위반=수정 대상)
- R1 스타일은 src/lib/design/ 밖에서 선언 금지. 컴포넌트에 하드코딩 색/px 금지 — 토큰만.
- R2 파라미터 UI를 손으로 만들지 말 것. ParamSpec → 자동 생성 경로만 사용.
- R3 UI↔엔진 통신은 packages/schema 스키마를 통해서만. 임의 메시지 타입 추가 금지(스키마 먼저).
- R4 엔진 노드는 nodes/ 1파일 1노드, Processor 상속, tick() 안에서 blocking I/O 금지.
- R5 프레임 경로에 UI 경유 금지 — 최종 출력은 엔진이 직접 낸다.
- R6 새 위젯 타입 추가 금지(6종 고정). 필요하면 TODO.md에 제안만.
- R7 새 의존성 추가 전 TODO.md에 사유 기록. 특히 UI 라이브러리 추가 금지(디자인 시스템 자체 구현).
- R8 모든 modulatable 파라미터는 ModMatrix 타깃 자동 등록 확인.

## 검증
- UI: `pnpm check && pnpm test` + Playwright MCP로 해당 화면 스크린샷 → docs/verify/에 저장, 토큰 위반 육안 확인 항목 체크리스트 수행.
- 엔진: `pytest` + 해당 노드 벤치(`python -m kkum_engine.bench <node>`) — 성능 예산표(PLAN §6) 초과 시 실패로 간주.
- 프로토콜 변경: schema 수정 → zod/pydantic 양쪽 재생성 → 계약 테스트 통과.

## 커뮤니케이션
- 불확실하면 구현하지 말고 TODO.md `## Questions`에 적을 것.
- 성능 수치는 반드시 실측값으로 보고(추정치 표기 금지).
```

### 10.2 스킬 세트 (skills/ 디렉토리)
| 스킬 | 트리거 | 내용 요약 |
|---|---|---|
| `design-system` | 모든 UI 작업 | 토큰 전체 목록, 6종 위젯 API, NodeCard 해부 스펙, 안티패턴 예시(하드코딩 색, 임의 spacing), 스크린샷 검증 체크리스트 |
| `node-authoring` | 새 노드 추가 | Processor 템플릿, ParamSpec 작성법, latest-wins 큐 사용법, 벤치 등록 절차, UI 자동생성 확인법 |
| `protocol` | WS/스키마 작업 | 스키마 수정 절차, zod↔pydantic 미러 생성 커맨드, 버저닝 규칙 |
| `realtime-perf` | 성능 작업 | CUDA 스트림/TRT 빌드 캐시, 프로파일링 커맨드, 예산표, "지연 누적 금지" 패턴 |
| `verify-ui` | 매 UI 작업 종료 시 | Playwright MCP 시나리오: 앱 기동→노드 생성→파라미터 조작→스크린샷→토큰 검사 |
| `gesture-rules` | 제스처 작업 | 랜드마크 인덱스 맵, JSON 제스처 규칙 문법, one-euro 필터 파라미터 가이드 |
| `audio-mod` | 오디오/ModMatrix | 특성 추출 정의(정규화 방식 포함), 매트릭스 직렬화 포맷, 프롬프트 바인딩 문법 |

### 10.3 2-에이전트 운용 (기존 워크플로 연장)
- **Claude Code(구현)**: TODO.md 루프 수행. 터미널 + Playwright MCP.
- **claude.ai 세션(기획/검증, 본 세션)**: PLAN 개정, TODO 배치 설계, 스크린샷 리뷰, 성능 수치 검토.
- TODO.md 항목은 항상 이 세션에서 "검증 가능한 완료 조건" 포함해 작성 → Claude Code에 전달.

### 10.4 TODO.md 초기 배치 (M0)
```markdown
# TODO — M0 Skeleton
- [ ] T1 모노레포 스캐폴드 (구조=PLAN §9) — 완료조건: pnpm dev로 빈 Tauri 창 기동
- [ ] T2 디자인 토큰 + 6종 위젯 구현 — 완료조건: /design 데모 페이지에 전 위젯 렌더, verify-ui 스크린샷
- [ ] T3 NodeCard 컴포넌트 — 완료조건: 6개 카테고리 색상 변형 데모, 헤더 성능배지 목업 포함
- [ ] T4 packages/schema v0 (hello, node.list, param.set, frame.preview) + zod/pydantic 생성
- [ ] T5 engine 스켈레톤: WS 서버 + scheduler + ParamSpec — 완료조건: pytest 통과
- [ ] T6 Camera 노드 E2E — 완료조건: 카메라 프리뷰가 NodeCard 안에 15fps+로 표시, 실측 fps 배지 동작
## Questions
(비어 있음)
```

## 11. 리스크 & 오픈 퀘스천

1. **모델 상업 라이선스**: SD-Turbo(비상업 제약 있음) vs LCM-LoRA vs SDXL-Lightning — 판매 제품이므로 M2 전에 확정 필요. *가장 중요한 오픈 이슈.*
2. Spout/Syphon/NDI Rust 바인딩 성숙도 — M0에서 스파이크 테스트.
3. 640×480↑ 해상도에서 25fps 유지 여부 — 4090 실측으로 §6 예산표 갱신.
4. 실시간 스템 분리는 v1 범위에서 제외 유지할 것(확정 요망).
5. 제품명 — KKUM 유지? (꿈틀/URLD 계보와의 관계 정리 필요)
```
