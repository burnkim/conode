# CONODE — Claude Code 운용 규칙

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
- 엔진: `pytest` + 해당 노드 벤치(`python -m conode_engine.bench <node>`) — 성능 예산표(PLAN §6) 초과 시 실패로 간주.
- 프로토콜 변경: schema 수정 → zod/pydantic 양쪽 재생성 → 계약 테스트 통과.

## 커뮤니케이션
- 불확실하면 구현하지 말고 TODO.md `## Questions`에 적을 것.
- 성능 수치는 반드시 실측값으로 보고(추정치 표기 금지).
