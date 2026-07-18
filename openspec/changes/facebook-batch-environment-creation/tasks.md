## 1. Batch planning and validation

- [x] 1.1 Add a pure Facebook batch-planning module that parses multiline proxies, reuses proxy validation, assigns proxies by modulo round-robin, and selects one complete legal template per account.
  <!-- repo: aidcp-edge; commit: 4e5d381; validation: pure module exercised by task 1.2; deployment: not applicable; deviations: none -->
- [x] 1.2 Add focused unit tests for supported proxy formats, safe line-number errors, no-proxy behavior, round-robin assignment, random template selection, and invalid batch rejection.
  <!-- repo: aidcp-edge; commit: 4e5d381; validation: `npx tsx --test test/electron/facebook-batch-create.test.ts` PASS 6/6; deployment: not applicable; deviations: none -->

## 2. Main-process creation orchestration

- [x] 2.1 Extend the `ads:createEnv` IPC contract with an explicit Facebook-only batch mode and reject non-Facebook or malformed batch requests before any AdsPower write.
  <!-- repo: aidcp-edge; commit: 4e5d381; validation: main contract and pure planning tests PASS; deployment: not applicable; deviations: none -->
- [x] 2.2 Enforce remaining account capacity for the full batch, then execute the plan sequentially through the existing creation-intent, AdsPower, assignment, and roster-confirmation chain.
  <!-- repo: aidcp-edge; commit: 4e5d381; validation: capacity unit test + main contract assertions PASS; deployment: not applicable; deviations: none -->
- [x] 2.3 Return non-sensitive full-success and partial-failure receipts with accurate created counts, item summaries, failure position, and distinct assignment/roster state.
  <!-- repo: aidcp-edge; commit: 4e5d381; validation: partial receipt unit test + renderer partial-failure test PASS; deployment: not applicable; deviations: none -->

## 3. Renderer batch experience

- [x] 3.1 Add a Facebook-only single/batch selector; hide template selection in batch mode and add multiline proxy input with one shared proxy-type selector and explicit format/round-robin guidance.
  <!-- repo: aidcp-edge; commit: 4e5d381; validation: renderer smoke visibility assertions PASS; deployment: not applicable; deviations: none -->
- [x] 3.2 Submit explicit batch payloads, validate required visible inputs before IPC, disable creation while in flight, and preserve existing single-create behavior for all platforms.
  <!-- repo: aidcp-edge; commit: 4e5d381; validation: renderer smoke payload assertions and existing single-create cases PASS; deployment: not applicable; deviations: none -->
- [x] 3.3 Render honest success/partial-failure messages, refresh created environments, clear one-time inputs only after full success, and add renderer/style regression coverage for visibility and secret-safe payload/results.
  <!-- repo: aidcp-edge; commit: 4e5d381; validation: combined batch/main/renderer focused run PASS 68/68; deployment: not applicable; deviations: none -->

## 4. Validation and delivery

- [x] 4.1 Run focused Electron tests for batch planning, renderer behavior, account import, proxy normalization, creation flow/service, and write API.
  <!-- repo: aidcp-edge; commit: 4e5d381; validation: focused Electron suite PASS 181/181; deployment: not applicable; deviations: added main contract and companion UI coverage -->
- [x] 4.2 Run the owning repo's full required validation (`npm test`, `npm run typecheck`, and acceptance/build where proportionate) and resolve failures without weakening safety assertions.
  <!-- repo: aidcp-edge; commit: 4e5d381; validation: focused 181/181, `npm test` 1740/1740, acceptance 24/24, typecheck PASS, build PASS; deployment: not applicable; deviations: gated real-machine E2E was not enabled and no installer was built -->
- [x] 4.3 Update this checklist with repo commit SHAs and validation evidence, run `openspec validate facebook-batch-environment-creation --strict`, then integrate and push the clean default branches without packaging an Edge installer.
  <!-- repos: aidcp-edge 4e5d381, aidcp 66f5e9e; validation: strict OpenSpec PASS after rebase, canonical Edge focused 68/68 + typecheck PASS; delivery: both default branches fast-forwarded and pushed; deployment: no Edge installer/package by scope; deviations: real AdsPower account creation not executed because it would create external environments with real credentials/proxies -->
