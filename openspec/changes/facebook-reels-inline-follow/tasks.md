## 1. Protocol and contract synchronization

- [x] 1.1 Add optional Reel `noteId` to `InteractionFollowPayload` in Edge and Cloud without changing the message type or existing `authorId` callers.
- [x] 1.2 Document the Reel-specific targeting semantics and compatibility boundary in `docs/protocol.md`.

## 2. Edge Reel follow actuator

- [x] 2.1 Add a fail-closed active-Reel follow probe that binds the canonical Reel, unique author, and unique Follow/Following control across supported Facebook locales.
- [x] 2.2 Implement `FacebookReelsReader.follow(noteId, shadow)` with trusted input, pre-write stale-target recheck, bounded same-Reel verification, and truthful `already_followed` / shadow / failure outcomes.
- [x] 2.3 Route `interaction.follow` through the Reel reader only in Reels mode while preserving `capability_unsupported` on other Facebook surfaces.
- [x] 2.4 Keep the durable AdsPower probe read-only by default, exact-author gated, and aligned with the production target/verification logic.

## 3. Tests and validation

- [x] 3.1 Add Reel reader tests for exact success, already-followed no-op, shadow, stale note, missing target, ambiguous target, state unchanged, and movement during verification.
- [x] 3.2 Add Facebook session tests for Reels routing, payload forwarding, terminal receipts, and unchanged Feed unsupported behavior.
- [x] 3.3 Add Edge and Cloud protocol compatibility coverage for optional `noteId`, then run focused tests, required acceptance/full suites, and both repositories' typechecks.
  <!-- Validation 2026-07-20: Edge focused 92/92, acceptance 28/28, full 2062/2062, typecheck pass; Cloud focused protocol 22/22, acceptance 64/64, full 2723 pass + 8 intentionally skipped + 0 fail, typecheck pass. -->
- [x] 3.4 Record the authorized real probe evidence: `Tianxing Bai` followed `Salon de Comolis` on Reel `1964804494173822`, and the same unique control changed from `关注` to `已关注`; no automatic unfollow was performed.
  <!-- Evidence 2026-07-20: exact-author probe found one `aria-label="关注Salon de Comolis"` candidate on the canonical Reel, dispatched one trusted click under the explicit write flag, and verified `aria-label="已关注Salon de Comolis"` on the same Reel. The probe intentionally did not unfollow. -->

## 4. Integration and closeout

- [x] 4.1 Run `openspec validate facebook-reels-inline-follow --strict` and record repository commits, validation evidence, and deviations here.
  <!-- Commits: aidcp-edge 6665b88; aidcp-cloud f6118fc. `openspec validate facebook-reels-inline-follow --strict` passed on 2026-07-20. Deviation: no automatic Reel follow policy was added because no selection/probability rule was requested; this change provides the explicitly commanded actuator. -->
- [ ] 4.2 Fetch/rebase and fast-forward integrate the isolated Edge, Cloud, and control changes without overwriting the concurrent Reel random-like work; push eligible default branches.
- [x] 4.3 Do not build an Edge installer. Record that installed clients remain unchanged until an explicit package/release request; no runtime deployment is required for protocol type/docs-only Cloud changes.
  <!-- Delivery boundary: no Edge installer/package was built, so installed clients are unchanged. Cloud changes are TypeScript protocol types plus an offline contract test only; no runtime deployment is required. -->
