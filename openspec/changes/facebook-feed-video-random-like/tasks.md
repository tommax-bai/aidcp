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

## 4. Live localized action/count regression

- [x] 4.1 Replace duplicated numeric guards with one shared localized reaction-control classifier used by strict card identity and exact like location/verification.
  <!-- aidcp-edge commit 94e93ad centralizes exact localized labels, same-action-bar comment proof, summary-toolbar exclusion, and fail-closed ambiguity handling for scan, action, and verification. -->
- [x] 4.2 Add regression fixtures for an exact neutral action containing numeric text, a distinct reaction-summary toolbar, supported locale variants, and structurally ambiguous failure.
  <!-- Regression coverage includes numeric `Thích`, a separate numeric reaction summary, zh/en/es/vi action variants, and summary-only ambiguity. -->
- [x] 4.3 Run focused Facebook tests, acceptance/full Edge tests, typecheck, and a bounded read-only Mi Xu probe from the isolated Edge source.
  <!-- Rebased validation: focused Facebook tests 74/74; acceptance 28/28; full suite 2141/2141; `npm run typecheck` exit 0. The bounded source probe launched exact AdsPower profile `k1es035u`, recovered the visible Sang Vlog video by round 4 with stable watch identity, author, caption, reaction count, and `isVideo=true`, performed no interaction, then returned the profile to `Inactive`. -->
- [x] 4.4 Integrate and push the Edge fix and control evidence serially, preserving the no-installer boundary.
  <!-- Pushed Edge 94e93ad to origin/master first, then pushed control contract/evidence bc66491 to origin/main. No Edge installer was built or installed. -->

## 5. Present-but-unreportable Feed fallback and locale convergence

- [x] 5.1 Extend the shared Facebook locale vocabulary and structural classifier for the verified Re Su verbose Vietnamese like/comment accessibility labels while preserving same-card uniqueness, summary exclusion, and fail-closed ambiguity.
  <!-- aidcp-edge commit 652996f recognizes the verified verbose Vietnamese controls, keeps same-action-bar/summary exclusion, and no longer treats the neutral visible word `Thích` as proof of an already-liked state. -->
- [x] 5.2 Add a protocol-level present-but-unreportable Feed list state after eight unsuccessful continuation rounds, gated by a fresh confirmed-home, physical-card, loading, login, consent, and checkpoint probe; do not reuse `empty`, `no_feed`, or `feed_exhausted` dishonestly.
  <!-- aidcp-edge commit 652996f adds `page.cards{cards:[],listKind:'feed',listState:'present_unreportable',documentGeneration}` only after the bounded continuation and a fresh safe home sample; loading/login/checkpoint/consent/unknown remain fail-closed. -->
- [x] 5.3 Make Cloud deduplicate that observation per startup/document generation and authorize exactly one Reels transition through the existing Edge command boundary; keep early reportable-card recovery and explicit-empty behavior unchanged.
  <!-- aidcp-cloud commit 2706e4c translates only the well-formed Facebook Feed observation into a distinct internal event and reuses the per-session fallback authorization latch plus existing `empty_feed_reels_fallback` command. -->
- [x] 5.4 Reuse normalized supported-locale vocabulary in the dedicated Reels reader while retaining separate active `noteId + videoKey`, geometry, exact-target, and post-action verification rules.
  <!-- aidcp-edge commit 652996f injects the shared CTA sources into Reels summary noise/like targeting/verification while preserving the dedicated active-video geometry and identity checks. -->
- [x] 5.5 Add Edge protocol/session/Feed/Reels fixtures and Cloud handler/dispatcher/integration tests for Re Su labels, eight-round fallback, blockers, early recovery, repeated observations, and exact transition identity.
  <!-- Focused final validation: Edge 11 targeted cases plus 9 home-state/consent cases passed; Cloud 6 handler/dispatcher cases passed; both protocol acceptance suites passed 23/23. -->
- [x] 5.6 Run focused tests, acceptance/full suites, and typechecks in isolated Edge and Cloud worktrees; update protocol documentation, validate OpenSpec strictly, and perform a bounded read-only Re Su acceptance before serial integration. Do not build an installer unless separately requested.
  <!-- Final isolated validation after rebase: Edge full 2174/2174 and typecheck passed; Cloud full 2785 passed, 8 gated skips, 0 failures, and typecheck passed; strict OpenSpec validation passed. Re Su AdsPower profile k1es5ky2 read-only acceptance confirmed canonical home, homeReady=true, physical cards, loading=false, no login/checkpoint/consent, and production scan cards=[]; no like/comment was executed and the browser was left open. The first optional input-scroll sample timed out, so acceptance was rerun with an explicit zero-scroll probe and a direct production-reader sample. No installer was built. -->
  <!-- Integrated and pushed serially: aidcp-edge 652996f to origin/master, aidcp-cloud 2706e4c to origin/master, then control protocol/evidence to origin/main while preserving unrelated control working-tree changes. Deployed Cloud 2706e4c to dev after target check and backup stamp 20260721-190607; verified active/NRestarts=0, listeners 8787/8090/8091, direct panel/client-auth and dev-Nginx health, PostgreSQL SELECT 1, Feishu WS onReady, and matching local/remote source hashes. -->
