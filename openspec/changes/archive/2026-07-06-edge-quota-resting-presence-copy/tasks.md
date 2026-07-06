## 1. OpenSpec

- [x] 1.1 Create proposal, design, and delta spec for quota-rest presence copy.
- [x] 1.2 Validate the OpenSpec change with `openspec validate edge-quota-resting-presence-copy --strict`.

## 2. Edge Electron

- [x] 2.1 Implement quota-rest presence text in Electron renderer logic using existing `dailyUsage.windows`.
- [x] 2.2 Add focused Electron unit/renderer tests for current saturated windows, expired windows, and fallback stale activity.

## 3. Validation And Release

- [x] 3.1 Run focused edge Electron tests.
  <!-- aidcp-edge 0104c85: `npx tsx --test test/electron/ui-logic.test.ts test/electron/companion-ui.test.ts` passed 50/50. -->
- [x] 3.2 Run relevant edge validation before closeout.
  <!-- 2026-07-06: `openspec validate edge-quota-resting-presence-copy --strict` passed; aidcp-edge `npm run typecheck` passed; aidcp-edge `npm test` passed 624/624. -->
- [x] 3.3 Record implementation commit, validation, and release/publish notes.
  <!-- pushed: aidcp-edge 0104c85 to origin/master. publish: rebuilt Windows installer from aidcp-edge master 0104c85 via `npm run electron:build:win`; rebuilt macOS dmg files via `npm run electron:build:mac`; uploaded the three console-referenced 0.2.4 installers to ECS `/opt/aidcp/downloads/` after backing up previous same-name files (`AIDCP Setup 0.2.4.exe.bak-20260706-110236`, `AIDCP-0.2.4.dmg.bak-20260706-110723`, `AIDCP-0.2.4-arm64.dmg.bak-20260706-110723`). Verified HTTP 200 via `127.0.0.1:8088/downloads/...`: Windows exe length 78563149 sha256 b06e55e4a478157ed5acbf15fde6a99c00a9d4de5d3571dd7e174cab55e63cca; mac Intel dmg length 101461118 sha256 89809505164c551bbba84085d6fd281628e457cf1fc463d290b8404773a52fa6; mac Apple Silicon dmg length 95430189 sha256 e8babaf64605a7173ae61a543c7bd34ad3cd38aff8fb912d55d78542c7a8c207. Console download config already points to these filenames, so no console rebuild/deploy was needed. -->
