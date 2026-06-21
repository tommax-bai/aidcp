# Tasks — comment-like-on-detail

> Re-ground EVERY file/symbol below by SYMBOL (not line number) at apply time — aidcp-cloud has concurrent uncommitted WIP. Stage your own files explicitly (never `git add -A`). Land after the 4 overlapping active changes (comment-interaction, interaction-appraiser-like-rebalance, captcha-restrict-and-interaction-gating, follow-already-followed-truthful-report) archive, or rebase onto them.

## 0. Phase-0 live probe (HARD GATE — DONE)

- [x] 0.1 Probe per-comment like control selector, liked-state signal, and anchor re-location survival on a real detail page <!-- aidcp-edge scripts/comment-like-probe.ts (uncommitted) — PASSED 2026-06-21: like btn = #comment-<id> .interactions .like .like-wrapper; liked signal = svg use #like→#liked + count+1 (like-active is base class, not signal); anchor survival after heavy scroll = 100% (20/20), no virtualization → cloud-pick→edge-relocate round-trip VALID -->

## 1. aidcp-cloud + aidcp-edge — protocol plumbing

- [x] 1.1 Add cloud→edge message `interaction.like_comment` with payload `{ commentAnchorId, noteId, reason?, thinkMs? }` to the MessageType union + PayloadMap in cloud `src/comm/protocol.ts` <!-- deviation: requestId NOT on the wire — correlation is cloud-internal via single-flight (edge only needs the anchor) -->
- [x] 1.2 Mirror 1.1 BYTE-IDENTICAL in edge `src/comm/protocol.ts`
- [x] 1.3 Add optional `candidates?: CommentCandidate[]` (`{ anchorId, author?, text }`) to `ActionCompletedPayload` in BOTH protocol.ts files (byte-identical)
- [x] 1.4 Add EdgeCommand action `comment_like` to the EdgeCommand action union and a case in command-bridge mapping it → `createEnvelope('interaction.like_comment', params)` (cloud) <!-- deviation: action string is 'comment_like' (not 'like_comment') for symmetry with the RiskAction + reported action.completed -->
- [x] 1.5 Live count was N=55; bumped the AC-PROTO `ALL_TYPES.length` assertion 55→56 and added the `interaction.like_comment` key to `ALL_MESSAGE_TYPES` in BOTH repos' protocol-contract tests
- [x] 1.6 Updated `docs/protocol.md`: header count 55→56, added `interaction.like_comment` to the §2 message table + action↔message map

## 2. aidcp-cloud — separate `comment_like` risk action

- [x] 2.1 Added `comment_like` to `RISK_ACTIONS` in `src/risk/types.ts`; kept it OUT of `InteractionAction` (no per-note dedup) with a comment explaining why
- [x] 2.2 Added `comment_like` to ALL 5 quota literals in `src/risk/quotas.ts` — daily conservative 3 / normal 6 / aggressive 12, minute 1, hour 3 <!-- also cold-start-planner.ts QuotaRange 7 entries (tsc-forced): day1-2 [0,0]/day3-4 [0,1]/day5-7 [0,2] -->
- [x] 2.3 Confirmed (no edit): like/view ratio gate stays `action==='like'`; `zeroInteractions` spares only `view` so `comment_like` is zeroed under restricted; record/canDo/dailyRemaining are generic over RiskAction
- [x] 2.4 RED-LINE fixed: `src/comm/handler.ts` recording filter + the `interaction.occurred` emit action cast now include `comment_like` (recorded on ok:true via `record(evt.action)`)
- [x] 2.5 Confirmed (no edit needed): `src/server.ts` `likedNoteStore.recordLike` is `action==='like'` only and the `recordInteraction` dedup branch is `like||collect` only — `comment_like` flows through `record()` (counts) but is correctly excluded from both <!-- grounding suggested adding it to dedup; overridden per design -->
- [x] 2.6 Widened `RiskCanDoPayload['action']` (both protocol.ts byte-identical, tsc-forced by risk.canDo/record handlers) to include `comment_like`. canInteract union + getCommentLikeDailyRemaining wiring done in Phase 4 (role-dispatcher)
- [x] 2.7 `src/risk/pg-risk-store.ts`: updated inline `risk_counters` CHECK (fresh DBs) + added a guarded idempotent DO-block migration (existing DBs — only DROP+ADD when `comment_like` absent, avoids per-boot revalidate); `risk_interactions` CHECK left untouched

## 3. aidcp-edge — act path (edge executor + candidate harvest)

- [x] 3.1 `scrollNoteComments` harvests a final-viewport candidate list `{anchorId, author?, text, alreadyLiked}` (new `harvestCommentCandidates`) onto the success receipt; best-effort, empty reported truthfully
- [x] 3.2 `executeLikeComment(anchor)`: `getElementById` re-locate; finds `.interactions .like .like-wrapper`; post-verify `use` `#like`→`#liked` OR `.count` +1 → success only on confirmed
- [x] 3.3 Missing anchor → `no_target` (NO positional fallback); already-liked (`#liked`) pre-skip; no-flip → `state_unchanged`; fresh captcha recheck before click <!-- requestId NOT echoed: correlation is cloud-internal (single-flight), not on the wire -->
- [x] 3.4 `interaction.like_comment` command case: `thinkBefore(thinkMs)` + lognormal jitter only, calls `executeLikeComment`, reports typed result as action `comment_like`

## 4. aidcp-cloud — act path (appraiser + dispatch + frequency pre-gate)

- [x] 4.1 New role `CommentLikeAppraiser` (RoleName `comment_like_appraiser`) in `src/agents/comment-like-appraiser.ts`, registered behind the flag; triggers on the scroll_comments receipt via its OWN single-flight (subscribes `reading.scroll_comments` for noteId + `action.completed` for candidates); never touches reading.done
- [x] 4.2 Pre-gate (BEFORE the LLM): session `comment_likes` cap → `dailyRemaining('comment_like')` → ratio `(commentLikes+1)/max(1,noteLikes) ≤ 0.15` → Bernoulli (likeProbability 0.6); fail any → `comment_like.skipped`, no LLM, no budget touch
- [x] 4.3 LLM scores candidates (趣味性/知识深度/共鸣) over note body, picks 0-or-1; filters already-liked/anchorless; parse-failure or pick=0 → ABSTAIN (never default-pick); holds `{noteId,anchorId,text,author}` single-flight; emits `comment_like.intended`; on ok:true receipt emits `comment_like.confirmed`; interleaving guard drops stale pick on new note
- [x] 4.4 Dispatcher `comment_like.intended` → `canInteract('comment_like')` + `comment_likes`-budget honest-skip (no command, no decrement, log) → `comment_like` command with `thinkNow()`
- [x] 4.5 `comment_likes` added to `freshBudget` (cap 3); `consumeBudget('comment_like')` decrements ONLY on ok:true receipt; `comment_like` in `noRecoverScroll`; `sessionLikeCounts()` for the ratio
- [x] 4.6 Whole feature behind `AIDCP_COMMENT_LIKE` (default OFF): role not registered + intent subscriber inert when off

## 5. aidcp-cloud — valuable-comment corpus + composer

- [x] 5.1 `src/cache/valuable-comment-store.ts` (clone of liked-note-store): idempotent boot DDL `valuable_comments {dedup_key UNIQUE, comment_text, author, source_note_id, source_note_title, topics TEXT[] (GIN), reason, liked_at}`, insert-or-ignore, global retention cap (newest N) <!-- retention is global (not per-topic) for simplicity — bounds growth, the actual requirement; spec scenario reworded to "oldest rows" -->
- [x] 5.2 `ValuableCommentArchivist` (thin role): subscribes `comment_like.confirmed` ONLY (emitted by appraiser on ok:true receipt); archives from that event's correlated payload (text/author/anchor — receipt carries no text); keys by `topicKeysFromTitle(note.title)` (latin words + CJK bigrams, no LLM, no concept-pipeline dependency)
- [x] 5.3 `CommentComposer.getCorpusReferences(topics)` injects a "参考（仅作灵感，不可照抄）" block; empty/unavailable → prompt unchanged (composer derives topics via the same `topicKeysFromTitle`)
- [x] 5.4 `CommentComposedPayload.references` threaded so `CommentDeAiFlavor` sees the used references
- [x] 5.5 `CommentDeAiFlavor` overlap guard: `overlapsAny` (char-4gram Jaccard ≥0.5) → rewrite once (`rewriteAwayFrom`) → SKIP (`overlaps_reference`) if still overlapping (never loops, never ships a near-copy)
- [x] 5.6 PII/retention posture documented in the store header (only liked/public comments + handles stored; global retention cap; author stored raw — small corpus, low-stakes) <!-- if policy tightens, hash author -->

## 6. Acceptance red lines (aidcp-cloud + aidcp-edge)

> New `test/acceptance/comment-like.test.ts` (8 AC-CLIKE tests). Existing AC-PROTO bumped to 56 both repos.

- [x] 6.1 AC-PROTO: `ALL_TYPES.length === 56` both repos (passing); `interaction.like_comment` envelope valid; unions byte-identical
- [x] 6.2 AC-RISK (AC-CLIKE-RISK): `comment_like` is a separate action — own quota (normal 6), does NOT consume `like` (independent count), restricted-zeroed. <!-- handler-filter "records on ok:true" is covered by the server wiring + AC-RISK separation; the full handler→occurred→record path is integration-level, verified by reading + the separation test -->
- [~] 6.3 AC-EDGE: missing anchor → `no_target` (NO positional fallback), no-flip → `state_unchanged`. Verified BY READING the edge executor (DOM/CDP-bound; no CDP mock harness exists) + Phase-0 probe confirmed the real DOM contract. Real-machine E2E is the final check.
- [x] 6.4 AC-APPRAISER (AC-CLIKE-ABSTAIN): malformed output / pick=0 / all-already-liked → abstain, no intent, no LLM when pre-gate fails
- [x] 6.5 AC-NO-DEADLOCK: CommentReviewer still emits reading.done synchronously on the scroll receipt; the appraiser is a separate subscriber on its own single-flight (verified by design — reading.done path untouched; existing reading.done tests stay green)
- [x] 6.6 AC-FREQ (AC-CLIKE-RATIO): ratio gate blocks early-session (`(0+1)/1 > 0.15`) and skips the LLM; per-session cap is the hard limiter
- [~] 6.7 AC-CORPUS: archive-only-on-confirmed + dedup + retention are coded (store + archivist); PG-backed assertions deferred to real-machine (no in-test PG). topic-key + overlap helpers are unit-tested
- [x] 6.8 AC-COMPOSER (AC-CLIKE-OVERLAP): `overlapsAny` detects near-verbatim; empty/unavailable corpus → unchanged composing (optional closure)
- [x] 6.9 AC-MIGRATION: idempotent by construction (guarded DO-block only DROP+ADDs when `comment_like` absent; re-run is a catalog-lookup no-op)
- [x] 6.10 `npm run typecheck` + `npm run test:acceptance` + full `npm test` green BOTH repos (cloud 308/308, edge AC-PROTO 56)

## 7. Deploy (ECS — ordered, gated)

- [ ] 7.1 Dry-run the rsync scope and surface accumulated master scope before deploying (ECS ships full master)
- [ ] 7.2 HARD ORDERED: run the `risk_counters` CHECK ALTER on live ECS PG BEFORE service restart; then backup → rsync → restart → healthcheck
- [ ] 7.3 Enable the config flag conservatively (small per-session cap / low ratio / conservative quota tier); observe comment_like-vs-note-like ratio converging to ≈15% and watch `no_target` rates for selector drift
