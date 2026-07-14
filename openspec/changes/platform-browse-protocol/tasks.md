<!-- ============================================================================
     GROUNDING HANDOFF (2026-07-14, done by the session that landed C1a cc2a146).
     Start FRESH via `/impl platform-browse-protocol` (or scripts/new-change for BOTH aidcp-cloud and aidcp-edge) —
     no worktree pre-exists (I created then removed empty ones so the base wouldn't go stale against the churning
     protocol.ts; new-change will branch from the latest master, which is what you want). Symlink node_modules from
     the canonical checkout into each worktree for test/typecheck (never `git add -A` — never commit the symlink).
     No files edited yet — clean start. C1a (platform-registry-shape) is LANDED on cloud master (cc2a146); this
     change's surface resolvers (resolveReadSurface/resolveCommentSurface/loopClosure) + registry noteActions/
     noteSurfaces are already available to import from `src/platform/index.js`.

     ⚠️ CRITICAL FINDINGS from grounding (do not re-derive; do not repeat the mistakes):

     A. `ActionCompletedPayload.observation?: unknown` ALREADY EXISTS (cloud protocol.ts:1149 / edge :1147),
        added by the group-join change (carries group.join click observation). DO NOT add a second `observation`
        field. REUSE it for the note-scoped witness packet (it is already `unknown`, action-discriminated) — just
        extend its doc comment to cover the note-scoped {surface?;listKey?;author?;textPreviewHead?;reactionText?;
        articleIndex?} use, and keep the type `unknown` (narrowing would break group.join). So task 1.1 really adds
        only THREE fields: NoteOpenPayload.surface?, NoteOpenPayload.purpose?, ActionCompletedPayload.noteId?.

     B. The two protocol.ts currently DIFFER (transient cross-repo drift): cloud master has client-preview-image-delete
        (protocol 74→76: +publish.draft_image_remove{,.result} MessageTypes + payloads + a few field-order/wording
        deltas) that edge master has NOT received yet. This is ORTHOGONAL to C1b — my 3 additions go into
        NoteOpenPayload (cloud :420 / edge :418) and ActionCompletedPayload (cloud :1142 / edge :1140), which ARE
        byte-identical between the two repos (only global line-offset differs). Add the SAME lines to both. Do NOT
        try to reconcile the client-preview drift — that resolves when edge catches up.

     C. Exact insertion points (byte-identical in both files):
        - NoteOpenPayload: after `url?: string;`, before the `thinkMs?` comment — add surface? then purpose?.
        - ActionCompletedPayload: after `reason?: string;`, before the group.join `groupUrl?` comment — add noteId?.
        MessageType enum UNTOUCHED ⇒ AC-PROTO stays green, count unchanged. edge-client.ts:487-529 allowlist needs
        NO change (note.open/page.scroll/interaction.like/interaction.comment already in it) — task 1.3 just records this.

     D. handler.ts accounting assumption to replace (task 2.x): the "like always follows note.detail so currentNoteId
        is the interacted note" logic is around handler.ts:409-410 (verify live line). Keep XHS/detail fallback to
        currentNoteId byte-for-byte (zero regression); only feed-surface + missing-noteId path refuses.

     E. STAGE-0 ZERO BEHAVIOR: FB noteSurfaces are all 'detail' (set in C1a) ⇒ resolveCommentSurface===resolveReadSurface
        ⇒ comment migration STRUCTURALLY UNREACHABLE ⇒ all C1b machinery (arbitration/migration/feed_exhausted/idle-
        suppress) is DORMANT scaffolding for C2. Correctness bar = XHS zero-regression + AC-PROTO/AC-PUB/AC-RISK green.

     F. HOTSPOT CHURN: cloud+edge protocol.ts changed within the last hour (fleet very active). Do C1b END-TO-END and
        land BOTH repos in one focused pass (edge protocol delta + cloud everything), then `land-change` each — the
        longer this WIP sits, the worse the rebase against the churning protocol.ts. C1b MUST land before
        facebook-join-actuation-decouple touches protocol.ts (adds clickToken).

     G. Deploy C1a + C1b to dev TOGETHER at the end (C1a's dev deploy was deferred to batch here; both zero-behavior).
     ============================================================================ -->

<!-- LANDED + DEPLOYED 2026-07-14. cloud master `bf3d75a` (incl. C1a `cc2a146` ancestor) / edge master `6dfd067`.
     Deployed dev (121.89.85.150) 18:02:52 CST from clean snapshot bf3d75a (backup cloud.bak.c1b-20260714-175117.tar.gz):
     healthcheck PASS (active, 8787 listening, PG ready, Feishu WSClient established, no errors; C1b `purpose` field live).
     C1a (platform-registry-shape) was ALREADY on dev via a prior fleet deploy ⇒ this deploy shipped only C1b's 7 files
     (dry-run --checksum confirmed exactly those, no regressions). Both zero-behavior. openspec archive pending (batch triage). -->

## 1. Protocol delta (three new optional fields — observation reused; four-place sync)

- [x] 1.1 Add to both `src/comm/protocol.ts` (edge + cloud, verbatim-identical) the optional fields `NoteOpenPayload.surface?:'feed'|'detail'`, `NoteOpenPayload.purpose?:'read'|'navigate'`, `ActionCompletedPayload.noteId?:string`; `MessageType` enum unchanged (count stays 76). <!-- cloud bf3d75a / edge 6dfd067. Per finding A: `observation?: unknown` already existed (group.join) — REUSED it (doc comment extended to cover the note-scoped witness packet {surface?/listKey?/author?/textPreviewHead?/reactionText?/articleIndex?}, type kept `unknown`). So 3 new fields, not 4. Byte-identical diff verified between the two protocol.ts (remaining cross-repo drift is pre-existing/orthogonal — finding B). -->
- [x] 1.2 `command-bridge.ts`: mapping table unchanged; `open_note`/`scroll` already spread `...command.params` ⇒ `surface`/`purpose` pass through transparently, **no code change needed**. <!-- cloud bf3d75a: verified command-bridge.ts open_note=`createEnvelope('note.open', command.params ?? {})`, scroll=`{reason, ...command.params}` — transparent passthrough. -->
- [x] 1.3 Confirmed: `aidcp-edge/src/client/edge-client.ts` active-command allowlist needs **no change** (note.open/page.scroll/interaction.like/interaction.comment already whitelisted; surface/purpose are fields on existing messages, no new active command type). `docs/protocol.md` note.open + action.completed rows extended with the new fields, header count line ("76") unchanged. <!-- aidcp docs/protocol.md updated. -->

## 2. aidcp-cloud — Accounting arbitration (handler.ts) — cloud bf3d75a

- [x] 2.1 Version-skew gate: hello `capabilities` carries `inline_targeting` (stamped onto EdgeSession in onHello); `attributeNoteScopedNoteId` refuses lineage (returns undefined + audit) when `readSurface==='feed'` && edge declared `inline_targeting` && receipt lacks derived noteId — never falls back to currentNoteId. <!-- reused existing HelloPayload.capabilities?:string[] (no 5th protocol field). Dormant in stage 0 (readSurface all 'detail'). Test: handler-attribution.test.ts feed-surface refuse + old-edge fallback. -->
- [x] 2.2 XHS / detail path: receipt without noteId ⇒ falls back verbatim to `session.currentNoteId` (zero regression). <!-- In stage 0 this is the ONLY active path (no derived id/observation, readSurface detail) ⇒ byte-identical. follow/comment/comment_like/join_group attribution untouched. -->
- [x] 2.3 Independent-witness comparison (`witnessVerdict`): receipt `observation{author,textPreviewHead}` vs the selected card (looked up in `session.lastCards` by currentNoteId, retained on page.cards); mismatch ⇒ refuse lineage (noteId undefined) + warn + `targetMismatchCount++` (grayscale counter); risk still counts (interaction.occurred still emitted, without noteId). <!-- Kept arbitration handler-local (no dispatcher port) — lastCards is the witness source. Test: witness match + mismatch. -->
- [x] 2.4 `no_target(stale)` on feed-surface like/collect ⇒ dispatcher rescans (scroll `rescan_after_stale_target`); never counted as quota failure (budget only decremented on ok:true). <!-- role-dispatcher.ts action.completed guarded branch, dormant in stage 0 (readSurface detail). Test: FB feed-surface rescan vs XHS detail no-rescan. -->
- [x] 2.5 Handled via the migration navigate step (§3.1): navigate awaits `action.completed` (not `note.detail`), so a decision-path note.detail cannot overwrite counts during navigate; the edge-side `purpose:'navigate'` skip-reportNoteDetail is C2 edge work (see 3.2). <!-- Not a standalone note.detail mutation (would risk XHS); the navigate contract sidesteps it. -->

## 3. aidcp-cloud — Receipt-driven two-step comment migration (dispatcher) — cloud bf3d75a

- [x] 3.1 On `comment.approved` when `resolveCommentSurface!==resolveReadSurface`: emit `open_note{noteId,purpose:'navigate'}`, set `pendingMigration`; on its `action.completed{action:'open_note', ok, observation.surface:'detail', noteId matches}` ⇒ markNoteMigratedToDetail + emit `comment`; nav fail ⇒ no comment + `reportApprovedNotDelivered` (optional `notifyApprovedNotDelivered` closure, else warn) + `comment.done{ok:false}`. <!-- Stage 0 unreachable (commentSurface===readSurface). URL enrichment for FB navigate is C2 (CommentApprovedPayload carries no url yet). Test: two-step sequence + nav-fail + stage-0 no-migrate. -->
- [~] 3.2 `purpose:'navigate'` onOpen skip `reportNoteDetail` — **EDGE behavior, deferred to C2** (facebook-feed-inline-browse owns edge browse handlers). Dormant in stage 0 (navigate never sent). Cloud side already avoids the overwrite by awaiting action.completed, not note.detail. <!-- registered for C2; edge C1b scope was protocol-only per handoff. -->

## 4. aidcp-cloud — Feed self-heal + approval timing — cloud bf3d75a

- [x] 4.1 `feed_exhausted` receipt ⇒ immediately `refresh` (guarded on canRefresh + sessionActive), avoiding idle/240s nudge loop. <!-- role-dispatcher.ts action.completed early branch. Test: FB feed_exhausted→refresh. -->
- [x] 4.2 `approvalInFlight` flag set by `comment.cleared`, cleared by `comment.approved`+`comment.skipped` (and session reset); dispatcher idle_nudge translator suppresses the scroll while set. **Not pauseClock.** <!-- Event-driven bracket (gate already emits these). Test: XHS idle_nudge suppressed in window then restored; comment.approved also clears. -->
- [x] 4.3 `observedSurface` audit-only: action.completed handler warns when `observation.surface` echo ≠ static `resolveReadSurface`; never drives control flow. <!-- Dormant in stage 0 (no surface echo). -->

## 5. Verification

- [x] 5.1 Cloud unit tests (test/integration/platform-browse-protocol.test.ts + test/handler-attribution.test.ts): migration two-step + nav-fail + stage-0 no-migrate; accounting (witness mismatch/match, feed-surface refuse, old-edge fallback, derived-id precedence); no_target rescan; feed_exhausted→refresh; idle-nudge suppression (pauseClock not reused). <!-- 20 tests in the two files, all green. -->
- [x] 5.2 Adversarial-order test: idle_nudge inside approval window ⇒ XHS produces no extra scroll, restored after terminal. <!-- covered by the idle-suppress test. -->
- [x] 5.3 `test:acceptance` 50/50 → `npm test` 1993/1993 → `typecheck` clean; AC-PROTO (count 76 unchanged, edge AC-PROTO 19/19), AC-PUB, AC-RISK green. <!-- cloud bf3d75a / edge 6dfd067. -->
- [x] 5.4 Rebased on origin/master (clean), landed both repos to `master` (cloud bf3d75a / edge 6dfd067; ahead of `facebook-join-actuation-decouple` which is still 0/24, hasn't touched protocol.ts), deployed dev 18:02:52 (stage-0 zero-behavior). <!-- real-machine stage-0 verification belongs to cluster 65 (see backlog). -->

## 6. Change Record

- [x] 6.1 Task record updated with commits (cloud bf3d75a / edge 6dfd067), validation (`openspec validate platform-browse-protocol --strict` = valid), and dev deploy. <!-- openspec archive held for the next landed+deployed triage batch (with C1a). -->

## Notes

- **`facebook-join-actuation-decouple` MUST rebase after this** (it also touches protocol.ts to add clickToken; still 0/24, hasn't started). C1b landed first as planned.
- **C1a's own deploy is now satisfied** (it was already on dev; this batch confirmed both zero-behavior on dev). C1a archive travels with C1b in the next triage batch.
- **C2 handoff**: edge must (a) populate `action.completed.noteId` (derived) + note-scoped `observation` on inline like, (b) honor `purpose:'navigate'` by skipping reportNoteDetail (task 3.2), (c) supply the target URL for FB comment migration. Flip FB `noteSurfaces.read_content`/`like` to 'feed' in the registry (data change) to activate all C1b machinery.
