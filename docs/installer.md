# 인스톨러 / 배포 (M6 T37, PLAN §7)

판매용 바이너리는 **Tauri 번들러**로 생성한다(Electron 대비 품질/용량 우위). 모델 가중치는
앱에 미포함 — 최초 실행 시 다운로더가 받는다(배포 라이선스 리스크 회피, §7).

## 빌드
```bash
# 프론트 정적 빌드 + Rust 릴리즈 + OS 인스톨러 번들
pnpm --filter @conode/studio build          # = tauri build

# 산출물: apps/studio/src-tauri/target/release/bundle/
#   macOS   : dmg/ (conode_x.y.z_aarch64.dmg), macos/ (conode.app)
#   Windows : msi/ · nsis/
#   Linux   : deb/ · appimage/
```
번들 설정은 `apps/studio/src-tauri/tauri.conf.json` `bundle` (category, copyright,
아이콘, macOS.minimumSystemVersion 11.0).

## 코드사이닝 / 공증 (배포 전 필수)
- **macOS**: Apple Developer ID 서명 + notarization.
  `tauri.conf.json > bundle.macOS.signingIdentity`, `APPLE_ID`/`APPLE_PASSWORD` 환경변수.
- **Windows**: Authenticode 인증서. `bundle.windows.certificateThumbprint`.
- 카메라/마이크 권한(macOS TCC): `Info.plist` 에 `NSCameraUsageDescription`,
  `NSMicrophoneUsageDescription` 추가 필요(제스처/카메라·오디오 노드).

## 엔진 사이드카
Python 엔진은 `.venv` + CUDA(4090) 의존이라 앱 번들에 포함하지 않는다. 배포 옵션:
1. 엔진을 별도 인스톨러/도커로 배포(원격 엔진, 랜더 머신 분리 — §1.1 확장).
2. 로컬 번들 시 PyInstaller 로 엔진을 사이드카 바이너리화 후 Tauri `externalBin` 등록.

## 라이선스 통합 (§7)
- 발급자가 Ed25519 개인키로 라이선스 서명(`python -m conode_engine.licensing issue`).
- 앱은 공개키를 임베드하고 **오프라인 로컬 검증**(Tauri Rust 사이드에서 `ed25519-dalek`
  crate 로 동일 포맷 검증; 개발 검증은 `conode_engine.licensing.verify_license`).
- 티어: Personal(1석) / Pro(2석 + 상업공연 + NDI/Spout 출력) / Edu(할인).

## 릴리즈 체크리스트
- [ ] 모델 라이선스 확인 완료 (LCM 채택 — 상업 OK, §11)
- [ ] 카메라/마이크 usage 문자열 + 코드사이닝/공증
- [ ] `pnpm build` 인스톨러 생성 + 실기 설치 테스트
- [ ] 4090 타깃에서 StreamDiffusion+TRT 25fps 검증(M2), Syphon/Spout/NDI Out 검증(M5)
- [ ] 프리셋 팩(`presets/`) 동봉, 버전/체인지로그
