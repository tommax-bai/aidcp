## MODIFIED Requirements

### Requirement: Navigate-purpose open does not report a decision note

When a note-open command carries the navigate purpose, the edge MUST only bring the browser to the target detail and MUST NOT report a decision note.detail (which would overwrite real reaction counts with zero). It MUST instead return an action-completed receipt carrying the independent observation and the page-derived canonical post id.

"Bring the browser to the target detail" MUST mean an actual navigation to the commanded post. The edge MUST read the purpose field rather than only forwarding it, MUST resolve the navigable canonical target from the command itself (the canonical post permalink carried as the note identity, or an explicit address when supplied), and MUST verify after landing that the page's canonical post id equals the commanded id. If no navigable canonical target can be resolved, if navigation fails, or if the landed identity differs, the edge MUST return a not-started action-completed receipt naming that failure.

The edge MUST NOT satisfy a navigate-purpose open by reading whatever page is currently open: evaluating the current surface and returning it as the commanded detail is prohibited, whether or not the reported payload happens to describe a real post. A navigate-purpose open MUST always terminate in an action-completed receipt, never in a detail report and never with no receipt at all, so the cloud's migration wait has exactly one thing to consume.

#### Scenario: Navigate open returns a witness, not a note.detail

- **WHEN** the edge receives a navigate-purpose open for an approved comment migration
- **THEN** it lands on the target detail and returns an action-completed receipt with observation and derived note id
- **AND** it does not report a note.detail that overwrites the post's real reaction counts

#### Scenario: Navigate open without an explicit address still navigates

- **WHEN** a navigate-purpose open carries only the canonical post permalink as its note identity and no separate address field
- **THEN** the edge navigates to that permalink before producing its receipt
- **AND** it does not fall through to a current-page read

#### Scenario: Unresolvable or mismatched navigation is honestly not started

- **WHEN** the navigate-purpose open cannot resolve a navigable canonical target, or the landed page's canonical post id differs from the commanded id
- **THEN** the edge returns an action-completed receipt with a not-started outcome naming the resolution or identity failure
- **AND** it reports no detail and leaves no navigate-purpose command without a receipt
