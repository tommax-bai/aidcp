## 1. Reels navigation implementation

- [x] 1.1 Add trusted ArrowDown and randomized 70–100px wheel input helpers with an injectable random source.
- [x] 1.2 Implement the ordered keyboard → wheel → button ladder with a fresh pre-write probe and route/video identity verification after every method.
- [x] 1.3 Tighten the next-control fallback for the first-Reel layout and add method-level diagnostic logging without changing protocol semantics.
  <!-- aidcp-edge reels-reader.ts: trusted rawKeyDown/keyUp, inclusive clamped wheel distance, per-method movement proof, scoped first-Reel button fallback, and method-specific logs. -->

## 2. Regression coverage

- [x] 2.1 Add focused reader tests for keyboard success, wheel fallback/order/range, late movement, button fallback, header exclusion, ambiguity, and all-method failure.
- [x] 2.2 Keep the Facebook session projection and truthful `scroll/no_target` behavior covered.
  <!-- Focused Reels/session suite passed 58/58; jsdom reproduces the So La header + disabled previous + single enabled next layout and proves animation-only rect drift keeps a stable video identity. -->

## 3. Validation and delivery

- [x] 3.1 Run focused Facebook tests, Edge acceptance/full tests, and typecheck; record concise results.
  <!-- 2026-07-20: focused Reels/session 58/58; Edge acceptance 26/26; Edge full suite 2002/2002; npm run typecheck and git diff --check passed. -->
- [x] 3.2 Run strict OpenSpec validation and a bounded So La navigation probe, without likes/comments/publishing.
  <!-- Strict validation passed. So La profile k1es0359: a temporary foreground Reel tab showed trusted ArrowDown starting the vertical transition; follow-up sampling proved the same video element's rect drifts during animation, which informed the stable element identity fix. No like/comment/publish input was sent. The profile closed before an end-to-end rerun of the final patched reader, so final fallback ordering is automated-test validated. -->
- [x] 3.3 Commit, push, rebase, and fast-forward integrate the isolated Edge and control changes without force-pushing.
  <!-- aidcp-edge 81b520f7eea0a606cf386f1aba34f7b276d5acf2 was rebased onto current origin/master, revalidated, pushed to its feature branch, and fast-forwarded to master. The control change was rebased onto current origin/main and is delivered by this evidence commit using the same non-force flow. -->
- [x] 3.4 Backfill commit/validation/live-probe evidence and record that no Cloud deployment or Edge installer was required.
  <!-- Final post-rebase validation: acceptance 26/26, full Edge suite 2022/2022, typecheck, diff checks, and strict OpenSpec all passed. This is an Edge-only source/runtime behavior change: no Cloud code or server deployment changed, and no Edge installer was built. -->

## 4. Reels view accounting follow-up

- [x] 4.1 Record one Cloud `view` for every presented non-empty Reels card, suppress a matching later `note.detail` from double-counting, and enforce view quota at the shared scroll exit.
  <!-- aidcp-cloud handler records the single active Reels card at page.cards ingress; EdgeSession.countedReelViewNoteId suppresses only the matching later detail-side view; RoleDispatcher.sendScrollCommand closes the prior all-skip quota bypass. -->
- [x] 4.2 Add focused Cloud tests for skipped-Reel view accounting, matching-detail deduplication, normal feed preservation, and empty Reels.
  <!-- Focused handler/risk suites passed 25/25 with matching detail preservation, feed regression, empty/malformed Reels fail-closed coverage, and all-skip scroll quota sleep; post-change Cloud acceptance/full suite passed 2677 with 8 explicit gated skips and 0 failures; typecheck and diff checks passed. -->
- [x] 4.3 Record the So La evidence explaining why the run emitted only scroll commands and no likes.
  <!-- dev 2026-07-20 17:40-17:46, account 61592039187933 / edge ads-k1es0359: Edge proved successive Reel URL movement, Cloud content_evaluator skipped nearly all visible Vietnamese/off-persona cards and sent only scroll; no note.detail/reading.done/interaction_appraiser chain and therefore no interaction.like command. Daily usage remained view=0, like=0 despite available like quota. One first-card valuable decision overlapped startup nickname capture and was not dispatched, but later cards were explicit persona/content skips rather than Edge like failures. -->
- [ ] 4.4 Run focused/full Cloud validation and strict OpenSpec validation, integrate without force-push, deploy to `dev`, and backfill evidence.
