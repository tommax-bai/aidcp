## Why

A human reading a note detail occasionally taps "like" on a comment that resonates — but the bot never does, making its detail-page behavior subtly non-human (it only likes the note itself). We want it to occasionally like another person's high-value comment, and to keep those good comments as raw material so its own future comments read more naturally. Phase-0 has confirmed on a real platform that this is buildable (per-comment like control + state signal located, comment anchors survive scrolling 100%).

## What Changes

- New anthropomorphic action: on a note detail page, occasionally LIKE one other person's comment (0-or-1 per visit), driven by an LLM value judgement over the note body + on-screen comments. Distinct from liking the note and from posting a comment.
- New cloud role **comment_like_appraiser** (LLM): scores candidate comments for value (interest / knowledge depth / resonance), picks 0-or-1, on its own single-flight that never blocks the deep-read loop.
- New cloud role **valuable-comment-archivist** (thin): persists only confirmed-liked comments into a corpus keyed by topic, which the comment composer later draws on as inspiration (never copied — routed through the existing de-AI / rewrite path).
- New **separate `comment_like` risk action**, governed by the existing single-writer risk controller with its own daily quota (default normal 6), counted apart from note-likes and excluded from the note like/view ratio gate.
- New edge action: re-locate a chosen comment by its stable anchor, click its like control, and post-verify the like actually registered (else honest `no_target` — never a positional fallback).
- New protocol message `interaction.like_comment` plus an optional candidate-comment list carried back on the existing comment-scroll receipt.
- New PostgreSQL store for the valuable-comment corpus (idempotent boot DDL, dedup, retention cap, stated PII posture).
- Frequency shaping so comment-likes stay ≈ 15% of note-likes, with the whole feature behind a config flag (default OFF).

## Capabilities

### New Capabilities
- `comment-like-interaction`: deciding whether/which comment to like on a note detail, the separate `comment_like` risk action and frequency budget, the targeting + post-verify contract, and the no-silent-fake-success / no-deadlock invariants.
- `valuable-comment-corpus`: persisting confirmed-liked valuable comments keyed by topic, and surfacing them to the comment composer as non-copied reference material with an anti-plagiarism guard.

### Modified Capabilities
<!-- None — this change adds new behavior in the detail-page window and a new store/composer input; it does not change the requirements of existing specs. -->

## Impact

- **aidcp-cloud**: protocol (`interaction.like_comment` + candidates field), command-bridge, risk (`RISK_ACTIONS` + quota tiers + counters CHECK migration + recording-filter fix + server side-effect guards), role-dispatcher (dispatch, frequency pre-gate, `comment_like` budget, no-recover-scroll), two new agent roles, the comment composer + de-AI flavor roles, a new PostgreSQL corpus store, config flag.
- **aidcp-edge**: protocol (byte-identical), comment-scroll candidate harvest, new `executeLikeComment` executor with DOM-first post-verify. Phase-0 probe script already added under `scripts/`.
- **aidcp (docs)**: `docs/protocol.md` message count + table.
- **Acceptance**: AC-PROTO no-drift, new AC-RISK for the separate action, edge no-target honesty, appraiser-abstain, no-deadlock, idempotent migration, corpus archive-only-on-confirmed, composer overlap guard.
- **Sequencing**: touches role-dispatcher / handler regions also edited by 4 active changes — land after they archive or rebase. ECS deploy ships full master; the counters CHECK migration is an ordered step before restart.
