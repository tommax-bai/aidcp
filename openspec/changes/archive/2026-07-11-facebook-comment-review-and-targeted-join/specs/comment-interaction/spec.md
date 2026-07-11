## ADDED Requirements

### Requirement: Facebook comments require human review by default

All Facebook comments — whether or not they carry contact info — SHALL pass the Feishu human-review gate before edge submit when `AIDCP_FB_COMMENT_REVIEW_ALL` is not the literal string `false` (default ON). The gate MUST fail closed: an unwired approval port, a review timeout, or a rejection MUST result in an honest non-submitting outcome (`compose_skipped` / `approval_rejected_or_timeout`) with no edge submit and no dedup mark. Contact comments keep their existing always-reviewed behavior and keep showing the contact line on the card; non-contact comments show only the comment body with no phantom trailing line.

#### Scenario: Non-contact FB comment waits for review by default
- **WHEN** a Facebook non-contact comment is composed and passes deterministic validation with `AIDCP_FB_COMMENT_REVIEW_ALL` unset
- **THEN** it MUST request Feishu approval and MUST NOT submit until approved

#### Scenario: Review rejected or unwired → honest no-submit
- **WHEN** the approval port is unwired, times out, or returns rejected for a Facebook comment
- **THEN** the run MUST audit `compose_skipped` with reason `approval_rejected_or_timeout` (or the unwired equivalent), MUST NOT call edge submit, and MUST NOT record the target as commented

#### Scenario: Reversible escape hatch restores auto-publish
- **WHEN** `AIDCP_FB_COMMENT_REVIEW_ALL=false`
- **THEN** a non-contact Facebook comment MAY submit directly after validation (today's behavior); contact comments still require review

#### Scenario: Shadow never reviews or submits
- **WHEN** Facebook comment shadow/dry-run mode is active
- **THEN** the run MUST short-circuit to the shadow outcome before requesting any human review and MUST NOT submit

#### Scenario: manualOverride bypasses quota but never review
- **WHEN** a Feishu `/comment` run sets `manualOverride` (operator authority) with review enabled
- **THEN** it MAY skip quota/risk/daily-cap gates but MUST still require Feishu review before submit — the human review is not bypassable by operator override

#### Scenario: Red-line reversal — non-contact FB comment auto-posts under default (forbidden)
- **WHEN** an implementation submits a non-contact Facebook comment without review while `AIDCP_FB_COMMENT_REVIEW_ALL` is unset
- **THEN** it MUST be treated as a violation and not merged
