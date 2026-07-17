## MODIFIED Requirements

### Requirement: Slow-network comment submission must not spuriously time out into a duplicate

A slow-but-successful Facebook automatic comment submission MUST NOT be abandoned by a cloud-side step timeout that fires before the edge returns its own-identity verification receipt: a bare timeout leaves the post un-deduplicated, so the same target is re-posted on the next round and a duplicate comment goes live. The cloud comment step timeout SHALL therefore be derived from the composition length (plus fixed post-submit and round-trip margins, with a ceiling), rather than a single flat value, so the edge's real receipt — confirmed success or verification-ambiguous, both of which mark dedup — reaches the cloud before it gives up. A comment attempt that genuinely never submitted (a hard failure such as editor-not-found or focus failure) returns a non-timeout reason, is not dedup-marked, and remains eligible for a legitimate retry.

This single allowance covers the humanized per-character typing **plus the edge's post-submit in-place confirmation window**. Any change that enlarges the edge's post-submit confirmation budget MUST be re-reckoned against this timeout: if the edge's total post-submit spend can exceed the derived allowance, the cloud records a bare `timeout`, dedup is not marked, and the next round posts a real duplicate — the exact hole this requirement exists to close.

#### Scenario: Long comment on a slow link is not spuriously timed out into a duplicate
- **WHEN** a long comment is dispatched for submission on a slow connection
- **THEN** the step timeout is sized to cover the humanized per-character typing plus the post-submit in-place confirmation window (base + per-character + margin, capped), so the edge's receipt marks dedup and the same target is not re-posted next round

#### Scenario: Shorter comment keeps the standard step timeout floor
- **WHEN** a short comment is dispatched for submission
- **THEN** the derived timeout is at least the standard step timeout floor and never shorter than the flat baseline

#### Scenario: A genuine non-submission stays retryable
- **WHEN** a comment attempt fails before submission (editor not found / focus failure)
- **THEN** it returns a non-timeout reason, is not marked as posted, and remains eligible for a legitimate retry rather than being silently suppressed

#### Scenario: Enlarging the edge confirmation budget is re-reckoned against this timeout
- **WHEN** the edge's post-submit confirmation budget is changed
- **THEN** the total post-submit spend is verified to stay within the derived step timeout, so a slow-but-successful submission still returns a dedup-marking receipt instead of timing out into a duplicate
