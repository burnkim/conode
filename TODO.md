# TODO — M0 Skeleton
- [x] T1 모노레포 스캐폴드 (구조=PLAN §9) — 완료조건: pnpm dev로 빈 Tauri 창 기동
      ↳ 2026-07-05 완료: pnpm workspace + apps/studio(Tauri2 + SvelteKit/Svelte5 adapter-static) + engine/packages/skills 골격. `pnpm dev`로 341 crates 컴파일 후 빈 conode-studio 창 기동 확인(프로세스 상주·vite :1420). 이름 kkum→conode. 추가 의존성: @types/node(vite.config.ts process 타입, R7).
- [ ] T2 디자인 토큰 + 6종 위젯 구현 — 완료조건: /design 데모 페이지에 전 위젯 렌더, verify-ui 스크린샷
- [ ] T3 NodeCard 컴포넌트 — 완료조건: 6개 카테고리 색상 변형 데모, 헤더 성능배지 목업 포함
- [ ] T4 packages/schema v0 (hello, node.list, param.set, frame.preview) + zod/pydantic 생성
- [ ] T5 engine 스켈레톤: WS 서버 + scheduler + ParamSpec — 완료조건: pytest 통과
- [ ] T6 Camera 노드 E2E — 완료조건: 카메라 프리뷰가 NodeCard 안에 15fps+로 표시, 실측 fps 배지 동작
## Questions
(비어 있음)
