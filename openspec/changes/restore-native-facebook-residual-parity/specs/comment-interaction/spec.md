## ADDED Requirements

### Requirement: An unobserved engagement metric is not a below-threshold verdict

The deterministic engagement threshold that gates ordinary commenting MUST distinguish a measured metric from an unobserved one. When the edge reports a note whose engagement metric is explicitly marked as not observed, or when the metric is otherwise absent rather than measured, the cloud MUST NOT classify the note as below threshold and MUST NOT count it as evidence of low content quality. It MUST instead skip with a distinct, auditable reason that names the unavailable metric, so a platform-wide reading failure is visible as a reading failure rather than as normal threshold filtering.

The threshold values themselves MUST NOT be relaxed by this distinction: an unobserved metric MUST NOT be treated as satisfying the threshold, and the note MUST NOT be promoted to LLM appraisal on the strength of a metric nobody measured. A genuine measured zero MUST continue to be treated as below threshold.

#### Scenario: Unobserved reaction count is reported as an unavailable metric

- **WHEN** an appraised note's reaction count is marked not observed by the edge
- **THEN** the cloud skips the note with a reason naming the unavailable reaction metric
- **AND** it does not emit a below-threshold reason and does not call the appraisal model

#### Scenario: Measured zero is still below threshold

- **WHEN** an appraised note carries a measured reaction count of zero with no not-observed marker
- **THEN** the cloud skips the note with the existing below-threshold reason
- **AND** the threshold values are unchanged

#### Scenario: Unobserved metric does not open the gate

- **WHEN** every note in a session reports an unobserved reaction count
- **THEN** no note passes the deterministic threshold on the strength of the missing metric
- **AND** the unavailable-metric reason makes the platform-wide reading failure visible for triage
