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
  <!-- Final focused 71/71; full npm test 1977/1977; npm run typecheck passed. No installer/package built. -->
- [x] 4.2 Run Cloud focused integration/protocol/risk tests, required full tests, and typecheck; record concise evidence and confirm RiskController remains the only final risk writer.
  <!-- Focused fallback/protocol 36/36; full npm test 2656 passed, 8 gated/skipped, 0 failed; typecheck passed. Like receipt still enters existing handler/RiskController path. -->
- [ ] 4.3 Run strict OpenSpec validation and protocol-drift checks, then commit and push isolated Edge, Cloud, and control changes.
- [ ] 4.4 Integrate clean default branches serially and deploy Cloud to `dev` after `deploy-target dev --check`; verify service, listener, health, logs, Feishu, and PostgreSQL without touching unrelated services.
- [ ] 4.5 Backfill task evidence with repo/commit/validation/deployment details and document the So La probe boundary, including the single real Reel like and Edge no-installer boundary.
