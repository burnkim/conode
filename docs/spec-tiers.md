# 스펙 티어 — 다양한 하드웨어에서 LiveDiffusion 돌리기

conode 는 **한 코드베이스로 저사양(이 Mac)부터 고사양(4090)까지** 커버한다.
LiveDiffusion 의 백엔드·디바이스·해상도(저크기)·스텝을 하나의 **SpecProfile** 로 묶고,
장비에 맞는 티어를 자동 감지하거나 사용자가 선택한다. 요청 티어의 의존성이 없으면
**조용히 아래 티어로 폴백**해서 엔진이 죽지 않는다.

구현: `engine/conode_engine/diffusion/spec.py` (프로파일·감지·폴백),
`backend.py`(선택), `diffusers_backend.py`(MPS/CUDA), `streamdiffusion_backend.py`(TRT).

## 티어 표

| 티어 | 백엔드 | 디바이스 | 해상도 | 스텝 | 하드웨어 | 실디퓨전 |
|---|---|---|---|---|---|---|
| `potato` | fallback(cv2) | CPU | 256×144 | 1 | 어디서나 (이 Mac 포함) | ✕ (스타일라이즈) |
| `mps_low` | diffusers | MPS | 384×384 | 2 | Apple Silicon M1~ | ✓ (느림) |
| `cuda_3070` | diffusers | CUDA | 512×512 | 4 | ≈8GB VRAM (3060~3080) | ✓ |
| `cuda_max` | StreamDiffusion+TRT | CUDA | 512×512 | 2 | ≈16GB+ (4080/4090) | ✓ (최고 처리율) |

모델은 전 티어 공통 **SD1.5 + LCM-LoRA** (permissive/상업 OK, PLAN §11).

## 선택 방법

- **자동(기본)**: `python -m conode_engine` → `auto`. CUDA 있으면 `cuda_3070`,
  Apple Silicon 이면 `mps_low`, 그 외 `potato`. (`cuda_max` 는 TRT 셋업이 커서 자동
  선택엔 포함 안 됨 — 명시적으로 골라야 TRT 를 시도한다.)
- **CLI**: `python -m conode_engine --tier potato` (저사양 확인) / `--tier cuda_3070` 등.
- **UI(/live)**: LiveDiffusion 노드의 `tier` 드롭다운. ParamSpec → 자동 생성(R2)이라
  손으로 만든 UI 가 아니다. 런타임 변경 시 백엔드 재선택.

시작 시 엔진이 감지 결과를 출력한다:
```
spec tier: auto → potato (fallback/cpu, 256x144) · devices=['cpu']
```

## 설치

| 티어 | 설치 |
|---|---|
| `potato` | 추가 설치 없음 (기본 런타임의 opencv/numpy 로 동작) |
| `mps_low` | `pip install -r engine/requirements-diffusers.txt` (Apple Silicon) |
| `cuda_3070` | `pip install --extra-index-url https://download.pytorch.org/whl/cu121 -r engine/requirements-diffusers.txt` |
| `cuda_max` | `engine/requirements-cuda.txt` + StreamDiffusion 소스 + `install-tensorrt` |

## 폴백 규칙

`select_backend(profile)` 는 다음 순서로 안전하게 내려간다:
1. 요청 티어의 **디바이스**가 없으면(예: Mac 에서 `cuda_3070`) → `spec.downgrade()` 로 하강.
2. 백엔드 **패키지**가 없으면(torch/diffusers/streamdiffusion 미설치) → 최종 `potato`(fallback).
3. `cuda_max` 인데 streamdiffusion 만 없고 diffusers 는 있으면 → `cuda_3070` 로 대체 후 폴백.

즉 어떤 티어를 지정해도 엔진은 **항상 뜨고**, 가능한 최고 품질로 자동 정착한다.

## 검증 상태 (2026-07-07, Apple M1 Max)

- `potato` — **이 Mac 에서 E2E 실측**. `/live` LiveDiffusion 14fps(target 15, latest-wins),
  256×144 작업→프리뷰 복원. `docs/verify/H4-tier-live.png`.
- `mps_low` / `cuda_3070` / `cuda_max` — 코드+감지+폴백 로직은 검증(테스트 `test_spec.py`).
  실모델 실행은 torch/diffusers 설치 후(이 Mac MPS) 또는 해당 GPU 배포 시 검증 대기(블라인드).
