## ADDED Requirements

### Requirement: The joined-group ledger is an allowed comment-container source under a per-account gate

The Facebook comment pipeline SHALL accept, for an account whose joined-group coverage is enabled, the account's own joined groups (from the membership ledger, `status='joined'`) as the container source, in addition to the existing operator-configured container list. This substitution SHALL be controlled per account and MUST NOT change the unattended compose/validate/server-confirmed-verify mechanics, MUST NOT weaken the contact-forbidden invariant on the unattended path, and MUST keep the fail-closed behavior (no keywords or no eligible joined groups yields an honest no-op).

#### Scenario: Coverage-enabled account sources containers from the ledger
- **WHEN** a Facebook account has joined-group coverage enabled
- **THEN** the comment pipeline draws its container from that account's `joined` membership rows and otherwise runs the unchanged compose/validate/verify path

#### Scenario: No joined groups yields a no-op
- **WHEN** a coverage-enabled account has no joined groups yet
- **THEN** the trigger records/returns a no-targets outcome and does not fall back to whole-site search
