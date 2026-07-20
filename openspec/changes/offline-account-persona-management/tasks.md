## 1. Cloud shared persona service

- [x] 1.1 Add a shared account-persona application service for authoritative read summaries, bounded/idempotent generation, validated persistence, and first-bind onboarding.
- [x] 1.2 Route the existing WebSocket `persona.generate` / `persona.persist` handlers through the shared service without changing protocol shapes or legacy behavior.
- [x] 1.3 Add focused service tests covering configured/missing reads, summary projection, idempotency, platform/language validation, failed-generation eviction, persistence failures, and first-bind receipts.

## 2. Customer-auth offline persona API

- [x] 2.1 Add strict env-scoped GET persona, POST draft, and PUT persona routes that re-resolve ownership/binding on every request and never expose `accountId`.
- [x] 2.2 Wire the shared persona service into customer-auth startup while preserving fail-closed behavior when dependencies are unavailable.
- [x] 2.3 Add customer-auth tests for stopped/bound environments, missing persona honesty, binding/ownership failures, body/header allowlists, response DTO bounds, idempotency, and validated writes.

## 3. Edge offline persona bridge and UI

- [x] 3.1 Replace the new-client persona UI transport with named customer-auth IPC operations, resolve local env IDs to authoritative env keys, and give only draft generation the bounded long timeout.
- [x] 3.2 Add the offline persona read state and concise configured summary card with folded full definition, honest loading/error/binding-unknown states, and an explicit adjust entry.
- [x] 3.3 Reuse the existing selection/draft/confirmation flow without the engine-online gate, best-effort prefill current options, preserve per-environment isolation, and update UI only from Cloud receipts.
- [x] 3.4 Add Edge main/renderer regressions for stopped-environment read/generate/save, strict IPC scope, pending/rollback feedback, multi-environment late replies, and legacy bulk-persona behavior.

## 4. Validation and delivery

- [x] 4.1 Run Cloud focused tests, acceptance, full tests, and typecheck; run Edge focused tests, acceptance, full tests, and typecheck.
  <!-- Cloud: focused 66/66; acceptance 59/59; full 2611 passed, 8 gated skips; typecheck passed. Edge: persona/fleet focused 57/57 plus IPC/renderer regressions; acceptance 25/25; full 1927/1927; typecheck passed. -->
- [x] 4.2 Run `openspec validate offline-account-persona-management --strict` and record repo commits, validation results, deployment, and any honest deviations in this file.
  <!-- Implementation commits: aidcp-cloud 4a91973; aidcp-edge 73f42a6. OpenSpec strict validation passed. Control artifacts are committed with this evidence update. Deployment and live verification are recorded below after completion. -->
- [ ] 4.3 Rebase and fast-forward integrate Cloud then Edge to current default branches, push both defaults, and deploy Cloud from the clean canonical checkout to `dev` after `scripts/deploy-target dev --check`.
- [ ] 4.4 Verify the named dev service/listener/health path and the offline persona API boundary without performing real-account platform writes; leave Edge packaging explicitly not run.
