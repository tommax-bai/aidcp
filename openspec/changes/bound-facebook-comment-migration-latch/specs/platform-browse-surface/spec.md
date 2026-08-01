## MODIFIED Requirements

### Requirement: Comment migration is receipt-driven and fail-closed

When the comment surface differs from the read surface, the cloud MUST migrate to detail in two receipt-driven steps: emit a navigate-purpose open, wait for its action-completed with a detail-surface observation and matching note id, and only then emit the comment. If the navigate step fails, the cloud MUST NOT emit the comment and MUST report the approved-not-delivered comment to the operator. When the comment surface equals the read surface, migration MUST be structurally unreachable and no extra open is emitted.

The pending state that holds the approved comment between the two steps MUST have a bounded, correlated lifecycle. Three properties are required, and each is separately load-bearing:

**Consumption MUST be correlated.** An open receipt MUST be admitted to the migration branch only when it correlates with the migration that armed the pending state — at minimum, the same note id. A non-correlating open receipt MUST NOT clear the pending state, MUST NOT cause the approved comment to be discarded, and MUST NOT produce a failure attribution for this migration. Correlation and landing are separate judgements and MUST NOT be merged: correlation decides whether this receipt concerns this migration, landing decides whether that migration succeeded. Merging them turns "correlated but failed to land" into "not correlated", which leaves the pending state armed forever.

**Clearing MUST NOT precede the judgement.** The pending state MUST be cleared only after the receipt has been judged to concern this migration. Clearing first and judging afterwards is not permitted even where the judgement is present, because the approved comment is already gone by the time the judgement runs.

**Every approved delivery MUST have a bounded terminal outcome.** The bounded timeout that clears the pending state and reports to the operator MUST cover every approved delivery, not only deliveries carrying an auto-approval trace. Where a delivery has no such trace, it MUST still be armed, MUST still be cleared on expiry, MUST still report the approved-not-delivered comment to the operator, and MUST still emit its terminal event so the comment subline's clock resumes. Arming only the traced path leaves ordinary approved deliveries with no terminal outcome at all: the pending state stays armed, the subline clock never resumes, and the operator is never told the comment was not delivered.

The comment subline's own hard expiry and the pending state MUST terminate together. Where the subline declares the comment over, the pending state MUST be cleared in the same step and the operator MUST be informed; leaving it armed after the subline has ended means a later unrelated receipt can fail an already-expired migration a second time.

#### Scenario: Navigate failure does not send the approved comment elsewhere

- **WHEN** the navigate-purpose open for an approved comment fails to land on the target detail
- **THEN** the comment is not emitted on the current page
- **AND** the approved-not-delivered comment is reported to the operator

#### Scenario: Unrelated open receipt leaves the migration untouched

- **WHEN** an open receipt arrives for a different note while a migration is pending
- **THEN** the pending state remains armed and the approved comment is not discarded
- **AND** no failure is attributed to this migration on the basis of that receipt
- **AND** the receipt continues down its ordinary handling path

#### Scenario: Correlated receipt that failed to land is still consumed

- **WHEN** an open receipt correlates with the pending migration but reports failure or a non-detail surface
- **THEN** it is consumed, the pending state is cleared, and the migration is reported as failed
- **AND** it is not treated as uncorrelated and left pending

#### Scenario: Ordinary approved delivery has a bounded terminal outcome

- **WHEN** an approved delivery without an auto-approval trace is dispatched and no receipt arrives within the bounded budget
- **THEN** the pending state is cleared, the approved-not-delivered comment is reported to the operator, and the terminal event is emitted
- **AND** the comment subline's clock resumes

#### Scenario: Subline expiry and pending state terminate together

- **WHEN** the comment subline reaches its hard expiry while a migration is still pending
- **THEN** the pending state is cleared in the same step and the operator is informed
- **AND** a later unrelated open receipt does not produce a second failure for that migration

#### Scenario: Arming over an occupied pending state is reported

- **WHEN** a new approved delivery is armed while a pending migration is already held
- **THEN** the condition is reported honestly rather than silently overwriting the held delivery
