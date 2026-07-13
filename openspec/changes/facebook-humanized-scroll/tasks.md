## 1. Shared Gesture Boundary

- [x] 1.1 Add a Facebook viewport-scroll helper that reuses the shared inertial scroll physics, injected random/sleep dependencies, viewport-centre wheel dispatch, and bounded movement observation. <!-- aidcp-edge codex/facebook-humanized-scroll: src/facebook/viewport-scroll.ts -->
- [x] 1.2 Add focused unit tests for the helper's frame shape, exact displacement, movement-aware fallback, and non-throwing CDP failure handling. <!-- focused Facebook tests: 33 pass -->

## 2. Facebook Callers

- [x] 2.1 Replace the feed reader's fixed wheel plus unconditional `window.scrollBy` with the shared helper and a 650px jittered baseline. <!-- focused Facebook tests: 33 pass -->
- [x] 2.2 Replace the comment executor's editor lazy-load scroll with the same helper while preserving its bounded probe and honest result behavior. <!-- focused Facebook tests: 33 pass -->

## 3. Verification and Rollout

- [x] 3.1 Run focused Facebook/humanize tests, edge acceptance tests, full edge tests, and typecheck. <!-- focused 33 pass; npm run test:acceptance 16 pass; npm test 1100 pass; npm run typecheck pass -->
- [x] 3.2 Validate the OpenSpec change strictly and record commit, validation, and real-machine observation in the task ledger. <!-- edge 6576a49; openspec validate --strict passed; focused 33 / acceptance 16 / full 1100 / typecheck passed. Real dev observation 2026-07-13: Facebook import 1 (`k1ej3o8f`) measured four document-wheel gestures at about 587/728/657/568px, each continuously advancing over about 0.5s; no successful wheel was followed by JS fallback. -->
- [x] 3.3 Merge the reviewed edge change to `master`, deploy the edge runtime, and observe Facebook import 1 with the existing safety mode before changing any interaction rollout. <!-- edge master fast-forwarded and pushed 6576a49. Started local edge against healthy dev cloud with AIDCP_FB_BROWSE_AUTO=on; Facebook identity, cards, and detail reads were healthy. Views 6 -> 9; likes/comments/follows remained 0. Ctrl-C stopped the edge and AdsPower returned Inactive. No interaction rollout changed. -->
