## 1. Protocol delta (four optional fields, four-place sync)

- [ ] 1.1 Add to both `src/comm/protocol.ts` (edge + cloud, verbatim-identical) four optional fields: `NoteOpenPayload.surface?:'feed'|'detail'`, `NoteOpenPayload.purpose?:'read'|'navigate'`, `ActionCompletedPayload.noteId?:string`, `ActionCompletedPayload.observation?:{surface?;listKey?;author?;textPreviewHead?;reactionText?;articleIndex?}`; keep the `MessageType` enum unchanged.
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
