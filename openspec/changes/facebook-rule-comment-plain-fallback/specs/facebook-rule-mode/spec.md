## ADDED Requirements

### Requirement: The rule round comment leg distinguishes contact comments from fallback plain comments

When a Facebook rule round reaches its comment stage for an account with no configured contact info, Cloud SHALL declare the plain-comment fallback explicitly and SHALL record the resulting comment as a distinguishable outcome. A confirmed fallback comment MUST NOT be projected as a confirmed contact comment.

The rule round SHALL preserve which of the two happened across restart and reconnect, and the account automation view, panel API and client MUST render the distinction. A stale or unreadable projection MUST be shown as unknown rather than resolved to either outcome.

Declaring the fallback SHALL NOT weaken any other gate: join and comment MUST each still pass their own just-in-time risk, session, daily, approval, dedupe and target gates, and the comment stage MUST still require a platform-confirmed `joined` or `already_member` result for the exact group.

#### Scenario: Fallback comment is not reported as a contact comment
- **WHEN** a rule round's comment stage posts a plain comment because the account has no contact info
- **THEN** the round records a fallback-comment outcome and the projection MUST NOT show a confirmed contact comment

#### Scenario: Contact comment keeps its own outcome
- **WHEN** a rule round's comment stage posts a comment with the account's configured contact info
- **THEN** the round records a contact-comment outcome distinct from the fallback outcome

#### Scenario: Fallback still requires confirmed membership
- **WHEN** the fallback is declared but the join stage returns pending, ambiguous, gated, failed or unconfirmed
- **THEN** the comment stage does not start and the round preserves the honest join outcome

#### Scenario: Fallback does not bypass approval
- **WHEN** the fallback comment's effective approval mode requires human review
- **THEN** the round waits for approval and MUST NOT post on the strength of the contact-comment lane's authorization

### Requirement: Rule-mode configuration surfaces the fallback consequence at write time

The Facebook rule-mode configuration write path SHALL accept an account with no configured contact info rather than rejecting it, and its authoritative readback SHALL carry a named note stating that this account's join-contact leg will fall back to a plain comment. The note SHALL be derived from server-side truth at read time and MUST NOT be cached client-side as a configuration value.

#### Scenario: Enabling rule mode without contact info is allowed but annotated
- **WHEN** an operator enables rule mode for a Facebook account that has no contact info configured
- **THEN** the write succeeds and the readback names the plain-comment fallback consequence

#### Scenario: Adding contact info clears the note
- **WHEN** contact info is later configured for that account
- **THEN** a subsequent readback no longer carries the fallback note
