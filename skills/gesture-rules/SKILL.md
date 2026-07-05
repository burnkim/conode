---
name: gesture-rules
description: conode 제스처 작업 — 랜드마크 인덱스 맵, JSON 제스처 규칙 문법, one-euro 필터 가이드. HandTracker/GestureRecognizer/RegionMask 작업 시 사용.
---

# gesture-rules — conode 제스처 (PLAN §2)

시그니처: **프레임 제스처 = 영역 디퓨전**. 파이프라인:
`Camera → HandTracker → GestureRecognizer → RegionMask → LiveDiffusion.mask`.
규칙 기반 v1(ML 불필요) + JSON 규칙 확장(ComfyUI 대비 차별점).

## 랜드마크 인덱스 (MediaPipe Hand 21점)
```
0 wrist
1-4  thumb  (cmc, mcp, ip, tip)
5-8  index  (mcp, pip, dip, tip)
9-12 middle
13-16 ring
17-20 pinky
```
tip=끝, pip=중간 관절. `gesture.rules.LM` 딕셔너리로 이름→인덱스 조회.

## 내장 제스처 (v1)
| 제스처 | 조건 | 출력 |
|---|---|---|
| **frame** | 양손 | 두 손 thumb+index 코너 bbox → `rect` (영역 디퓨전) |
| **pinch-spread** | 한손 | thumb-index 거리 → `value` 0..1 (파라미터 모듈레이션) |
| **point-hold** | 한손 검지만 폄 | `circle` at 검지끝. point_hold_sec 유지 → event `point_hold` |
| **palm-push** | 한손 span 큼(z 근접) | rising edge → event `palm_push` |

GestureRecognizer 출력 state: `{type, rect, circle, value, event, hands}`. event 는
씬 전환·프리셋 트리거에 바인딩(내부 버스). rect/circle 은 정규화 좌표(0..1).

## JSON 규칙 확장
사용자가 커스텀 제스처를 JSON 으로 선언 → `gesture.rules.eval_json_rules(hands, rules)`.
```json
[
  {
    "name": "peace",
    "hand": 0,
    "when": [
      {"type": "extended", "finger": "index"},
      {"type": "extended", "finger": "middle"},
      {"type": "curled",   "finger": "ring"},
      {"type": "dist", "a": 8, "b": 12, "op": ">", "value": 0.08}
    ],
    "emit": {"type": "event", "event": "peace"}
  }
]
```
조건 타입: `extended`/`curled`(finger), `dist`(a,b 랜드마크, op `<`/`>`, value 정규화 거리).
emit: `{type, event}` 또는 `{type, at_landmark, radius}`(원형 마스크). 첫 매칭 규칙 채택.

## one-euro 필터 (관성/스무딩)
마스크 좌표는 `gesture.one_euro.OneEuroVec` 로 채널별 스무딩 — 저속 지터 억제, 고속 반응.
- `min_cutoff` ↓ = 스무딩↑(관성↑, 지연↑). RegionMask `responsiveness` 파라미터.
- `beta` = 속도 적응(움직임 빠를수록 지연↓). 기본 0.02.
- 제스처 타입이 바뀌면 필터 리셋(스냅).
- feather(가우시안)로 마스크 가장자리 부드럽게 → 퍼포먼스에서 마스크 떨림 방지.

## RegionMask 동작
- frame→사각, point→원형. `no_gesture=full`(제스처 없으면 전체 디퓨전) / `none`(영역만).
- 출력 = BGR 마스크(white on black) → LiveDiffusion.mask → 그 영역만 `out=where(mask, diffused, original)` (§2 RegionApply, LiveDiffusion.process 내장).
