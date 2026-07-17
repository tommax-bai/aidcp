## MODIFIED Requirements

### Requirement: Note-scoped action support is declared per platform and gated at one point

The cloud registry MUST declare, for every platform, whether each note-scoped action (`read_content`, `like`, `collect`, `comment`, `comment_like`, `browse_images`, `scroll_comments`) is supported, as a fully-covered mapping so the type checker forces every cell to be stated. Every unsupported action MUST carry a non-empty reason. A single dispatch wrapper MUST be the only place that **gates dispatch** on this support: when an action is unsupported for the connected platform, the command MUST NOT be dispatched and the refusal MUST be audited with its reason. Support MUST NOT be inferred from numeric coincidence (for example a metric that happens to be zero).

Additional consumers MAY read the declaration **only for non-gating purposes** — for example projecting what the client is told it may do. Such a consumer MUST NOT dispatch, refuse, or cancel any command, MUST NOT be relied on as an enforcement point, and MUST NOT be the reason any refusal goes unaudited. Every non-gating consumer MUST fail open: a platform-resolution miss or a lookup exception MUST fall back to the behaviour that existed before that consumer was added, so a supported platform never loses capability because a read-only consumer's lookup failed.

#### Scenario: Facebook collect is refused explicitly, not by coincidence

- **WHEN** the interaction appraiser requests both a like and a collect for a Facebook note
- **THEN** the like is dispatched and the collect is refused at the single dispatch gate with its declared reason
- **AND** the refusal does not depend on Facebook's collect metric being zero

#### Scenario: Unsupported deep-read actions are not dispatched

- **WHEN** the platform declares `browse_images` or `scroll_comments` unsupported
- **THEN** those commands are never dispatched to the edge
- **AND** no round-trip or model call is spent producing a command that the edge would only reject

#### Scenario: A non-gating consumer reads the declaration without becoming a second gate

- **WHEN** a read-only consumer such as the client usage-cap projection reads note-scoped action support
- **THEN** it MAY shape what it reports to the client
- **AND** it MUST NOT dispatch, refuse, or cancel any command
- **AND** the single dispatch wrapper remains the only audited refusal point

#### Scenario: A non-gating consumer's lookup fails

- **WHEN** a non-gating consumer's platform resolution or support lookup misses or throws
- **THEN** it MUST fall back to the behaviour that existed before that consumer was added
- **AND** a supported platform never loses capability because a read-only lookup failed
