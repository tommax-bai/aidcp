# comment-like-interaction Specification

## Purpose
TBD - created by archiving change comment-like-on-detail. Update Purpose after archive.
## Requirements
### Requirement: Occasional comment-like decision on note detail

During the detail-page comment-reading window (after the comment section has been scrolled on-screen and before any note-level interaction fires), the system SHALL occasionally select at most ONE other person's comment to like, based on an LLM value judgement over the note body and the on-screen candidate comments. Most visits SHALL abstain. The selection SHALL exclude the bot's own comment, any already-liked comment, and any comment without a usable anchor.

#### Scenario: Picks a single high-value comment
- **WHEN** the pre-gate allows a comment-like this visit and at least one candidate comment qualifies
- **THEN** the appraiser selects exactly one comment (never two or more) judged most worth liking by interest / knowledge-depth / resonance

#### Scenario: Abstains when nothing is worth liking
- **WHEN** no candidate comment qualifies (all already-liked, anchorless, own, or low value)
- **THEN** the visit likes no comment and emits no like command

#### Scenario: Never targets own or already-liked comments
- **WHEN** the candidate list includes the bot's own just-posted comment or a comment already in the liked state
- **THEN** those candidates are filtered out before selection

### Requirement: Frequency budget keeps comment-likes a minority of note-likes

The number of comment-likes SHALL stay approximately 15% of the session's note-like count. This SHALL be enforced by a cheap pre-gate evaluated BEFORE invoking the LLM appraiser, combining: a per-session hard cap, a configurable ratio knob (default 0.15 against the observed note-like count this session), a random abstain, and remaining daily `comment_like` quota. Firing zero comment-likes early in a session (when few note-likes have accrued) is expected behavior, not a fault.

#### Scenario: Pre-gate short-circuits before the LLM
- **WHEN** the per-session cap is exhausted, the ratio would be exceeded, the random abstain triggers, or the daily `comment_like` quota is depleted
- **THEN** the appraiser LLM is NOT invoked and the visit likes no comment, with no budget decremented

#### Scenario: Early-session zero-fire
- **WHEN** fewer than a handful of note-likes have occurred this session
- **THEN** the ratio gate yields effectively zero and no comment-like fires

#### Scenario: Converges to the target ratio
- **WHEN** a session accumulates many note-likes
- **THEN** comment-likes remain at or below ≈15% of note-likes and never exceed the per-session cap

### Requirement: Separate comment_like risk action under single-writer control

Comment-likes SHALL be governed by the risk controller as a SEPARATE action distinct from note-likes, with its own daily quota tiers (conservative / normal / aggressive) and its own counting. A comment-like SHALL be recorded ONLY upon a confirmed successful like. Comment-likes SHALL NOT be counted toward the note-like total and SHALL NOT affect the note like/view ratio gate. Account status degradation (warned / restricted / frozen) and captcha-restricted interaction gating SHALL apply to the action.

#### Scenario: Recorded on confirmed success only
- **WHEN** the edge reports a comment-like succeeded (post-verified)
- **THEN** the risk controller records exactly one `comment_like` (not a note-like), and nothing is recorded on failure, no-target, or abstain

#### Scenario: Does not contaminate note-like accounting
- **WHEN** a comment-like is recorded
- **THEN** the note-like daily count is unchanged and the note like/view ratio gate's decision for the next note-like is unaffected

#### Scenario: Blocked under restricted/frozen and on quota exhaustion
- **WHEN** the account is restricted or frozen, or the daily `comment_like` quota is exhausted
- **THEN** the comment-like is honestly skipped — no command is dispatched and no budget is decremented

### Requirement: Anchor-based targeting with post-verify and no fake success

The edge SHALL re-locate the chosen comment by its stable anchor and act on that specific comment's like control, then post-verify the like actually registered (the per-comment like state flips to the liked signal and/or its count increments) before reporting success. If the anchor can no longer be found, the edge SHALL report `no_target` and SHALL NOT fall back to whatever comment now occupies that position. A click that does not change the like state SHALL be reported as state-unchanged, never as success.

#### Scenario: Successful like is post-verified
- **WHEN** the anchored comment is found and its like state flips to liked (and/or count increments) after the click
- **THEN** the edge reports success and the cloud records the `comment_like`

#### Scenario: Missing anchor reports no_target without positional fallback
- **WHEN** the chosen comment's anchor cannot be located at like time
- **THEN** the edge reports `no_target` and likes nothing — it does not like the comment now at that position

#### Scenario: Non-registering click is not success
- **WHEN** the like control is clicked but the like state does not change
- **THEN** the edge reports state-unchanged and the cloud records nothing

### Requirement: Comment-like never blocks the deep-read loop

The comment-like decision SHALL run on its own single-flight and SHALL NOT defer or block emission of the reading-done signal. The note-like, author-visit, and return-to-feed chain SHALL proceed regardless of the comment-like outcome — success, failure, abstain, or a dropped/late like receipt.

#### Scenario: Reading-done always proceeds
- **WHEN** the appraiser abstains, stalls, or its like receipt is dropped
- **THEN** reading-done still fires and the downstream note-like / author / back-to-feed chain is unaffected

### Requirement: Appraiser parse-failure abstains

On malformed or unparseable LLM output the appraiser SHALL abstain — emit no like command and decrement no budget — and SHALL NOT default to an arbitrary candidate.

#### Scenario: Malformed output yields abstention
- **WHEN** the appraiser's LLM output cannot be parsed into a valid selection
- **THEN** the visit likes no comment and no budget is touched

### Requirement: Centralized pacing, gated rollout

The comment-like command SHALL carry a cloud-computed hesitation (thinkMs) and SHALL NOT carry a page-leave dwell directive; the edge SHALL add only its lognormal jitter and SHALL NOT introduce its own timing. The whole feature SHALL be gated behind a configuration flag that defaults to OFF.

#### Scenario: Hesitation comes from cloud, jitter from edge
- **WHEN** a comment-like command is dispatched
- **THEN** it carries thinkMs only, and the edge waits thinkMs plus lognormal jitter before clicking

#### Scenario: Flag off disables the feature
- **WHEN** the config flag is off
- **THEN** no comment-like is ever appraised or dispatched

