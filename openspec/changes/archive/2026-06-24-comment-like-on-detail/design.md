## Context

The cloud is an event-driven multi-agent orchestrator; the detail-page deep-read pipeline runs note-quality → image-read → comment-scroll → note-interaction (like/collect) → (comment-post branch ‖ author-visit) → back-to-feed. Liking another person's comment does not exist anywhere today: the only like action targets the note's own engage-bar, and comments reach the cloud as text with no re-locatable handle. The risk controller is the single writer of account interaction state; pacing is centralized in the cloud; the edge only executes atomic actions and must never silently fake success.

This change was designed over two adversarially-reviewed design passes. A Phase-0 real-machine probe (`aidcp-edge/scripts/comment-like-probe.ts`, run 2026-06-21) resolved the two make-or-break unknowns:
- Per-comment like control = `#comment-<id> .interactions .like .like-wrapper`; liked-state signal = the icon `use` flips `#like`→`#liked` AND the count increments (the `like-active` class is a constant base class, NOT the signal).
- Comment anchors survive heavy comment-section scrolling at 100% (20/20 still resolvable by id after loading 57 more) — XHS does not virtualize/unmount comment rows.

That second result is load-bearing: it validates a "cloud picks a comment → edge re-locates by anchor and likes it" round-trip, rather than forcing a same-pass like during scrolling.

## Goals / Non-Goals

**Goals:**
- Occasionally like one high-value other-person comment per detail visit, by LLM value judgement over note body + comments.
- Keep comment-likes a realistic minority (≈15% of note-likes) and under an independent, honestly-recorded risk budget.
- Persist confirmed-liked comments as a topic-keyed corpus that improves the bot's own future comments without plagiarism.
- Preserve all existing invariants: single-writer risk, no fake success, no deadlock, byte-identical protocol, centralized pacing.

**Non-Goals:**
- Liking multiple comments per visit, replying to comments, or liking comments outside the detail-read window.
- A human-approval gate for comment-likes (low-stakes, unlike posting public text).
- Embedding/semantic corpus retrieval — keyword/topic match only for now.
- Merging comment-likes into the note like footprint or the like/view ratio gate.

## Decisions

**1. Two new roles, split (appraiser vs archivist).** The value judgement (LLM) and the persistence (thin, no-LLM) are distinct responsibilities, matching the one-decision-one-role granularity. The appraiser is named `comment_like_appraiser` to avoid collision with the existing `comment_appraiser` (which decides whether to POST a comment). *Alternative rejected:* folding both into one role — mixes an LLM decision with a side-effecting writer and muddies the no-archive-without-confirmed-like rule.

**2. Appraiser owns its own single-flight off the comment-scroll receipt; reading-done is untouched.** The comment-reviewer still emits reading-done synchronously; the appraiser merely also observes the same receipt (which now carries the candidate list) and runs in parallel. *Alternative rejected:* deferring reading-done until the comment-like resolves — the reviewer has no timeout, so a dropped like receipt would deadlock the loop until the idle watchdog fires a feed scroll that navigates the page away.

**3. LLM appraiser, not a rule-only picker.** The decision is a genuine value judgement (interest / knowledge-depth / resonance) over the note body + comments, and the same judgement doubles as the corpus harvest signal, so the per-visit LLM cost is justified. A cheap pre-gate (cap → ratio → random abstain → daily quota) runs first so the LLM is only invoked on visits that could actually like — bounding cost and removing the every-visit token spend.

**4. Separate `comment_like` risk action, not merged into `like`.** A comment-like and a note-like are different observable actions; modeling them separately gives comment-likes their own quota and keeps them out of the note like/view ratio gate, which is what the product wants. The risk machinery is generic over the action set, so degradation, restricted-state zeroing, and captcha gating are inherited for free. *Cost:* the action set widening is compile-enforced across the quota literals — and the recording filter that string-matches actions would silently drop the new one unless taught about it (the red-line fix). *Alternative rejected:* normalizing comment-likes to `like` — would inflate the note-like count and the ratio gate, contrary to the decision.

**5. Frequency = count ratio, shaped in the pre-gate, not the quota tiers.** The "≈15% of note-likes" target is a soft shaper (ratio knob vs this-session note-like count) plus a per-session hard cap; the risk quota tiers remain the absolute daily ceiling. Early-session zero-fire is accepted and specified, with the per-session cap as the real limiter.

**6. Stable-anchor targeting with post-verify; never index.** Phase-0 confirmed anchors survive scrolling, so the edge re-locates by `getElementById` and verifies the `#like`→`#liked` flip and/or count increment before reporting success; a missing anchor is `no_target` with no positional fallback. The post-verify mirrors the existing note-like executor's `#liked` check, scoped to the comment row.

**7. Dedicated protocol message + optional candidates field.** A new `interaction.like_comment` (carrying a request id + the stable anchor) keeps the edge executor switch unambiguous versus note-like; the candidate comments ride back as an optional field on the existing comment-scroll receipt (count-neutral for that direction). Both protocol files stay byte-identical; the message count is computed at apply time, never hardcoded.

**8. Corpus is one combined change but internally phased + flag-gated.** The user chose to ship the act path and the corpus together. To contain blast radius, the corpus/composer work is the last internal phase, the whole feature is behind a default-OFF flag, and the corpus archives only on the confirmed-like receipt — correlated from the appraiser's single-flight state (the receipt carries no comment text), with an interleaving guard.

**9. Anti-plagiarism is structural, not prompt-only.** Corpus references are injected as optional "inspiration, do not copy" context, and a near-verbatim overlap guard in the de-AI/rewrite step rewrites once then skips — so a near-copy can never ship and the guard never loops.

## Risks / Trade-offs

- [Recording filter silently drops `comment_like`] → Treat as a red-line: the filter + recording-action union must learn the new action atomically with adding it; guarded by an acceptance test asserting a confirmed comment-like is recorded.
- [Combined A+B inflates blast radius across protocol+risk+PG+composer] → Internal phasing, default-OFF flag, staged deploy; the corpus phase lands last and is independently revertible by the flag.
- [Concept-key race → corpus rows unretrievable by topic] → Deterministic fallback key (note-title hash) when concepts are empty, so rows are never orphaned.
- [Anchor stale at like time] → Phase-0 measured 100% survival, but the edge still honestly reports `no_target` (never a positional fallback) and the cloud records nothing; the no_target rate is observable.
- [Concurrent WIP / 4 active changes touch the same dispatcher & handler regions] → Re-ground every cited symbol at apply time (not line numbers), stage files explicitly, and land after those changes archive or rebase onto them.
- [PII: storing other users' comment text + author handles] → Bounded retention cap and a stated retention/redaction posture; archive only liked (already public) comments.
- [LLM cost on the hottest loop] → Cheap pre-gate runs before the LLM so it is invoked only on like-eligible visits.

## Migration Plan

1. Protocol + risk plumbing: add `interaction.like_comment` (both protocol files byte-identical, count N→N+1 at apply time, both AC-PROTO tests, docs), command-bridge mapping, the `comment_like` action + all quota literals, the recording-filter fix + server side-effect guards, and the idempotent `risk_counters` CHECK ALTER. Run AC-PROTO / AC-RISK then full test + typecheck in both repos.
2. Act path: edge `executeLikeComment` (re-locate / click / post-verify / no_target honesty / echo request id) + comment-scroll candidate harvest; cloud `comment_like_appraiser` (own single-flight, pre-gate, parse-failure abstain) + dispatch + `commentLikes` budget + no-recover-scroll entry. Behind the default-OFF flag.
3. Corpus + composer: PostgreSQL store (idempotent boot DDL, dedup, retention), `valuable-comment-archivist` (archive on confirmed ok only, correlated), composer reference injection + de-AI overlap guard.
4. Acceptance red lines, then staged deploy: **run the `risk_counters` CHECK ALTER on live ECS PG BEFORE service restart** (ordered step; ECS deploy ships full master — surface accumulated scope first), then enable the flag conservatively and watch comment_like-vs-note-like ratio and no_target rates.

Rollback: flip the config flag OFF (disables appraisal/dispatch); the additive protocol message, action, and table are inert when unused.

## Open Questions

- Default tuning to confirm before activation: per-session comment-like cap, Bernoulli abstain probability, and ratio (0.15). Daily quota tiers proposed conservative 3 / normal 6 / aggressive 12.
- Candidate harvest scope: final-viewport snapshot (freshest anchors) is the default; confirm whether a larger accumulated set is ever needed.
- Corpus retention cap value and whether author handles are stored raw or hashed.
- Request-id correlation lifetime / eviction if a like receipt never returns, and that the archivist tolerates that eviction.
