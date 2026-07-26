## 1. Contract and evidence

- [x] 1.1 Reproduce the customer failures from dev logs and distinguish route mismatch, customer scope, draft lifecycle, and platform send capability.
  <!-- evidence=dev returned 404 for documented PUT /replies/:jobId/draft and 403 for regenerate while environment ownership and list/detail reads were valid -->
- [x] 1.2 Validate this OpenSpec change strictly before implementation.
  <!-- validation=openspec validate wechat-draft-action-contract-alignment --strict passed -->

## 2. Cloud contract alignment

- [x] 2.1 Match the documented `/replies/:jobId/draft` route and reject the undocumented short form.
  <!-- evidence=customer API regression accepts PUT /replies/job-a/draft and returns 404 for PUT /replies/job-a -->
- [x] 2.2 Allow generate, edit, and approve under active identified auth without requiring platform send capability.
  <!-- evidence=workflow tests cover generate, edit and approve with commentsReply=false and dmSendText=false while inactive auth still fails before mutation -->
- [x] 2.3 Preserve fail-closed capability checks for real send and automatic dispatch.
  <!-- evidence=send orchestrator retains both auto-queue and dispatch capability gates; focused test proves commentsReply=false creates no attempt and emits no push -->
- [x] 2.4 Add focused Cloud regression tests for the route and admission boundaries.
  <!-- evidence=Cloud focused interaction suite passed 22/22 -->

## 3. Edge client clarity

- [x] 3.1 Replace the misleading customer-login permission copy with platform-capability wording.
  <!-- evidence=INTERACTION_PERMISSION_DENIED now identifies an unconfirmed platform channel capability instead of customer login scope -->
- [x] 3.2 Add regression coverage for the canonical draft URL, error copy, and send-only capability gate.
  <!-- evidence=Edge focused IPC and interaction workspace suite passed 43/43 -->

## 4. Validation and delivery

- [x] 4.1 Run focused tests in Cloud and Edge worktrees.
  <!-- evidence=Cloud focused 22/22; Edge focused 43/43 -->
- [x] 4.2 Run Cloud and Edge acceptance, full tests, and typecheck.
  <!-- evidence=Cloud acceptance 57/57, explicit Git Bash full run 1548 passed + 8 gated skips, typecheck passed; Edge acceptance 25/25, full 1814/1814, typecheck passed -->
- [x] 4.3 Rebase, fast-forward integrate, and push Cloud/Edge default branches without force; do not build an installer.
  <!-- evidence=Cloud f6f1920 and Edge 1469621 fast-forwarded and pushed to origin/master by land-change; no installer command was run -->
- [x] 4.4 Deploy Cloud to dev and verify service health, listeners, database access, and Feishu connectivity.
  <!-- evidence=dev backup cloud.bak.20260718-224437.tar.gz + .env.bak.20260718-224437; deployed f6f1920; service active with NRestarts=0; 8787/8090/8091 listening; panel/customer health ok; PostgreSQL select 1; Feishu WS ready; isales services remained active -->
- [x] 4.5 Record validation and deployment evidence, validate OpenSpec strictly, then commit and push control main.
  <!-- validation=all evidence recorded above; openspec validate wechat-draft-action-contract-alignment --strict passed before control commit -->
