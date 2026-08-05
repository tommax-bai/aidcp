## ADDED Requirements

### Requirement: The process that runs group commenting can read the group-comment policy

The runtime process that actually executes coverage comments and consumption comments SHALL be able to read the authoritative Facebook group-comment timing policy (`joinToFirstCommentHours` and the independent same-group re-comment cooldown) at selection time. A deployment topology in which the policy is owned by one service while the commenting loop runs in another SHALL provide that other service a first-class read path; the commenting side MUST NOT be shipped with the policy permanently absent.

When the policy is genuinely unreadable — never loaded, mirror stale, or the source service unreachable — selection MUST fail closed with the existing named blocker and MUST NOT substitute a default interval. A substituted default would make "the policy has not arrived yet" and "operations configured exactly this" indistinguishable at the moment a comment is submitted.

An unreadable policy MUST NOT halt unrelated action segments. It SHALL hold only the comment obligation it actually gates; browsing, likes and joins for the same account SHALL continue. A capability that a process cannot perform MUST NOT be able to become a durable, cross-restart halt of that account's whole automation.

Any process that ships without this read path SHALL state the full blast radius at startup, not only the part that is obvious. Recording "no coverage comment will be sent from this process" while the same absence also stops likes and joins is an incomplete disclosure that hides a production halt.

#### Scenario: Commenting process reads the policy it needs

- **WHEN** the coverage or consumption comment loop reaches target selection in a process that does not own the policy table
- **THEN** it obtains the current `joinToFirstCommentHours` and re-comment cooldown through its own read path
- **AND** it pins that revision with the selected group exactly as an owning process would

#### Scenario: Stale mirror still fails closed

- **WHEN** the read path exists but the mirrored policy is stale or absent
- **THEN** selection returns the named policy-unavailable blocker
- **AND** it MUST NOT fall back to the default interval or to any previously cached value presented as current

#### Scenario: Unavailable policy does not stop likes and joins

- **WHEN** a comment obligation is held by the policy-unavailable blocker
- **THEN** the same account continues to accumulate confirmed views, like opportunities and join opportunities
- **AND** the halt MUST NOT persist across process restarts as a whole-account stop

#### Scenario: Deliberate absence discloses its full blast radius

- **WHEN** a process is deliberately deployed without the policy read path
- **THEN** its startup record names every segment the absence stops, not only the comment segment
