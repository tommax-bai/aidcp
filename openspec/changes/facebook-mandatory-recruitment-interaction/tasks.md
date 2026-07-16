## 1. Structured persona rule

- [x] 1.1 Add typed `mandatory_interactions` soul fields plus strict loader validation for bounded rule count, unique ids, action/approval enums, comment requirements, and zero-config compatibility.
- [x] 1.2 Preserve valid mandatory rules in deterministic soul serialization and add loader/serializer/persona-store tests for valid, invalid, and round-trip cases.

## 2. Match once and propagate causally

- [x] 2.1 Make `ContentEvaluator` prioritize possible mandatory matches and make `ContentCuratorRole` confirm the full-detail match, reject unknown rule ids, and preserve global brand safety.
- [x] 2.2 Add typed mandatory context to `quality.pass`, reading, interaction, and comment payloads; propagate it end-to-end without shared-set ordering dependencies.

## 3. Deterministic like and comment behavior

- [x] 3.1 Make `InteractionAppraiserRole` deterministically emit mandatory like without ordinary LLM/session-budget filtering; make dispatcher skip cooldown only for the matched action while retaining `RiskController` and receipt-based accounting.
- [x] 3.2 Make `CommentAppraiser` bypass ordinary comment budget/daily pre-gate/cooldown/popularity/LLM only for matched mandatory comment rules.
- [x] 3.3 Make `CommentComposer` inject mandatory guidance, retry once on decline/empty/oversize, preserve no-template honesty, and propagate context through de-AI cleanup.
- [x] 3.4 Add explicit mandatory `auto_approve` handling to `CommentApprovalGate`: send a readable notification first, fail closed on notification failure, and keep ordinary/XHS review behavior unchanged.

## 4. Validation and delivery

- [x] 4.1 Add focused unit/integration tests for low-like forced like+comment, soft-gate bypass, hard-risk preservation, notification-first auto-approval, failure honesty, and no-rule zero regression.
- [x] 4.2 Run cloud acceptance tests, full tests, and typecheck; run `openspec validate facebook-mandatory-recruitment-interaction --strict`.
  <!-- Validation 2026-07-15: acceptance 54 passed / 1 gated skip; full 2222 passed / 3 skipped; typecheck passed; OpenSpec strict passed. -->
- [x] 4.3 Commit and push the cloud branch, land it to clean `aidcp-cloud/master`, re-run proportional validation, then deploy `dev` through the documented backup/restart/health sequence.
  <!-- Cloud 1848506: pushed feature branch, fast-forward landed origin/master, and the land helper re-ran acceptance/full/typecheck successfully. Deployed the clean committed snapshot to dev after scripts/deploy-target dev --check; backups: /opt/aidcp/cloud.bak.20260715-201622.tar.gz and /opt/aidcp/cloud/.env.bak.20260715-201622. aidcp-cloud active with NRestarts=0, ports 8787/8090 listening, /api/version 200, Feishu WS ready, PostgreSQL select 1 passed; unrelated isales units remained active. -->
- [x] 4.4 Update Tianxing Bai's dev persona to a structured Vietnam-recruitment `like + comment` auto-approved rule; verify API readback, live prompt visibility, service health, and honest runtime observation (or record pending real-post observation without claiming success).
  <!-- Dev persona audit 2026-07-15: Facebook account 61591753702668 (nickname Tianxing Bai) reads back mandatory rule vietnam-recruitment with like=true, comment=true, commentApproval=auto_approve. Content evaluator, curator, and interaction-appraiser prompt previews include the structured rule. Account-specific Feishu route resolves to the AI运营 chat and is present in bot membership. Edge logs confirm browse mode=on, but environment ads-k1ei3dbi is currently stopped by user_pause; no post-deploy public comment was triggered or claimed. The rule takes effect when the operator resumes the account. -->
- [x] 4.5 Defer mandatory `comment.appraised` to a microtask so same-post mandatory like reaches the edge queue before `commentInflight`; add stable `comment_inflight` suppression logging.
  <!-- Implemented in aidcp-cloud isolated worktree: mandatory comment pinning now enters on the next microtask, after the current interaction event has dispatched like; comment-inflight suppression logs action/note/account with a stable reason. -->
- [x] 4.6 Add an integrated regression with real note data and `actions=[like,comment]` that fails on the production ordering bug, proves like dispatch precedes the hold, and keeps hard-risk behavior unchanged.
  <!-- Regression first reproduced 0 like commands on the unpatched implementation, then passed after the fix. Focused mandatory/comment/dispatcher/platform suite: 65 passed; typecheck passed. -->
  <!-- Cloud 6a609ff: acceptance 54/54 passed; full 2291 passed / 5 environment-gated skips; typecheck passed. Fast-forward landed origin/master and deployed the clean git archive to dev after checksum dry-run showed only the two runtime files plus the regression test. Backup: /opt/aidcp/cloud.bak.20260716-182848.tar.gz and /opt/aidcp/cloud/.env.bak.20260716-182848. Health: active, NRestarts=0, 8787/8090 listening, /api/version 200, PostgreSQL select 1, Feishu WS ready. Tianxing Bai account 61591753702668 was restored through the hot-load API to vietnam-recruitment actions=[like,comment], comment_approval=auto_approve; no real post interaction was manually triggered or claimed. -->
