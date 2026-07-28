## MODIFIED Requirements

### Requirement: Comment migration is receipt-driven and fail-closed

When the comment surface differs from the read surface, the cloud MUST migrate to detail in two receipt-driven steps: emit a navigate-purpose open, wait for its action-completed with a detail-surface observation and matching note id, and only then emit the comment. If the navigate step fails, the cloud MUST NOT emit the comment and MUST report the approved-not-delivered comment to the operator. When the comment surface equals the read surface, migration MUST be structurally unreachable and no extra open is emitted.

The navigate-purpose open MUST carry enough targeting for the executing side to actually navigate without inferring the target from the current page: a canonical target the platform can navigate to (for platforms whose note identity is itself a canonical permalink, that identity suffices) or an explicit address. The cloud MUST NOT rely on a purpose marker alone to change the executing side's behavior.

The migration wait MUST be bounded and self-clearing **for every approved delivery**, not only for deliveries that carry a pre-authorized approval trace. The cloud MUST clear it on a bounded timeout, on session end, and on disconnection, and each of those MUST report the approved-not-delivered comment to the operator rather than leaving the wait armed.

An armed wait MUST only be **consumed** by a receipt correlated to the migration that armed it. Requiring correlation before treating a receipt as a successful landing is necessary but not sufficient: an uncorrelated receipt MUST NOT enter the wait's resolution path at all, because consuming the wait on an uncorrelated receipt disarms it and attributes this migration's failure to an unrelated command, which destroys the audit trail for the real cause. A cleared or never-armed wait MUST NOT be resolvable by a later receipt.

#### Scenario: Navigate failure does not send the approved comment elsewhere

- **WHEN** the navigate-purpose open for an approved comment fails to land on the target detail
- **THEN** the comment is not emitted on the current page
- **AND** the approved-not-delivered comment is reported to the operator

#### Scenario: Migration command carries a navigable target

- **WHEN** the cloud emits a navigate-purpose open for an approved comment on a platform whose read and comment surfaces differ
- **THEN** the command carries a canonical target the executing side can navigate to
- **AND** the purpose marker is not the only field the executing side would have to honour to reach the right page

#### Scenario: Migration wait cannot dangle for an ordinary approved comment

- **WHEN** a migration wait is armed for an approved comment that carries no pre-authorized approval trace, and no correlated receipt arrives within its bound
- **THEN** the cloud clears the wait and reports the approved-not-delivered comment to the operator
- **AND** no comment is emitted and the cleared wait is not resolvable by any later receipt

#### Scenario: Uncorrelated receipt neither releases nor disarms the wait

- **WHEN** an armed migration wait is followed by an open receipt belonging to a different note or a different orchestration step
- **THEN** the cloud does not treat that receipt as migration confirmation and emits no comment
- **AND** the wait is not disarmed by it and this migration's eventual failure is not attributed to that unrelated receipt
