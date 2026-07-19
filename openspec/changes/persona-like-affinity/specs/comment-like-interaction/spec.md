## MODIFIED Requirements

### Requirement: Frequency budget keeps comment-likes a minority of note-likes

The number of comment-likes SHALL stay approximately 15% of the session's note-like count. This SHALL be enforced by a cheap pre-gate evaluated BEFORE invoking the LLM appraiser, combining: a per-session hard cap, a configurable ratio knob (default 0.15 against the observed note-like count this session), a persona-affinity Bernoulli gate, and remaining daily `comment_like` quota. The Bernoulli allow probability SHALL be monotonic by `behavior_guidelines.like_affinity`: `normal=0.60`, `like_more=0.75`, `like_most=0.90`; a missing field SHALL equal `normal`. This affinity gate only changes how often an eligible candidate reaches the persona-derived LLM value judgement. It MUST NOT bypass candidate filtering, the ratio/cap/daily-quota gates, risk control, or confirmed-success accounting, and MUST NOT guarantee a comment-like. Firing zero comment-likes early in a session (when few note-likes have accrued) remains expected behavior, not a fault.

#### Scenario: Pre-gate short-circuits before the LLM

- **WHEN** the per-session cap is exhausted, the ratio would be exceeded, the affinity Bernoulli abstain triggers, or the daily `comment_like` quota is depleted
- **THEN** the appraiser LLM is NOT invoked and the visit likes no comment, with no budget decremented

#### Scenario: Higher affinity raises only Bernoulli eligibility

- **WHEN** otherwise identical accounts use `normal`, `like_more`, and `like_most`
- **THEN** their Bernoulli allow probabilities are respectively 0.60, 0.75, and 0.90, while every other quality and safety gate remains identical

#### Scenario: High affinity still abstains and never bypasses hard gates

- **WHEN** a `like_most` account has no valuable candidate, exceeds the 15% ratio, exhausts quota, is risk-blocked, or its random draw falls in the remaining 10% abstain range
- **THEN** no comment-like is dispatched or counted; `like_most` MUST NOT be treated as a force-like instruction

#### Scenario: Early-session zero-fire

- **WHEN** fewer than a handful of note-likes have occurred this session
- **THEN** the ratio gate yields effectively zero and no comment-like fires regardless of affinity

#### Scenario: Converges to the target ratio

- **WHEN** a session accumulates many note-likes
- **THEN** comment-likes remain at or below approximately 15% of note-likes and never exceed the per-session cap regardless of affinity
