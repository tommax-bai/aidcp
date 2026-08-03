## 1. Protocol and command contract

- [x] 1.1 Add the optional Facebook `targetSurface` field to both TypeScript `page.scroll` payloads, Native strict decoding, command mapping fixtures, and `docs/protocol.md`.
- [x] 1.2 Add focused protocol/strict-decoder tests proving `resume_redrive` accepts the target and unrelated/legacy scroll commands remain compatible.

## 2. Edge target reconciliation

- [x] 2.1 Route Facebook `resume_redrive` through one target-aware Native executor that probes the live page, reports an active Reel in place, enters Reels when off-target, and restores Feed to Facebook home before scrolling.
- [x] 2.2 Synchronize the embedded Facebook router and add focused Rust/Edge tests for already-on-target, off-target, missing target, and honest no-card outcomes.

## 3. Cloud unified redrive

- [x] 3.1 Centralize active browse continuation in RoleDispatcher so session start, auto-resume, Reels primary/fallback, and post-task continuation emit `page.scroll{reason:'resume_redrive',targetSurface}` through existing quota/pause/risk gates.
- [x] 3.2 Remove sticky `reelsFallbackState='confirmed'`; retain only bounded transient attempt/recovery data and update focused Reels dispatcher tests.

## 4. Workflow-final resume

- [x] 4.1 Expose final page-lease release acknowledgement and `edgeId` from consumption join/comment executors without changing platform outcome accounting.
- [x] 4.2 Accumulate page-task completion across recursive consumption actions and invoke the exact account/Edge runtime redrive port once after the root chain terminates with an acknowledged final release.
- [x] 4.3 Add focused tests for success, failure, `submitted_unknown`, missing release acknowledgement, intermediate releases, and chained-action single redrive.

## 5. Validation and delivery record

- [x] 5.1 Run focused Cloud tests, Cloud typecheck, focused Edge TypeScript/Rust tests, Edge typecheck, and protocol drift/safety checks.
- [x] 5.2 Run `openspec validate unify-facebook-post-task-browse-resume --strict` and record repository commits, validation evidence, deployment exclusion, and deviations in this task file.

<!--
Delivery record (2026-08-03):
- aidcp-cloud: 2923aab (rebased onto origin/master 622a1af)
- aidcp-edge: 87b8ac6 (rebased onto origin/master e6cd4bc)
- Cloud validation: focused redrive/lease/coordinator suites 56 passed; acceptance, full test suite, and typecheck passed on the rebased head.
- Edge validation: focused protocol/router/diagnostics suites 120 passed; acceptance passed; full suite 3066 passed and 1 existing gated test skipped; typecheck passed.
- Native validation: pinned 1.97.1 gate passed fmt, clippy with warnings denied, and all Rust tests; strict target decoding and active-Reel no-extra-navigation coverage passed.
- Control validation: openspec validate unify-facebook-post-task-browse-resume --strict passed; git diff --check passed in all three repositories.
- Scope refinements: Feed target is explicitly Facebook home after temporary group/search navigation; final redrive is targeted to the Edge that acknowledged the final page-lease release. No behavior deviation from the proposal.
- Excluded by scope: Edge packaging/installation, Cloud deployment, and real-account acceptance.
-->
