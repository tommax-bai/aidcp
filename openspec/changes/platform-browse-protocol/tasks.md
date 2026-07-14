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

## 1. Protocol delta (four optional fields, four-place sync)

- [ ] 1.1 Add to both `src/comm/protocol.ts` (edge + cloud, verbatim-identical) four optional fields: `NoteOpenPayload.surface?:'feed'|'detail'`, `NoteOpenPayload.purpose?:'read'|'navigate'`, `ActionCompletedPayload.noteId?:string`, `ActionCompletedPayload.observation?:{surface?;listKey?;author?;textPreviewHead?;reactionText?;articleIndex?}`; keep the `MessageType` enum unchanged. <!-- NB per finding A: `observation?: unknown` already exists (group.join) — REUSE it (only add surface?/purpose?/noteId?, 3 new fields not 4). -->
- [ ] 1.2 `aidcp-cloud/src/comm/command-bridge.ts`: mapping table unchanged; transparently pass `surface`/`purpose` in the `open_note`/`scroll` payload construction.
- [ ] 1.3 Confirm and record in this file: `aidcp-edge/src/client/edge-client.ts:487-529` allowlist needs **no change** (no new active command type); append the two field notes to `aidcp/docs/protocol.md` without changing the header count.

## 2. aidcp-cloud — Accounting arbitration (handler.ts)

- [ ] 2.1 Version-skew gate: hello carries edge capability bit `inline_targeting`; when static `readSurface==='feed'` and the receipt lacks a noteId ⇒ refuse to account + audit, never fall back to `currentNoteId`.
- [ ] 2.2 XHS / detail path: receipt without noteId ⇒ fall back verbatim to today's `currentNoteId` logic (zero regression).
- [ ] 2.3 Independent-witness comparison: `observation{author,textPreviewHead,reactionText}` vs the selected `page.cards` card, field by field; mismatch ⇒ `target_mismatch` + refuse to write `liked_notes` lineage + audit + grayscale rollback counter; risk still counts the real occurrence.
- [ ] 2.4 `no_target(stale)` ⇒ treat snapshot as expired (postId out of session candidates + rescan/reselect), never count as an interaction-quota failure.
- [ ] 2.5 note.detail derived-noteId semantics: a decision-path `note.detail` whose landing-derived noteId differs from the requested one is discarded + audited.

## 3. aidcp-cloud — Receipt-driven two-step comment migration (dispatcher)

- [ ] 3.1 On `comment.approved` when `resolveCommentSurface!==resolveReadSurface`: emit `open_note{noteId,url,purpose:'navigate'}`, wait for its `action.completed{ok, observation.surface:'detail', noteId matches}`, then emit `comment{noteId,text}`; any step failing ⇒ do not emit comment + report "approved-not-delivered" to the operator (Feishu).
- [ ] 3.2 `purpose:'navigate'` onOpen MUST skip `reportNoteDetail` (do not overwrite real reaction counts with 0).

## 4. aidcp-cloud — Feed self-heal + approval timing

- [ ] 4.1 `feed_exhausted` receipt ⇒ immediately map to refresh (avoid idle/240s nudge loop).
- [ ] 4.2 Suppress idle nudge while an approval is in flight (session flag set by `comment-approval-gate`, gated in the dispatcher idle_nudge translator; **do not reuse `pauseClock`**, it does not freeze idle); clear the flag when approval resolves.
- [ ] 4.3 `observedSurface` audit-only: warn on echo vs static `resolveReadSurface` mismatch; MUST NOT drive control flow.

## 5. Verification

- [ ] 5.1 Cloud unit tests: migration receipt-driven (FB + comment.approved + read=feed ⇒ sequence exactly `[open_note{purpose:'navigate',url}, (await ok), comment]`; navigate returns nav_failed ⇒ comment not emitted + operator report; XHS ⇒ comment only, zero regression); accounting arbitration (witness mismatch ⇒ `target_mismatch` + no lineage + risk still counts; read=feed missing noteId ⇒ refuse; XHS missing noteId ⇒ fall back to currentNoteId); no_target(stale) reselect not counted; feed_exhausted→refresh; idle-nudge suppression (pauseClock not reused).
- [ ] 5.2 Adversarial-order test: idle_nudge inside the approval window ⇒ XHS produces no extra open_note, not scrolled off target.
- [ ] 5.3 `npm run test:acceptance` → `npm test` → `npm run typecheck`; AC-PROTO (two protocol.ts verbatim-identical, count unchanged), AC-PUB, AC-RISK all green.
- [ ] 5.4 Rebase on `origin/master` (serialize on protocol.ts / command-bridge.ts / role-dispatcher.ts / handler.ts; land before `facebook-join-actuation-decouple` touches protocol.ts), integrate, push both repos to `master`, deploy dev, record stage-0 zero-behavior under cluster 65.

## 6. Change Record

- [ ] 6.1 Update this task record with commits, validation, and dev deploy; `openspec validate platform-browse-protocol --strict`.
