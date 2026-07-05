# TODO — M0 Skeleton
- [x] T1 모노레포 스캐폴드 (구조=PLAN §9) — 완료조건: pnpm dev로 빈 Tauri 창 기동
      ↳ 2026-07-05 완료: pnpm workspace + apps/studio(Tauri2 + SvelteKit/Svelte5 adapter-static) + engine/packages/skills 골격. `pnpm dev`로 341 crates 컴파일 후 빈 conode-studio 창 기동 확인(프로세스 상주·vite :1420). 이름 kkum→conode. 추가 의존성: @types/node(vite.config.ts process 타입, R7).
- [x] T2 디자인 토큰 + 6종 위젯 구현 — 완료조건: /design 데모 페이지에 전 위젯 렌더, verify-ui 스크린샷
      ↳ 2026-07-05 완료: tokens.css(§5.2)+base.css, 6종 위젯(Slider fill-bar/Toggle/Enum/Text/Seed/MultiMarkerSlider) src/lib/design/에 구현(R1/R6). /design 갤러리에 스와치14+위젯6 렌더, svelte-check 0/0, /browse 스크린샷 docs/verify/T2-design-system.png, 토글·Enum 반응성 실측 확인. 폰트 미번들(시스템 폴백).
- [x] T3 NodeCard 컴포넌트 — 완료조건: 6개 카테고리 색상 변형 데모, 헤더 성능배지 목업 포함
      ↳ 2026-07-05 완료: NodeCard.svelte(§5.3 고정 해부: 헤더 h56 카테고리색→다크 그라디언트, 핀/재생/이름/perf배지/⚡/경로/fps, PARAMETERS(T2 위젯), 16:9 인라인 프리뷰). /nodes 데모 6 카테고리 + 성능배지 ok4/warn1/error1(fps 기준). svelte-check 0/0, 스크린샷 docs/verify/T3-nodecard.png.
- [x] T4 packages/schema v0 (hello, node.list, param.set, frame.preview) + zod/pydantic 생성
      ↳ 2026-07-05 완료: protocol.schema.json(원천, 판별유니온) + generate.mjs로 zod(apps/studio/src/lib/protocol/messages.ts)·pydantic(engine/conode_engine/protocol/messages.py) 생성(R3). 공유 픽스처 examples.json으로 계약 테스트 양쪽 통과(pytest 17, vitest 16). R7 추가 의존성: zod(UI 런타임), vitest(UI dev), pydantic·pytest(engine, py3.12 venv=engine/.venv).
- [ ] T5 engine 스켈레톤: WS 서버 + scheduler + ParamSpec — 완료조건: pytest 통과
- [ ] T6 Camera 노드 E2E — 완료조건: 카메라 프리뷰가 NodeCard 안에 15fps+로 표시, 실측 fps 배지 동작
## Questions
(비어 있음)
