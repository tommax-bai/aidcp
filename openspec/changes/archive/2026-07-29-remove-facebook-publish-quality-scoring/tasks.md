## 1. Platform-Aware Quality Contract

- [x] 1.1 Extend `QualityReport` and `AssembledContent` with truthful `scored | not_applicable` status and nullable quality score; update Cloud-only record types without adding a database column or protocol field.
- [x] 1.2 Make `QualityScorer` read the trigger platform and return `null + not_applicable` for Facebook with zero prompt construction / LLM calls; preserve the existing non-Facebook scorer and fallback formula byte-for-byte.
- [x] 1.3 Keep `ContentAssembler` a pure single-writer mapper that passes quality applicability through without numeric fallback.
- [x] 1.4 Make `ApprovalGatekeeper` return deterministic `manual_review` for Facebook with zero LLM calls; preserve existing non-Facebook prompt, thresholds, fallback, and fail closed if a scored platform lacks a score.
- [x] 1.5 Keep `PublishExecutor` on the existing `gateDecision + titleSelection + publishMetadata` admission boundary and stage Facebook candidates for human approval without inspecting or inventing a quality score.
<!-- Cloud worktree remove-facebook-publish-quality-scoring: platform policy is explicit while the existing role topology and approval boundary remain intact. -->

## 2. Regression Coverage

- [x] 2.1 Add focused QualityScorer tests for Facebook zero-call/not-applicable and Xiaohongshu scored/fallback behavior.
- [x] 2.2 Add focused ApprovalGatekeeper tests for Facebook zero-call/manual-review, non-Facebook unchanged behavior, and non-Facebook missing-score failure safety.
- [x] 2.3 Add assembler/executor or orchestrator coverage proving a valid Facebook candidate reaches `pending_approval` without quality retry and without a fabricated score.
- [x] 2.4 Run Cloud publish-focused tests, `test:acceptance`, full `npm test`, and `npm run typecheck`; run `openspec validate remove-facebook-publish-quality-scoring --strict`.
<!-- Validation: focused 47/47; acceptance 123/123; full Cloud 3406 passed, 11 skipped, 0 failed; typecheck passed; OpenSpec strict passed. -->

## 3. Integration and DEV

- [x] 3.1 Commit in the isolated Cloud worktree, integrate with the ff-only helper, push Cloud master, and record the owning commit plus validation evidence here.
<!-- aidcp-cloud cc55c52; land-change rebased onto origin/master, reran acceptance/full/typecheck, ff-pushed master, and synchronized the clean canonical checkout. -->
- [x] 3.2 Commit and push the OpenSpec artifacts in control main.
<!-- aidcp 6e3598f pushed the validated proposal/design/spec/tasks artifacts to origin/main; this deployment closeout is a follow-up main commit. -->
- [x] 3.3 Deploy the clean Cloud master to DEV after backup and migration-status checks; verify source hash, service/listeners, schema gates, automation writer lock, Feishu connection, PostgreSQL, and internal/public health.
<!-- DEV 2026-07-26 16:14 CST: clean aidcp-cloud master cc55c52; backups /opt/aidcp/backups/cloud.20260726-161420.tar.gz and cloud.env.20260726-161420; all three owner ledgers checksum-clean with 0 pending; changed-source digest 58447be14f6f363505a9c9606568edbe7b8835616c8dbb1fedcdde62b22a7a29 matched. aidcp-cloud active/NRestarts=0; 8787/8090/8091/8088 listening; local/public health 200; three PostgreSQL SELECT 1 passed; enforce schema gates, dev writer lock, and Feishu WS onReady passed; four unrelated isales services remained active. No package change, migration, or npm install. -->
- [x] 3.4 Verify the deployed runtime exposes the Facebook `not_applicable → manual_review` branch and no quality-model call sites on that branch; do not approve or submit a real Facebook post as part of this change.
<!-- Deployed-source Facebook tests passed for QualityScorer zero-call/not_applicable, Gatekeeper zero-call/manual_review, and full pipeline pending_approval with null score (4 selected pass, 0 fail). No approval or real Facebook submit was performed. -->
