## 1. Shared multi-layout discovery

- [x] 1.1 Add a self-contained semantic-first feed-layout helper for top-level card discovery and closest-card lookup in `aidcp-edge`.
  <!-- aidcp-edge: FB_FEED_LAYOUT_HELPERS_JS added in src/facebook/post-identity.ts; semantic feed remains first, lightweight story-message roots are deduplicated and bounded. -->
- [x] 1.2 Route feed surface probing and card extraction through the shared helper while preserving canonical post identity filtering.
  <!-- aidcp-edge: feed-reader probe/scan share the helper and accept only links passing canonicalPostId; ambiguous photo-only fixture remains unreported. -->
- [x] 1.3 Route in-feed target resolution and exact-card attribution through the same helper without broadening action scope.
  <!-- aidcp-edge: FB_TARGET_HELPERS_JS delegates closest/top-card lookup to the shared helper; like observation recognizes lightweight feed cards. -->

## 2. Regression validation

- [x] 2.1 Add semantic-layout, lightweight-layout, ambiguous-media, deduplication, and cross-card scoping fixture tests.
  <!-- aidcp-edge: feed-reader and like-executor jsdom regressions cover both layouts, duplicate story nodes, media-only identity rejection, and second-card targeting. -->
- [x] 2.2 Run focused Facebook tests, the full Edge test suite, and Edge typecheck.
  <!-- aidcp-edge: focused feed/target tests passed (46/46 after new fixtures); integration gate passed acceptance 25/25, full suite 1940/1940 after rebase, and `npm run typecheck`. -->
- [x] 2.3 Validate both local Facebook layouts through read-only CDP and record the honest detection/identity evidence.
  <!-- 2026-07-20 read-only CDP: Tianxing Bai semantic layout hasFeed=true/cardCount=1; Mi Xu lightweight layout hasFeed=true/hydratedArticles=4/cardCount=1 (fb:2136768337195940). No Facebook interaction was executed. -->

## 3. Integration and rollout

- [x] 3.1 Update this checklist with repository commit and validation evidence, then run strict OpenSpec validation.
  <!-- aidcp-edge final commit aac77e4; fixture/focused/full/typecheck/live-CDP evidence recorded above. `openspec validate facebook-feed-multi-layout-compatibility --strict` passes before and after integration. -->
- [x] 3.2 Integrate and push the clean `aidcp-edge` default branch and the control-repo OpenSpec change.
  <!-- aidcp-edge aac77e4 fast-forwarded to origin/master and canonical checkout; this active OpenSpec change is committed/pushed on control main in the same closeout. -->
- [x] 3.3 Keep this Edge rollout source-only (no installer build), record the local read-only runtime validation, and leave autonomous browsing stopped.
  <!-- Edge has no ECS runtime artifact for this source-only change. No installer was built and no autonomous Facebook action was run. The two temporary AdsPower profiles and runtime were stopped; ports 50325/52298/52299 are closed. -->
