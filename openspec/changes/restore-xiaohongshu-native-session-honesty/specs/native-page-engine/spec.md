## ADDED Requirements

### Requirement: Session-open admission limits SHALL be reconciled per platform lane, not per platform

The mechanical reconciliation guard over the session-open timeout chain SHALL cover every platform lane the engine admits, and MUST fail when the set of platforms special-cased in the engine's admission diverges from the set of lanes the guard covers.

The engine's entry admission for `session.open` accepts a host-supplied timeout. That timeout travels through a chain of independently declared limits — the host's requested value, the host's own admission check, the host's session timeout, the engine's per-command ceiling, and the engine's protocol admission — and the chain is split across two languages that share no build. None of these divergences produce a compile error and none are visible to `typecheck`.

**A timeout that exceeds the engine's protocol admission is rejected at the door, so the failure is not "one command is slower than expected" but "no command on that platform can be issued at all".** The whole platform goes dark while every other signal (process alive, transport connected) stays green.

The mechanical reconciliation guard over this chain MUST cover **every platform lane the engine admits**, not one named platform. Specifically:

- For each lane, the guard SHALL assert the requested value passes both the host admission and the engine ceiling.
- For each lane, the guard SHALL assert the session timeout passes both the host admission and the engine protocol admission.
- For each lane, the guard SHALL assert the session timeout is not smaller than any command ceiling it can clamp, since the engine derives a command budget as `session_timeout.min(ceiling)` and a smaller session value silently clamps the ceiling back with no error and no log.

**The set of platforms special-cased in the engine's admission MUST correspond one-to-one with the set of lanes the guard covers, and the guard MUST fail when they diverge.** A guard that enumerates lanes by hand is a hand-copied list: it stays green precisely when a new platform lane is added and left uncovered, which is the condition under which the next outage occurs. Raising a single constant without closing this correspondence relocates the defect to the next platform rather than removing it.

#### Scenario: Non-Facebook session open is admitted at the value the host actually sends
- **WHEN** the host opens a session for a non-Facebook platform using its default session timeout
- **THEN** the engine admits it and proceeds to endpoint connection
- **AND** the session is not rejected as an invalid request

#### Scenario: A platform lane added to engine admission without a guard lane fails the guard
- **WHEN** a new platform is special-cased in the engine's session-open admission
- **AND** no corresponding lane is added to the reconciliation guard
- **THEN** the guard fails, naming the uncovered platform

#### Scenario: Raising one lane's session timeout past its engine admission fails the guard
- **WHEN** any lane's session timeout is raised above the engine protocol admission for that lane
- **THEN** the guard fails before the change can ship, rather than the platform going dark at runtime
