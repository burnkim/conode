# conode

**실시간 AI 비주얼 퍼포먼스 엔진** — 라이브 영상·오디오·제스처를 실시간 디퓨전과
프로젝션 매핑까지 하나의 노드 그래프로 잇는 퍼포먼스 악기(instrument).

> ComfyUI가 이미지를 "만든다"면, conode는 이미지를 "연주한다". 모든 노드가 지정 fps로
> 상시 스트리밍되고, 오디오·제스처·MIDI·LFO가 모든 파라미터를 모듈레이션한다.
> 설계 원천: [`docs/PLAN.md`](docs/PLAN.md).

## 빠른 시작

```bash
# 1) 프론트엔드 (Tauri 2 + SvelteKit)
pnpm install
pnpm dev                      # 빈 Tauri 창 / http://localhost:1420

# 2) 엔진 (Python 3.12)
cd engine && uv venv --python 3.12 .venv
uv pip install --python .venv -e ".[dev,runtime]"
cd .. && engine/.venv/bin/python -m conode_engine              # ws://127.0.0.1:8787 (티어 auto)
#     저사양 확인용 최소 티어:  … -m conode_engine --tier potato
#     Apple Silicon/CUDA 실디퓨전: docs/spec-tiers.md (requirements-diffusers.txt)

# 3) 브라우저에서 화면 열기 (엔진 실행 중이어야 함)
#   /design  디자인 시스템      /nodes  NodeCard 갤러리
#   /live    라이브 그래프       /quad   비전 쿼드뷰
#   /graph   노드 그래프 편집    /audio  오디오 ModMatrix
#   /output  코너핀 매핑 출력    /scenes 씬/큐
```
> `/live`·`/quad`·`/graph`·`/audio`·`/output`은 엔진 연결 필요. 첫 실행 시 MediaPipe 모델은
> `engine/models/`로 자동 다운로드(캐시).

## 시그니처 기능
- **제스처 = 영역 디퓨전 (§2)**: 양손으로 프레임을 만들면 그 사각형 내부만 디퓨전.
  `Camera → HandTracker → GestureRecognizer → RegionMask → LiveDiffusion.mask`.
- **오디오 12스템 ModMatrix (§3)**: 스템×특성 → modulatable 파라미터 모듈레이션 + 프롬프트
  바인딩 `(star:{kick.rms})`. "제품의 심장". `/audio` 에서 소스→타깃 셀 편집(추가/amount/curve/삭제).
  소스 = 스템×특성 + LFO + 제스처 + 신호 노드(`sig.<name>` — LFO·EnvelopeFollower).

## 노드 (24종)
| 카테고리 | 노드 |
|---|---|
| Input | Camera · VideoFile · Image · AudioIn |
| Vision | Canny · Pose · Segmentation · HandTracker |
| Analysis(Depth) | DepthMap · GestureRecognizer · RegionMask · MaskCompose |
| Generate | LiveDiffusion · Blend · Crossfade · ColorGrade · Switch · FeedbackLoop · StylePreset |
| Audio | ModMatrix · LFO · EnvelopeFollower |
| Output | MappedOutput · Recorder |

> 노드는 엔진 `Processor` 클래스만 추가하면 UI(파라미터 패널·프리뷰)가 **ParamSpec 에서
> 자동 생성**된다(R2) — 손으로 만들지 않는다. `/graph` 팔레트에 전 노드 노출.

## 라이브 악기 기능
- **스펙 티어**: LiveDiffusion 을 하드웨어별로 — `potato`(CPU, 이 Mac 확인용) ·
  `mps_low`(Apple Silicon) · `cuda_3070` · `cuda_max`(TRT). auto 감지 + `--tier` +
  /live 드롭다운, 의존성 없으면 자동 폴백. [`docs/spec-tiers.md`](docs/spec-tiers.md).
- **파라미터 자동 UI (R2)**: 노드 ParamSpec → 6종 위젯 자동 렌더 + 모듈레이션 링.
- **노드별 fps + latest-wins (§1.2)**: 무거운 노드는 낮은 fps, 다운스트림은 최신 출력 소비.
- **씬/큐 (§0.2)**: 파라미터 스냅샷 저장 → 크로스페이드 recall. 제스처 이벤트(palm_push/
  point_hold)를 씬에 바인딩해 트리거(§2).
- **커스텀 제스처**: JSON 규칙(dist/angle/finger)으로 사용자 제스처 추가(ComfyUI 대비 차별점).

## 아키텍처
2-프로세스: **UI**(`apps/studio`, Tauri 2 + Svelte 5) ↔ **엔진**(`engine/`, Python).
계약은 `packages/schema`(JSON Schema → zod/pydantic 생성)로만(R3). 프레임은 프리뷰
JPEG over WS, 최종 출력은 엔진이 직접(R5).

```
apps/studio/  Tauri+Svelte (src/lib/design 토큰·위젯·NodeCard, graph 편집, protocol)
engine/       Python (core 그래프/스케줄러, nodes, diffusion, audio, gesture, protocol)
packages/schema/  프로토콜 원천(zod/pydantic 생성)
skills/       realtime-perf · gesture-rules
docs/         PLAN.md · output-bridges.md · verify/(스크린샷)
presets/      예제 그래프 프리셋
```

## 마일스톤 상태
| | | 상태 |
|---|---|---|
| M0 | 스켈레톤 (모노레포·디자인시스템·프로토콜·엔진·Camera E2E) | ✅ |
| M1 | 비전 파이프라인 (Canny/Pose/Depth/Seg·쿼드뷰·그래프 편집기) | ✅ |
| M2 | LiveDiffusion (스펙 티어: potato→mps→3070→4090, LCM) | ✅ potato(이 Mac) · 🔶 GPU 티어 배포검증 |
| M3 | 제스처 = 영역 디퓨전 | ✅ |
| M4 | 오디오 12스템 ModMatrix | ✅ |
| M5 | 출력 (코너핀·Recorder / NDI·Spout·Syphon) | ✅ 코어 · 🔶 네이티브 문서 |
| M6 | 제품화 (라이선스·프리셋·문서) | ✅ |

> 🔶 = Mac 개발기에서 실행 불가(CUDA/TRT, 네이티브 브리지) → 코드+문서, 타깃 배포 시 검증.

리뷰 후속 완료: ParamSpec→UI 자동생성(R2 척추), 노드별 fps+latest-wins, v1 노드 8종
추가(총 21종), 제스처 JSON 규칙·ModMatrix 제스처 소스, 씬/큐 + 제스처 이벤트 바인딩.
추가(2026-07-07): 스펙 티어(potato~4090), 루트 홈, ModMatrix 매트릭스 에디터,
VideoFile·LFO·EnvelopeFollower 노드(총 24종).
남은 로드맵: FaceMesh(v1.5), 메쉬 워프(v1.5), 준실시간 스템 분리(v2), MIDI/OSC In,
플러그인 SDK.

## 개발
```bash
pnpm --filter @conode/studio check        # svelte-check
pnpm --filter @conode/studio test         # vitest (프로토콜 계약)
engine/.venv/bin/python -m pytest engine/tests/   # 엔진
engine/.venv/bin/python -m conode_engine.bench all --enforce   # §6 성능 예산
pnpm --filter @conode/schema generate     # 프로토콜 재생성(스키마 수정 후)
```
운용 규칙: [`CLAUDE.md`](CLAUDE.md) (작업 루프 · 불변 규칙 R1~R8). 작업 큐: [`TODO.md`](TODO.md).

## 라이선스 (제품)
유료 영구 + 업데이트권. 티어 Personal/Pro/Edu. Ed25519 서명 라이선스 파일 · **오프라인
활성화**(공연장 인터넷 없음 전제). `python -m conode_engine.licensing`. 모델 가중치는 앱
미포함(다운로더). SD-Turbo 등 상업 라이선스는 LCM 채택으로 해소(§11).
