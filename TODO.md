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
- [ ] T9 프로토콜 확장 — graph 메시지(graph.get/node.add/node.connect/node.remove) 스키마 + zod/pydantic 재생성 + 계약 테스트.
- [ ] T10 Pose 노드 (MediaPipe, 폴백) — 스켈레톤 오버레이 프리뷰.
- [ ] T11 Depth 노드 (경량 모델/근사, 폴백) — 뎁스맵 프리뷰.
- [ ] T12 Segmentation 노드 (MediaPipe SelfieSeg/YOLOv8-seg, 폴백) — 마스크 프리뷰.
- [ ] T13 쿼드뷰 UI — 4분할 노드 프리뷰 레이아웃.
- [ ] T14 노드 그래프 편집 UI — 캔버스 노드 배치/연결선/삭제/저장(직렬화 왕복).

## Questions / 리뷰 대기 (기획 세션)
- Q1 T2에서 인터랙션 파생 토큰(--field-fill/border/hover, --focus-ring, --knob 등) 추가함 → §5.1상 디자인 리뷰 대상. 확정 필요.
- Q2 폰트(Inter/Pretendard/JetBrains Mono) 미번들 → 현재 시스템 폴백. 번들 방식/라이선스 결정 필요(오프라인 공연 도구).
- Q3 카메라 권한: 실카메라는 macOS TCC 그랜트 필요(첫 cap.read()가 블록). 배포 시 Tauri 앱 번들의 카메라 usage 권한/entitlement 설정 필요.
- Q4 프로토콜 v0는 node.list에 ParamSpec 미포함(id/name/category/index만). ParamSpec→UI 자동생성(R2)의 완전한 배선은 M1에서 node.describe 확장 필요.
