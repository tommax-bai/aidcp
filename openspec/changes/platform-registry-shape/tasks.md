## 1. aidcp-cloud — Registry shape (additive)

- [ ] 1.1 Extend `src/platform/registry.ts` `PlatformRegistryEntry` with `noteActions: Record<NoteScopedAction, {supported:true}|{supported:false;reason}>` (all 7 note-scoped actions), `noteSurfaces: Record<'read_content'|'like'|'comment', Surface>`, and `capabilities: Record<'browse'|'feed_refresh', ...>`; fill XHS and Facebook entries with stage-0 values (FB surfaces all `detail`; FB collect `{false,'no_collect_concept'}`; FB comment_like/browse_images/scroll_comments `{false,'v1_unimplemented'}`; FB feed_refresh `supported:true`).
- [ ] 1.2 Migrate the browse startup gate `role-dispatcher.ts:1008` from `.includes('browse')` to `.browse.supported` in the same commit; assert XHS `browse.supported===true`.
- [ ] 1.3 Add pure `src/platform/surface.ts` with `resolveReadSurface(platform)` / `resolveCommentSurface(platform)`.

## 2. aidcp-cloud — Static control flow + capability gate

- [ ] 2.1 Add the private `sendNoteScopedCommand()` wrapper: `noteActions[a].supported===false ⇒ not dispatched + audited reason`; route like/collect/comment/browse_images/scroll_comments/comment_like through it as the single explicit refusal point.
- [ ] 2.2 Drive loop-closure back-vs-scroll from `resolveReadSurface(platform)` plus a per-note `currentNoteMigratedToDetail` flag (set by cloud when it emits a migration command, reset per note); **do not read `observedSurface`** for control (`observedSurface` audit-only).
- [ ] 2.3 Gate FeedScroller construction on `capabilities.feed_refresh` and generalize `facebookScrollDwellMs` into a `pacing.feedScrollDwellFloorMs` consumer.
- [ ] 2.4 Inject fail-open closures `canBrowseImages()`/`canScrollComments()`/`canRefresh()` (mirror `isInteractionEligible` injection at `role-dispatcher.ts:803`); registry-miss/exception ⇒ return true (today's behavior).

## 3. aidcp-cloud — Roles consume injected closures (fail-open, honest short-circuit)

- [ ] 3.1 `deep-reader.ts` short-circuits on `canBrowseImages()===false` to `reading.images_done{imagesBrowsed:0, reason:'surface_unsupported'}` (no LLM, no fabrication); `comment-reviewer.ts` short-circuits on `canScrollComments()===false` to `reading.done{commentsRead:0}`; roles MUST NOT import registry or branch on `platform==='x'`.

## 4. Verification

- [ ] 4.1 Cloud unit tests: registry all-coverage typecheck + test (every platform × every NoteScopedAction has a supported profile; every `supported:false` has a non-empty reason; noteSurfaces 3 keys present; `browse.supported` Record shape ⇒ XHS===true startup gate); capability gate (FB + `interaction.completed{actions:['like','collect']}` ⇒ only like dispatched, collect audited); short-circuit fail-open (`canBrowseImages()` miss/exception ⇒ still dispatch browse_images for XHS; ===false ⇒ `reading.images_done{imagesBrowsed:0}` and LLM not called); static routing (XHS reads `resolveReadSurface`==='detail' ⇒ always back, independent of event order).
- [ ] 4.2 Adversarial-order test: `page.cards.arrived` interleaved between XHS `note.detail` and `feed.entered` ⇒ still emits `back` (proves control flow no longer depends on event ordering).
- [ ] 4.3 Run `npm run test:acceptance`, full `npm test`, `npm run typecheck`; AC-PROTO/AC-RISK stay green.
- [ ] 4.4 Rebase on `origin/master` (serialize on `role-dispatcher.ts` with any concurrent FB change), integrate, push cloud to `master`, deploy dev (backup → rsync → restart → healthcheck), record dev journalctl observation of stage-0 zero-behavior (XHS command sequence unchanged; FB collect refusal audited; FB no stray refresh; FB browse_images/scroll_comments not dispatched) under cluster 65.

## 5. Change Record

- [ ] 5.1 Update this task record with commits, validation, and dev deploy; `openspec validate platform-registry-shape --strict`.
