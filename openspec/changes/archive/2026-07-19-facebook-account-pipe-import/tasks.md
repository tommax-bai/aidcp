## 1. Parser contract and implementation

- [x] 1.1 Add focused account-import tests for the six-field pipe format, mixed legacy/pipe batches, embedded Cookie pipes, UID mismatch, safe errors, and omission of token/timestamp/`fakey`.
  <!-- repo: aidcp-edge; commit: 9b44d35; validation: account-import tests PASS 8/8; deviations: none -->
- [x] 1.2 Extend the shared Facebook account parser with deterministic format detection, two-ended pipe parsing, required-field checks, and readable `c_user` identity validation while preserving the legacy format.
  <!-- repo: aidcp-edge; commit: 9b44d35; validation: focused Facebook/Electron suite PASS 98/98; deviations: none -->

## 2. Client guidance and regressions

- [x] 2.1 Update the create-environment account input guidance to show both supported formats without displaying real credentials.
  <!-- repo: aidcp-edge; commit: 9b44d35; validation: renderer smoke coverage PASS; deviations: none -->
- [x] 2.2 Add renderer regression coverage proving the guidance applies to the shared single/batch input and raw credentials remain one-time IPC data only.
  <!-- repo: aidcp-edge; commit: 9b44d35; validation: renderer/main/write focused coverage PASS; deviations: access token is structurally absent from parsed accountImport -->

## 3. Validation and delivery

- [x] 3.1 Run focused Facebook account-import, batch-create, renderer, main-contract, and AdsPower write tests plus typecheck.
  <!-- repo: aidcp-edge; commit: 9b44d35; validation: focused PASS 98/98; typecheck PASS; deviations: none -->
- [x] 3.2 Run the owning Edge repository's full required test/build validation and strict OpenSpec validation, recording commit SHAs and any honest validation boundary.
  <!-- repo: aidcp-edge; commit: 9b44d35; validation: npm test PASS 1831/1831; acceptance PASS 25/25; typecheck PASS; build PASS; strict OpenSpec PASS; deviations: gated real-machine E2E not enabled, no real Facebook/AdsPower creation and no installer build -->
- [x] 3.3 Integrate and push the clean default branches via the repository helpers without packaging an installer or executing a real Facebook/AdsPower creation.
  <!-- repos: aidcp-edge 9b44d35, aidcp 46fcd68; validation: land-change acceptance 25/25, full 1831/1831, typecheck PASS; delivery: edge/master and aidcp/main pushed; deployment: no installer/package by scope; deviations: none -->
