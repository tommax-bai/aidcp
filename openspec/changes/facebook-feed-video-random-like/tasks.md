## 1. Edge: strict Feed-video identity and interaction parity

- [x] 1.1 Add one shared lightweight-video card identity primitive with explicit-link/data-video-id agreement, synthetic `watch?v=` note identity, and fail-closed ambiguity handling.
- [x] 1.2 Merge strict lightweight videos into Feed discovery, require primary viewport presentation, and reuse the same card identity for inline reading, like/comment targeting, and post-action verification.
- [x] 1.3 Add exact Vietnamese like/unlike/comment controls and keep numeric reaction summaries separate from actionable controls.
- [x] 1.4 Add focused fixtures and tests for the observed Mi Xu and Tianxing Bai layouts, adjacent/mismatched cards, embedded Reels rails, viewport selection, and exact-target action verification.
  <!-- aidcp-edge commit 126d5a1; integrated and pushed to origin/master after land-change reran acceptance, 2096/2096 full tests, and typecheck. -->

## 2. Cloud: viewed-video accounting and 25 percent policy

- [x] 2.1 Record one existing view interaction for each unique presented ordinary-Feed video and deduplicate a later detail read in the same session.
- [x] 2.2 Generalize the existing presented-video policy to make one session-idempotent `random < 0.25` Feed-video like decision with non-empty-caption and bounded obvious-risk guards.
- [x] 2.3 Bypass the ordinary LLM appraiser after the Feed-video decision while preserving mandatory-interaction precedence and all existing gates and confirmed-receipt accounting.
- [x] 2.4 Add focused handler, dispatcher, policy, appraiser-precedence, continuation, and duplicate-presentation tests without changing the protocol shape.
  <!-- aidcp-cloud commit bf4fb93; integrated and pushed to origin/master after land-change reran acceptance/full tests and typecheck with exit 0. -->

## 3. Validation, integration, and development runtime

- [x] 3.1 Run Edge focused Facebook tests, required acceptance/full suites, and typecheck in the isolated Edge worktree.
  <!-- aidcp-edge validation: focused Facebook identity/feed/like/CTA 72/72; acceptance 28/28; full suite exit 0; `npm run typecheck` exit 0. -->
- [x] 3.2 Run Cloud focused tests, required acceptance/full suites, and typecheck in the isolated Cloud worktree.
  <!-- aidcp-cloud validation: focused policy/handler/dispatcher/appraiser 44/44; acceptance 64/64; full suite exit 0; `npm run typecheck` exit 0. -->
- [x] 3.3 Record repository commits, validation evidence, deviations, and strict OpenSpec validation in this task list.
  <!-- `openspec validate facebook-feed-video-random-like --strict` passed before implementation and again after the implementation evidence update. -->
- [x] 3.4 Integrate and push Edge and Cloud default branches serially without overwriting concurrent work.
  <!-- land-change --yes fast-forwarded clean canonical checkouts and pushed origin/master serially: Edge 126d5a1, then Cloud bf4fb93. -->
- [x] 3.5 Deploy the Cloud runtime change to `dev` after target checks, backup, and clean-default verification; verify service, listener, health, Feishu, and PostgreSQL evidence.
  <!-- Dev target check passed; backed up `/opt/aidcp/cloud` and `.env`, synced clean origin/master bf4fb93, restarted only `aidcp-cloud.service`, and verified active/NRestarts=0, listeners 8787/8090/8091, direct and Nginx health, PostgreSQL, source hashes, and unchanged isales services. Feishu WS was explicitly unset, so no Feishu ready/send probe applied. -->
- [x] 3.6 Re-run bounded live probes on Mi Xu and Tianxing Bai when the installed Edge/runtime boundary permits, and report any installer or session limitation honestly.
  <!-- Pre-implementation bounded probes confirmed the two observed real Feed-video layouts and exact neutral-to-liked controls. A post-implementation source probe was not started: the active installed client is 0.3.22 while source is 0.3.24, it owns AdsPower port 50325, and starting a second source client would risk two controllers sharing the same environments. No installer was built or installed because packaging was outside this change's authorized scope. -->
