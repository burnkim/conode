# 출력 브리지 — NDI / Spout / Syphon / 멀티디스플레이 (M5 T33)

> **상태: 네이티브/생태계 의존 — Mac 개발기에서 미검증. 배포 타깃에서 검증.**
> (PLAN §4, §11 리스크 #2: Spout/Syphon/NDI Rust 바인딩 성숙도)

프레임 워프(코너핀)와 레코더는 엔진(cv2)에서 처리·검증됨(T30/T31). 실제 **화면 출력**
(전용 풀스크린 창, NDI/Spout/Syphon)은 플랫폼 네이티브라 Tauri(Rust) 사이드에서 구현하고
타깃 환경에서 검증한다. 최종 출력은 UI(WS)를 경유하지 않는다 — 엔진이 직접 낸다(R5).

## 아키텍처
```
LiveDiffusion → MappedOutput(코너핀, 엔진) → ┬→ 전용 풀스크린 창(멀티 모니터) [Tauri]
                                            ├→ NDI Out        [engine or Rust]
                                            ├→ Spout Out (Win) / Syphon Out (Mac) [Rust]
                                            └→ Recorder(파일)  [엔진 cv2] ✅ 검증됨
```

## 전용 출력 창 · 멀티디스플레이 (Tauri, Rust)
- `apps/studio/src-tauri`: 두 번째 WebGL2/WebGPU 풀스크린 창을 지정 모니터에 생성.
  - `tauri::WindowBuilder` + `Monitor` API 로 대상 디스플레이 선택, `fullscreen(true)`.
  - 프레임은 엔진이 SharedMemory/Spout/Syphon 으로 직접 전달(프리뷰 WS 경유 금지, R5).
- 매핑 상태는 프로젝트와 별도 저장 슬롯(공연장 프리셋, §4) — 장소가 바뀌어도 그래프 유지.

## NDI Out (크로스플랫폼)
- NDI SDK(무료, 재배포 조건 확인) + Rust 바인딩(`ndi` crate) 또는 Python(`ndi-python`).
- 엔진 MappedOutput 결과(BGR)를 NDI 프레임(UYVY/BGRA)으로 송출.
- 검증: NDI Studio Monitor / Resolume 에서 `conode` 소스 수신 확인.

## Spout Out (Windows)
- Spout2 + Rust FFI 또는 `spout-rs`. DX11 텍스처 공유. Windows 전용.
- 검증: Resolume/MadMapper 에서 Spout 소스 수신.

## Syphon Out (macOS)
- Syphon Framework + Rust/ObjC 브리지. Metal/GL 텍스처 공유. macOS 전용.
- 검증: Resolume/MadMapper(Mac) 에서 Syphon 소스 수신.

## 포지셔닝 (§0.2, §4)
초기엔 Resolume/MadMapper 와 "함께 쓰는" 포지션 → Spout/Syphon/NDI Out 이 판매에 유리.
자체 코너핀(T30)은 단일 서피스 v1; 멀티 서피스·베지어 메쉬 워프는 v1.5.

## 다음 (배포 타깃 착수 순서)
1. Tauri 전용 출력 창 + 멀티 모니터 선택 (Mac/Win 공통, 가장 먼저).
2. Syphon(Mac) / Spout(Win) Out — 각 OS 에서.
3. NDI Out — 크로스플랫폼 공용.
