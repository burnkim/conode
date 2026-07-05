---
name: realtime-perf
description: conode 실시간 성능 작업 — CUDA 스트림/TRT 빌드 캐시, 프로파일링, §6 예산표, "지연 누적 금지" 패턴. 성능 관련 노드/파이프라인 작업 시 사용.
---

# realtime-perf — conode 실시간 성능 (PLAN §6 / §10.2)

타깃: **RTX 4090 / 640×480 / 20~30fps, glass-to-glass <100ms**. 개발기(Mac)에서는
벤치 도구는 돌지만 4090 예산은 참고용(TRT/CUDA 미존재).

## §6 성능 예산 (4090 / 640×480, ms/frame)
| 스테이지 | 목표 | 비고 |
|---|---|---|
| Camera capture | <2ms | |
| Pose (RTMPose-s TRT) | ~4ms | MediaPipe 폴백은 더 느림 |
| Depth (DA-V2-S TRT) | ~6ms | |
| Canny | <1ms | GPU |
| Seg (YOLOv8n-seg TRT) | ~5ms | |
| Diffusion (LCM 1~4step + CN, TRT) | 20~35ms | SIF 로 스킵 활용 |
| Composite + Mapping | <3ms | |
| **End-to-end** | **<100ms · 20~30fps** | |

## 프로파일링
```bash
# 단일 노드
python -m conode_engine.bench canny --frames 200 --size 640x480
# 전체 + 예산 강제(초과 시 exit 1 — CI/검증)
python -m conode_engine.bench all --size 640x480 --enforce
```
성능 수치는 **실측값으로만 보고**(추정치 금지). 예산 초과 = 실패로 간주(CLAUDE.md).

## 지연 누적 금지 (핵심 패턴)
- **latest-wins**: 무거운 노드(디퓨전)는 최신 프레임만 소비. `core.latest_wins.LatestWins`
  — 소비 안 된 이전 프레임은 드랍(카운트). 큐잉 = 지연 누적 → 금지.
- **scheduler 기한 리셋**: `core.scheduler.Scheduler` 는 주기보다 늦으면 다음 기한을
  현재로 리셋(밀린 만큼 몰아치지 않음).
- **Similar Image Filter**: `diffusion.sif.SimilarImageFilter` — 유사 프레임은 디퓨전
  스킵(최대 `sif_max_skip` 연속), 직전 결과 재사용. 파라미터: `sif_threshold`, `sif_max_skip`.
- **노드 크래시 격리**: `Processor.tick` 은 process 예외를 잡아 output=None 처리 —
  한 노드가 죽어도 그래프 전체는 계속(§1.1).

## CUDA 스트림 / TensorRT (4090)
- **비전 노드는 CUDA 스트림 분리** — Pose/Depth/Seg 를 별 스트림에서 병렬(§6). 디퓨전은
  latest-wins 로 최신 프레임만.
- **TRT 빌드 캐시**: StreamDiffusion 의 `accelerate_with_tensorrt(stream, engine_dir, ...)`
  는 `engine_dir`(기본 `models/trt-engines`)에 최초 1회 엔진을 빌드하고 이후 재사용.
  - 최초 빌드는 수 분. 해상도/배치/모델이 바뀌면 재빌드된다 → 프리셋 해상도(512/640/768/1024)
    별로 캐시가 쌓인다.
  - `models/`(및 `models/trt-engines`)는 gitignore. 배포 시 타깃 GPU 에서 빌드.
- **dtype**: float16. **cfg**: LCM 은 보통 guidance_scale=1.0 (cfg_type="none").
- **StreamDiffusion 셋업**: `engine/requirements-cuda.txt` 참고. ControlNet 지원은 버전별
  차이가 커서 4090 에서 검증 필요.

## 백엔드 교체 지점
`diffusion.backend.select_backend()` 가 CUDA 시 `StreamDiffusionBackend`(LCM), 아니면
`FallbackBackend`(Mac 스타일라이즈)를 고른다. 노드 코드는 `DiffusionRequest`/`generate()`
계약만 알면 되고 백엔드에 무관하다.
