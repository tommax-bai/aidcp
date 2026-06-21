# Tasks — comment-like-on-detail

> Re-ground EVERY file/symbol below by SYMBOL (not line number) at apply time — aidcp-cloud has concurrent uncommitted WIP. Stage your own files explicitly (never `git add -A`). Land after the 4 overlapping active changes (comment-interaction, interaction-appraiser-like-rebalance, captcha-restrict-and-interaction-gating, follow-already-followed-truthful-report) archive, or rebase onto them.

## 0. Phase-0 live probe (HARD GATE — DONE)

- [x] 0.1 Probe per-comment like control selector, liked-state signal, and anchor re-location survival on a real detail page <!-- aidcp-edge scripts/comment-like-probe.ts (uncommitted) — PASSED 2026-06-21: like btn = #comment-<id> .interactions .like .like-wrapper; liked signal = svg use #like→#liked + count+1 (like-active is base class, not signal); anchor survival after heavy scroll = 100% (20/20), no virtualization → cloud-pick→edge-relocate round-trip VALID -->

## 1. aidcp-cloud + aidcp-edge — protocol plumbing

- [ ] 1.1 Add cloud→edge message `interaction.like_comment` with payload `{ requestId, commentAnchorId, noteId, reason?, thinkMs? }` to the MessageType union + PayloadMap in cloud `src/comm/protocol.ts`
- [ ] 1.2 Mirror 1.1 BYTE-IDENTICAL in edge `src/comm/protocol.ts`
- [ ] 1.3 Add optional `candidates?: CommentCandidate[]` (`{ anchorId, author, text }`) to `ActionCompletedPayload` in BOTH protocol.ts files (byte-identical)
- [ ] 1.4 Add EdgeCommand action `like_comment` to the EdgeCommand action union and a case in command-bridge mapping it → `createEnvelope('interaction.like_comment', params)` (cloud)
- [ ] 1.5 Compute the live MessageType count N at apply time; bump the AC-PROTO `ALL_TYPES.length` assertion N→N+1 and add the `interaction.like_comment` key to `ALL_MESSAGE_TYPES` in BOTH repos' protocol-contract tests
- [ ] 1.6 Update `docs/protocol.md` (this repo): header count N→N+1, add `interaction.like_comment` to the §2 message table + action↔message map, note the new `candidates` field on the scroll receipt

## 2. aidcp-cloud — separate `comment_like` risk action

- [ ] 2.1 Add `comment_like` to the `RISK_ACTIONS` tuple in `src/risk/types.ts` (do NOT add it to the per-note `InteractionAction` union)
- [ ] 2.2 Add a `comment_like` key to ALL quota literals (conservative/normal/aggressive daily + minute/hour burst caps) in `src/risk/quotas.ts` — defaults conservative 3 / normal 6 / aggressive 12, minute cap 1, small hour cap
- [ ] 2.3 Confirm (no edit) the like/view ratio gate stays keyed to `like` only so `comment_like` is excluded, and that restricted-state zeroing / frozen / warned degradation are inherited generically
- [ ] 2.4 RED-LINE: fix the `action.completed` recording filter in `src/comm/handler.ts` so a `comment_like` (or its edge action name) receipt is recorded on ok:true instead of being string-dropped; include it in the emitted interaction-recording action union
- [ ] 2.5 Guard server side-effects so `comment_like` does NOT fire the liked-note store, does NOT enter the like/collect dedup table, and does NOT route into the per-note interaction table (`src/server.ts`)
- [ ] 2.6 Widen the `canInteract` closed action union to include `comment_like` at its call sites and add a `getCommentLikeDailyRemaining` via `riskController.dailyRemaining('comment_like')` (mirror the comment one)
- [ ] 2.7 Add an idempotent ALTER to the `risk_counters` CHECK constraint to allow `comment_like` in `src/risk/pg-risk-store.ts` (IF-NOT-EXISTS guarded, never DROP); leave the per-note interaction CHECK untouched

## 3. aidcp-edge — act path (edge executor + candidate harvest)

- [ ] 3.1 In the comment-scroll handler, after the scroll settles, harvest a final-viewport candidate list `{ anchorId, author, text }` from `[id^="comment-"]` rows and attach it to the existing scroll receipt (best-effort; empty list reported truthfully)
- [ ] 3.2 Implement `executeLikeComment(anchor)`: re-locate via `getElementById`; DOM-first 3 gates — find the row's `.interactions .like .like-wrapper`, click it, then post-verify the `use` flips `#like`→`#liked` and/or `.count` increments; report success only on confirmed flip
- [ ] 3.3 On missing anchor report `no_target` with NO positional fallback; on click-without-state-change report state-unchanged; pre-filter already-liked (`#liked`); echo `requestId` on the receipt; fresh captcha re-check before click
- [ ] 3.4 Add the `interaction.like_comment` command case: wait the cloud `thinkMs` plus lognormal jitter only (no extra edge timing), call `executeLikeComment`, report the typed result

## 4. aidcp-cloud — act path (appraiser + dispatch + frequency pre-gate)

- [ ] 4.1 New role `comment_like_appraiser` (RoleName `comment_like_appraiser`, distinct from `comment_appraiser`) in `src/agents/`, registered in the role dispatcher; triggers on the comment-scroll receipt (ok + non-empty candidates) on its OWN single-flight; MUST NOT defer/emit reading-done
- [ ] 4.2 Appraiser pre-gate (BEFORE the LLM), ordered AND-chain: per-session `commentLikes` cap → ratio knob (default 0.15 vs this-session note-like count) → Bernoulli abstain → `dailyRemaining('comment_like') > 0`; fail any → abstain, no LLM, no budget touch
- [ ] 4.3 Appraiser LLM: score candidates for interest/knowledge-depth/resonance over note body + candidates, pick 0-or-1, filter own/already-liked/anchorless; parse-failure = ABSTAIN (never default-pick); on a pick, hold `{ requestId, anchorId, text, author }` in request-id-keyed single-flight state and emit the like intent
- [ ] 4.4 Dispatcher: on the like intent apply `canInteract('comment_like')` + `commentLikes` budget honest-skip (blocked → no command, no decrement, log); dispatch `like_comment` with `thinkMs` from the centralized pacing
- [ ] 4.5 Add `commentLikes` to the per-session budget (`freshBudget`/`getRemaining`) and a `comment_like` case to `consumeBudget` that decrements ONLY on the confirmed ok:true receipt; add `comment_like`/`like_comment` to the no-recover-scroll set
- [ ] 4.6 Gate the whole feature behind a config flag (default OFF)

## 5. aidcp-cloud — valuable-comment corpus + composer

- [ ] 5.1 New PostgreSQL store (clone the existing concept/liked-note store pattern): idempotent boot DDL for `valuable_comments` `{ id, comment_text, author, source_note_id, concept_keys, value_tags, score, liked_at, dedup_key UNIQUE }`, insert-or-ignore on dedup_key, retention cap (newest N per topic)
- [ ] 5.2 New thin role `valuable-comment-archivist`: subscribe to the CONFIRMED comment-like ok:true receipt ONLY; archive from the appraiser's correlated single-flight state (by requestId) with an interleaving guard; key by extracted concepts with a note-title-hash fallback when concepts are empty
- [ ] 5.3 Composer: add an optional `getCorpusReferences(keywords)` input that injects a "参考（仅作灵感，不可照抄）" block — empty/PG-down → unchanged prompt
- [ ] 5.4 Thread the used references through the comment-composed event payload so the de-AI/flavor role can see them
- [ ] 5.5 De-AI/flavor overlap guard: detect near-verbatim overlap with a reference, rewrite once, then SKIP if still overlapping (never loop, never ship a near-copy)
- [ ] 5.6 State the PII/retention posture (other users' text + author handles persisted; retention cap; raw-vs-hashed author decision)

## 6. Acceptance red lines (aidcp-cloud + aidcp-edge)

- [ ] 6.1 AC-PROTO: `ALL_TYPES.length === N+1` in both repos; `interaction.like_comment` constructs a valid v2 envelope; the two MessageType unions stay byte-identical
- [ ] 6.2 AC-RISK: a confirmed comment-like records exactly one `comment_like` (guards the handler-filter fix); it does NOT change the note-like count and does NOT affect the like/view ratio; restricted/frozen → blocked; quota exhausted → honest skip with no budget decrement
- [ ] 6.3 AC-EDGE: missing anchor → `no_target` with NO positional fallback; non-registering click → state-unchanged; cloud records nothing in both cases
- [ ] 6.4 AC-APPRAISER: malformed LLM output → abstain (no dispatch, no budget decrement)
- [ ] 6.5 AC-NO-DEADLOCK: reading-done always fires regardless of the comment-like outcome
- [ ] 6.6 AC-FREQ: over a simulated session comment-likes converge to ≈15% of note-likes and never exceed the per-session cap; early-session zero-fire asserted as expected
- [ ] 6.7 AC-CORPUS: archived only on confirmed ok:true; correlated text/author match the liked comment; dedup keeps a single row; retention cap evicts oldest per topic
- [ ] 6.8 AC-COMPOSER: empty/unavailable corpus → unchanged composing; near-verbatim overlap → rewrite-once-then-skip
- [ ] 6.9 AC-MIGRATION: the `risk_counters` CHECK ALTER is idempotent (re-run is a no-op)
- [ ] 6.10 Run `npm run test:acceptance` then full `npm test` then `npm run typecheck` in BOTH repos

## 7. Deploy (ECS — ordered, gated)

- [ ] 7.1 Dry-run the rsync scope and surface accumulated master scope before deploying (ECS ships full master)
- [ ] 7.2 HARD ORDERED: run the `risk_counters` CHECK ALTER on live ECS PG BEFORE service restart; then backup → rsync → restart → healthcheck
- [ ] 7.3 Enable the config flag conservatively (small per-session cap / low ratio / conservative quota tier); observe comment_like-vs-note-like ratio converging to ≈15% and watch `no_target` rates for selector drift
