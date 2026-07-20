## 1. Cloud decision plumbing

- [x] 1.1 Preserve the optional `listKind` field from `page.cards` on the internal `page.cards.arrived` event without changing the wire protocol.
- [x] 1.2 Add canonical Reel validation and a session-local normalized set that makes each active Reel decision idempotent across duplicate reports.
- [x] 1.3 Implement the strict `< 0.25` ordinary like draw at the active-Reel presentation boundary and route hits through existing budget, risk, cooldown, note-scoped dispatch, retry, and receipt paths.
- [x] 1.4 Make InteractionAppraiserRole skip the later ordinary LLM decision for externally handled Reels while keeping mandatory likes ahead of the skip.

## 2. Tests and validation

- [x] 2.1 Add handler coverage proving `listKind:'reels'` reaches the internal event and old payloads remain compatible.
- [x] 2.2 Add focused policy tests for hit, exact-threshold miss, duplicate idempotency, invalid batch/platform fail-closed behavior, safety-gate blocking, and session reset.
- [x] 2.3 Add appraiser tests proving ordinary handled Reels do not call the LLM and mandatory Reel likes still bypass the ordinary skip.
- [x] 2.4 Run focused tests, Cloud acceptance tests, full Cloud tests, and `npm run typecheck` with concise retained evidence.
  <!-- aidcp-cloud: focused 39/39 passed; acceptance 63/63 passed; full 2722 passed, 0 failed, 8 skipped/gated; typecheck passed. -->

## 3. Integration and runtime closeout

- [x] 3.1 Record Cloud repository, commit SHA, validation results, and deviations in this checklist; run `openspec validate facebook-reels-random-like --strict`.
  <!-- aidcp-cloud commit 759c178; validation: focused 39/39, acceptance 63/63, full 2722 passed/0 failed/8 skipped, typecheck passed; OpenSpec strict passed; deviation: none. -->
- [x] 3.2 Commit and push the control and Cloud changes, integrate Cloud to the latest eligible `master`, and preserve unrelated work.
  <!-- aidcp-cloud 759c178 fast-forwarded and pushed to origin/master; canonical master is clean and matches origin/master. Control artifacts are committed and pushed immediately after this final record. -->
- [x] 3.3 Read the deployment guide, pass `scripts/deploy-target dev --check`, deploy only the Cloud runtime change to `dev`, and verify the documented service, listener, health, Feishu, and PostgreSQL checks.
  <!-- Deployed aidcp-cloud 759c178 runtime delta to dev 121.89.85.150 from the clean canonical master. Backups: /opt/aidcp/cloud.bak.20260720-212223.tar.gz and /opt/aidcp/cloud/.env.bak.20260720-212223. Exactly four runtime source files were synced after local/remote SHA-256 matched; no package or migration change. ECS typecheck passed before restart. Post-restart: aidcp-cloud.service active, NRestarts=0, ports 8787/8090/8091 listening, panel API healthy, client-auth fail-closed with 401 without credentials, PostgreSQL select 1 passed, Feishu WSClient onReady, critical startup error scan zero, and all four isales units remained active. No real Facebook action was manually triggered or claimed. -->
