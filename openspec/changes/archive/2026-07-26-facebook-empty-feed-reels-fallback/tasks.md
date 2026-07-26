## 1. Protocol and empty-home contract

- [x] 1.1 Add backward-compatible `page.cards` list-kind/list-state fields to Edge, Cloud, event translation, and `docs/protocol.md` without changing message types or the `feed/detail` Surface union.
  <!-- aidcp-edge + aidcp-cloud protocol mirrors add only optional listKind/listState; AC-PROTO remains 91 messages and Surface remains feed|detail. -->
- [x] 1.2 Split Facebook home readiness from card/container presence and implement generation-bound, minimum-age, three-sample explicit empty-state confirmation with loading/blocker/final rechecks.
  <!-- aidcp-edge feed-reader.ts: homeReady is independent; confirmHomeEmpty binds URL+timeOrigin, age>=8s, 3 samples, final fresh recheck. -->
- [x] 1.3 Add focused Edge tests for normal cards, slow loading, unknown zero-card layout, explicit empty home, late card arrival, generation reset, and non-home/login/checkpoint/consent/captcha rejection.
  <!-- Final focused Edge suite passed 71/71, including jsdom Vietnamese explicit-empty and zero-card-not-exhausted cases; existing overlay tests cover consent/captcha front doors. -->

## 2. Cloud-authorized fallback

- [x] 2.1 Translate only Facebook `feed/empty` observations into an internal confirmed-empty event and have RoleDispatcher send exactly one existing scroll command with the dedicated fallback reason per empty generation.
  <!-- aidcp-cloud handler + RoleDispatcher: exact Facebook/feed/empty/zero-card gate; one authorization per active session. -->
- [x] 2.2 Add Cloud integration/protocol tests proving explicit authorization, idempotence, old-payload compatibility, and no fallback for unconfirmed/blocked/other-platform states.
  <!-- New handler/dispatcher tests and AC-PROTO-20 passed; malformed, reels, xhs and inactive cases do not authorize. -->

## 3. Facebook Reels Edge execution

- [x] 3.1 Implement canonical Reel identity, active-video selection, bottom-left summary extraction, and video `page.cards`/`note.detail` projection.
  <!-- aidcp-edge reels-reader.ts + FacebookBrowseSession Reels card/detail projection. -->
- [x] 3.2 Route the dedicated fallback command into Reels mode and route feed-surface open/read commands by the fresh current list mode.
  <!-- Only page.scroll reason=empty_feed_reels_fallback enters mode; normal feed commands cannot. -->
- [x] 3.3 Implement a fail-closed one-click Reels like executor with active-note matching, unique structural target, same-Reel selected-state proof, and DOM-derived receipt observation.
  <!-- Trusted CDP click once; selected/unlike witness on same canonical route is required; rounded count is observation only. -->
- [x] 3.4 Implement Reels next-card navigation through the unique far-right lower control with route/video-change validation and deduplication.
  <!-- Global lower navigation target only; wheel/in-video controls unused; canonical route/video identity must change. -->
- [x] 3.5 Add fixture/unit tests for preloaded videos, summary filtering/expansion drift, stale or ambiguous likes, selected-state verification, wrong controls, unchanged navigation, and successful next card.
  <!-- Reels focused tests plus session routing test passed; stale/ambiguous writes perform zero clicks. -->

## 4. Validation and delivery

- [x] 4.1 Run Edge focused tests, required acceptance/full tests, and typecheck; record concise evidence and deviations.
  <!-- Final focused 71/71; post-rebase acceptance 26/26 and full npm test 1980/1980; npm run typecheck passed. No installer/package built. -->
- [x] 4.2 Run Cloud focused integration/protocol/risk tests, required full tests, and typecheck; record concise evidence and confirm RiskController remains the only final risk writer.
  <!-- Focused fallback/protocol 36/36; post-rebase acceptance 60/60; full npm test 2666 total, 2658 passed, 8 gated/skipped, 0 failed; typecheck passed. Like receipt still enters the existing handler/RiskController path. -->
- [x] 4.3 Run strict OpenSpec validation and protocol-drift checks, then commit and push isolated Edge, Cloud, and control changes.
  <!-- Strict OpenSpec and the exact PageCards protocol-block drift check passed. Isolated branches were pushed before rebase. Final default commits: aidcp-edge 7644caac00f2426a008248e79864104177906b1f; aidcp-cloud 1951715a6e907e2b2b74f26423376efb443ad8de; control artifact 9ab215c1575e828b93afaddf6fbcec5b7e540a24. -->
- [x] 4.4 Integrate clean default branches serially and deploy Cloud to `dev` after `deploy-target dev --check`; verify service, listener, health, logs, Feishu, and PostgreSQL without touching unrelated services.
  <!-- Edge and Cloud were rebased on the latest defaults, revalidated, and fast-forward pushed without force. dev target 121.89.85.150 passed preflight; backups cloud.bak.20260720-153110.tar.gz and cloud.env.bak.20260720-153110 were created; committed Cloud 1951715 was checksum-synced with .env unchanged and no dependency delta, then only aidcp-cloud.service was restarted. Runtime: active, NRestarts=0, deployed SHA matches, 8787/8090/8088 listen, local/public health ok, PostgreSQL select 1, Feishu WSClient onReady, and all four isales services active. ol was not contacted. -->
- [x] 4.5 Backfill task evidence with repo/commit/validation/deployment details and document the So La probe boundary, including the single real Reel like and Edge no-installer boundary.
  <!-- So La live probe established the real Reels DOM/route/summary/like/next behavior. It performed one real like on Reel 837962452581083 and confirmed the selected/unlike witness; that like remains. The integrated implementation is covered by automated tests but was not run as a second live write against the account. Mi Xu (`k1es035u`) was later used for a read-only non-empty feed-end probe: 13 production-scroll rounds reached y=12948/height=13749, then four consecutive rounds had zero remaining distance, stable height, no new canonical card, no loader, and no new GraphQL request; the triggering `CometNewsFeedPaginationQuery` response also carried `has_next_page:false`. The visible Vietnamese end card had no stable data marker, but its locale-independent structure was `role=article` + heading + illustration + one `/friends/` CTA. The probe performed no like/comment/publish and left the existing browser running. No Edge installer was built. -->

## 5. Non-empty Feed exhaustion fallback

- [x] 5.1 Extend the proposal/design/spec contract so confirmed non-empty Facebook `feed_exhausted` reuses the deployed Reels fallback handshake, while non-Facebook exhaustion keeps refresh behavior.
  <!-- Proposal/design/facebook-feed-browse delta now distinguish explicit empty home from confirmed non-empty exhaustion, reuse the deployed handshake for mixed-version safety, preserve non-Facebook refresh, and passed strict OpenSpec validation. -->
- [x] 5.2 Update Cloud RoleDispatcher to authorize the existing `empty_feed_reels_fallback` command once per active Facebook session on `feed_exhausted`, without requiring Edge or protocol changes.
  <!-- aidcp-cloud RoleDispatcher now shares one authorization helper for empty and exhausted Facebook feeds, sets the idempotence gate only after real command dispatch, swallows duplicate exhaustion after authorization, and leaves non-Facebook refresh unchanged. -->
- [x] 5.3 Add focused Cloud integration coverage for Facebook switch, duplicate idempotence, inactive-session rejection, and non-Facebook refresh preservation; keep the existing Edge handshake test green.
  <!-- Cloud focused fallback + platform-browse integration tests passed; Edge facebook-session focused tests passed with the deployed `empty_feed_reels_fallback` handshake unchanged. -->
- [x] 5.4 Run proportionate Edge/Cloud validation and strict OpenSpec validation, then record commit, integration, push, and Cloud `dev` deployment evidence without building an Edge installer.
  <!-- Final delivery 2026-07-20: Cloud focused fallback/platform tests passed (21/21); Cloud full suite 2668 total / 2660 passed / 8 gated / 0 failed; Edge facebook-session focused suite passed; Edge and Cloud typecheck passed; strict OpenSpec passed before and after rebase. Fast-forwarded and pushed aidcp-edge master `9dbfcfe` (read-only probe only; no installer) and aidcp-cloud master `7da82ee` (RoleDispatcher + two tests). dev preflight passed for 121.89.85.150; backups `/opt/aidcp/cloud.bak.20260720-191338.tar.gz` and `/opt/aidcp/cloud/.env.bak.20260720-191338` were created. Exact three-file rsync hashes matched canonical, only `aidcp-cloud.service` restarted, and runtime checks passed: active, NRestarts=0, 8787/8090/8091/8088 listening, panel/public/client-auth health ok, PostgreSQL select 1, Feishu WSClient onReady, no error-priority service logs, and all four isales services active. ol was not contacted. -->
