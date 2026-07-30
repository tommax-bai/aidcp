## 1. Contract Alignment

- [x] 1.1 Synchronize the still-active `restore-native-facebook-residual-parity` design, specification, and task evidence so a later archive cannot restore the rejected five-of-five `explicit_end` home-Feed gate. <!-- proposal/design/spec synchronized; predecessor task 4.9 records the later override -->
- [x] 1.2 Validate that the new `facebook-feed-continuity` and `native-facebook-behavior-parity` deltas define near-bottom as the actual scroll container's one viewport, preserve the five fixed samples, require a same-document validated Feed-identity witness, and keep marker-free completion home-command-only. <!-- both changes pass OpenSpec strict validation after implementation -->

## 2. Native Home-Feed Confirmation

- [x] 2.1 Change the five-sample classifier so a structurally valid canonical home Feed confirms exhaustion after the fifth sample even when `explicit_end` is absent or unstable, while preserving the existing non-home behavior. <!-- home structural confirmation maps to ConfirmedEnd; search/group retain five-marker terminal handling -->
- [x] 2.2 Require the commanded scroll to have observed at least one real validated Feed identity before mapping a structurally confirmed home window to `feed_exhausted`; otherwise retain the existing zero-card/continuation evidence ladder. <!-- the witness is bound to the same home surface, URL, and document time origin; raw-card continuation remains separate -->
- [x] 2.3 Preserve the exact `t=0 / 5 / 7.5 / 10 / 12.5s` schedule, actual-scroll-container one-viewport near-bottom predicate, 100px height-growth threshold, same-document/surface/card checks, cancellation, deadline, and no-early-success rule. <!-- internal probe now carries documentTimeOriginMs and scrollViewportHeight; non-home command redirects cannot inherit marker-free authorization -->

## 3. Regression Coverage

- [x] 3.1 Add or update focused Rust tests proving marker-free and intermittently marked home windows return `feed_exhausted` only after sample five. <!-- stable/partially marked home and no-early-success cases pass in the 23-test Feed focus -->
- [x] 3.2 Add or update negative tests for no prior canonical card, loading, material height growth, new/reordered card identity, navigation/generation/surface change, backward document-age reset, departure from near-bottom, and marker-free search/group windows. <!-- also covers document-time-origin change, nested-scroller viewport, non-home-to-home redirect, and noncanonical raw-card continuation -->
- [x] 3.3 Keep the deterministic timing and cancellation/deadline tests green without weakening the initial-home-empty or present-unreportable ladders. <!-- exact offsets, cancellation/deadline, zero-card, and present-unreportable tests pass -->

## 4. Validation and Delivery

- [x] 4.1 Run focused Facebook Feed Rust tests, `npm run gate:native`, and `npm run typecheck` in the Edge worktree. <!-- Feed Rust 23/23; router contract 98/98; native fmt/clippy/full test OK; typecheck OK -->
- [x] 4.2 Run `openspec validate confirm-facebook-feed-exhaustion-structurally --strict` and strict validation of the synchronized predecessor change. <!-- both strict validations pass -->
- [x] 4.3 Record repository commit SHAs and validation evidence, rebase onto the latest defaults, then fast-forward and push Edge `master` and control `main` without packaging an installer. <!-- aidcp-edge 1607b4f; aidcp dc3ab14c; post-rebase Feed 23/23, router 98/98, native gate/typecheck and both OpenSpec strict validations pass; both defaults fast-forwarded and pushed; no installer built -->

## 5. Daniel Golden Typed-Identity Follow-up

- [x] 5.1 Add one typed validated Feed identity projection in Native Rust: absent/`permalink` identities use the canonical Facebook post identity extracted from a validated content URL, while explicit `content_ref` identities must pass the existing exact prefix and 64-lowercase-hex validator; malformed or kind/value-mismatched cards fail closed. <!-- `facebook_feed_card_identity` reads `note_id_kind`, reuses both existing validators, and rejects every missing/mismatched form -->
- [x] 5.2 Use that same projection in `facebook_page_cards`, typed session seen deduplication, settle/bottom-confirmation ordered identity vectors, and the renamed `FacebookValidatedFeedCardWitness`, removing every permalink-only identity side path. <!-- one helper now feeds all four consumers; witness naming no longer implies permalink-only evidence -->
- [x] 5.3 Preserve operation ordering and evidence scope: report every unseen validated `content_ref` card before considering exhaustion, allow a seen validated card to establish only the current command's same-URL/same-document-time-origin witness, and never carry that witness across commands or documents. <!-- fresh `page.cards` still returns before bottom classification; the witness remains command-local and matches exact surface, URL, and document time origin -->

## 6. Follow-up Regression Coverage

- [x] 6.1 Add focused Rust tests reproducing Daniel Golden's permalink-zero/content-ref-two viewport: unseen valid `content_ref` cards are emitted and entered into typed seen-state before any exhaustion result, while already-seen cards are filtered without losing current-command witness evidence. <!-- the two-card probe emits both refs once, deduplicates both on replay, and the content-ref-only home test reaches exhaustion only after sample five -->
- [x] 6.2 Add negative tests for missing/mismatched identity kind, malformed `content_ref` prefix/digest, cross-command witness reuse, URL/document-time-origin changes, and typed permalink/content-ref dedupe separation. <!-- malformed/uppercase/missing/mismatched identities fail closed; witness mismatch covers surface/URL/document replacement; permalink and content-ref keys coexist in one seen set -->
- [x] 6.3 Keep permalink reporting, the exact `t=0 / 5 / 7.5 / 10 / 12.5s` no-early-success schedule, loading/growth/navigation invalidation, marker-free home-only authorization, and explicit-marker non-home behavior green. <!-- focused Feed 28/28 before final assertion tightening; full Native 165-unit plus integration/doc tests, clippy, fmt, and Edge typecheck pass -->

## 7. Follow-up Validation and Delivery

- [x] 7.1 Run focused Facebook Feed Rust tests, `npm run gate:native`, `npm run typecheck`, and `openspec validate confirm-facebook-feed-exhaustion-structurally --strict`; retain bounded pass/failure evidence. <!-- Feed focused 28/28; post-rebase Native fmt/clippy/165 unit plus integration/doc tests all pass; Edge typecheck passes; this change and the synchronized predecessor both pass strict validation -->
- [ ] 7.2 Record Edge/control commit SHAs and validation evidence, rebase onto the latest defaults, then fast-forward and push the eligible default branches. Keep source, packaged client, and installed-runtime state explicit; do not claim Daniel Golden live acceptance without a separately authorized package/install and observed runtime result.
