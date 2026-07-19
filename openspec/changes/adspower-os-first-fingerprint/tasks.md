## 1. Contract

- [x] 1.1 Add OpenSpec deltas for OS-family creation and AdsPower-first fingerprint generation.
- [x] 1.2 Validate the change with `openspec validate adspower-os-first-fingerprint --strict`.
  <!-- 2026-07-19: strict validation passed. -->

## 2. Edge implementation

- [x] 2.1 Replace fixed machine templates with OS-family options while preserving backwards-compatible template keys where needed.
- [x] 2.2 Build minimal AdsPower-first `fingerprint_config` for `user/create`, keeping OS, proxy-safe WebRTC, timezone/location, language, and noise policy constraints.
- [x] 2.3 Update single and Facebook batch creation to pass OS-family keys and avoid fixed template selection.
- [x] 2.4 Update renderer labels, messages, and payload names from machine template to OS family.

## 3. Validation

- [x] 3.1 Update focused unit/smoke tests for fingerprint config, creation flow, batch planning, main IPC, and renderer behavior.
- [x] 3.2 Run focused `aidcp-edge` Electron tests for touched behavior.
- [x] 3.3 Run proportionate typecheck/full validation if the focused suite shows broad type or contract risk.
  <!-- 2026-07-19: aidcp-edge e648b67; focused Electron suite 109/109 passed; acceptance 25 passed with the gated real-device E2E skipped; full suite 1828/1828 passed; npm run typecheck passed. Desktop packaging/release was not run because no installer release was requested. -->
