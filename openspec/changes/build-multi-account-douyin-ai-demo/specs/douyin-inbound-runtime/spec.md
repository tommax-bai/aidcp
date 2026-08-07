## ADDED Requirements

### Requirement: Inbound adapters preserve the fixture and real boundary
The inbound runtime SHALL select only the adapter for the process platform mode. The fixture adapter MUST emit deterministic, operator-triggerable direct-message and comment records without contacting Douyin. The real adapter SHALL treat undocumented web interfaces as experimental, MUST validate response and event schemas before normalization, and MUST fail closed with source-specific evidence when required fields or protocol expectations drift; it MUST NOT fabricate an empty successful read or a healthy source from an unreadable response.

#### Scenario: Real comment response no longer matches the schema
- **WHEN** the real comment adapter receives a response missing a required cursor or stable comment identity
- **THEN** it records a schema-drift failure for the comment source, inserts no guessed inbound item, and leaves the direct-message source state unchanged

#### Scenario: Fixture event is injected
- **WHEN** an operator triggers a named fixture direct-message event
- **THEN** the fixture adapter emits the documented deterministic record and performs no external request

### Requirement: Direct messages use an account-level WebSocket runtime
Each active real account SHALL receive direct messages through one session-bound account-level WebSocket stream rather than requiring a continuously running Chromium instance or relying on polling as the primary source. Before marking the direct-message source healthy, the runtime MUST establish an authenticated schema proof from current first-party behavior: an explicit protocol acknowledgement when one exists, or otherwise both a schema-valid session-bound DM bootstrap/history response and a WebSocket that remains owned and open for the bounded validation interval. Disconnects SHALL move that source to reconnecting or degraded, and bounded reconnect attempts MUST preserve account identity and deduplication state; transport open alone MUST NOT be presented as a healthy subscribed source, and the implementation MUST NOT invent an acknowledgement command absent observed evidence.

#### Scenario: WebSocket opens but the authenticated proof fails
- **WHEN** the direct-message transport opens but an observed acknowledgement is rejected or the required session-bound bootstrap/history proof fails
- **THEN** the source is not marked healthy and no unvalidated frame is normalized as an inbound message

#### Scenario: Direct-message stream reconnects
- **WHEN** a subscribed direct-message WebSocket disconnects and later reconnects within its bounded policy
- **THEN** the runtime resubscribes for the same account and repeated platform events remain deduplicated

### Requirement: Automation begins after a historical baseline for each source
For each account, each enabled inbound source SHALL complete and durably record its own initial historical baseline before any observed item from that source becomes eligible for automatic reply. The direct-message baseline MUST establish the authenticated stream proof plus a history cursor, server time boundary, or equivalent stable frontier; the comment baseline MUST include the platform cursor or equivalent stable frontier and the stable identities needed to protect the boundary. Subsequent frames and reads SHALL classify only records strictly beyond the applicable frontier as new. Service restart, session reauthorization, reconnect replay, poll overlap, or cursor replay MUST NOT convert baseline or previously observed items into new automation work.

#### Scenario: First successful comment read establishes baseline
- **WHEN** an authorized account completes its first schema-valid comment read containing existing comments
- **THEN** the runtime records the baseline, displays those comments as historical if retained, and creates no automatic-reply work for them

#### Scenario: Initial direct-message history is replayed
- **WHEN** a newly subscribed account receives pre-existing direct messages at or before its established source frontier
- **THEN** the runtime classifies them as baseline history and creates no automatic-reply work for them

#### Scenario: Incremental read contains old and new comments
- **WHEN** a later read repeats baseline comments and includes a comment with a new stable platform identity beyond the stored frontier
- **THEN** only the new comment is admitted as a new inbound item

### Requirement: Inbound records are normalized without losing platform identity
The runtime SHALL normalize every accepted direct message or comment into an account-scoped record containing source kind, stable platform event identity, exact conversation or content target identity, sender identity when available, platform timestamp, normalized text or media classification, observed timestamp, and eligibility state. It MUST preserve enough exact target data for a later ownership check while MUST NOT persist cookies, authorization tokens, protocol signatures, or unnecessary raw personal payloads. Non-text and self-originated items SHALL remain visible with an explicit ineligible reason and MUST NOT enter text auto-reply generation.

#### Scenario: Non-text direct message arrives
- **WHEN** the direct-message stream emits a schema-valid image-only message
- **THEN** the runtime stores a sanitized non-text inbound record, marks it ineligible for text auto-reply, and does not synthesize message text

#### Scenario: Text comment is normalized
- **WHEN** an incremental comment read returns a new text comment with stable comment and video identities
- **THEN** the stored record retains those exact identities and is eligible only after all configured policy checks pass

### Requirement: Deduplication is durable and atomic
The demo SHALL deduplicate inbound records using a durable uniqueness key that includes platform mode, account identity, source kind, and stable platform event identity. Admission of an inbound record and creation of its automation eligibility state MUST be atomic, and a comment page's accepted records and cursor advancement MUST commit in one transaction. Reconnect replay, overlapping comment pages, repeated fixture injection, process restart, and concurrent runtime callbacks MUST yield one inbound record and at most one generation claim for the same platform event; a crash MUST NOT advance a cursor past an uncommitted item.

#### Scenario: Same event arrives concurrently
- **WHEN** two runtime callbacks concurrently submit the same account, source kind, and stable platform event identity
- **THEN** exactly one durable inbound record is admitted and at most one auto-reply candidate is created

#### Scenario: Event is replayed after restart
- **WHEN** the service restarts and the platform replays an event already stored before shutdown
- **THEN** the durable uniqueness key suppresses a second record and no new generation or delivery is scheduled

#### Scenario: Comment transaction fails before commit
- **WHEN** comment item insertion or eligibility persistence fails while processing a page
- **THEN** the page cursor does not advance and a later repeat remains safe through durable deduplication

### Requirement: Source health is independent and evidence based
The runtime SHALL maintain separate direct-message and comment source states for each account, including disabled, starting, baselining, healthy, reconnecting, degraded, reauthorization-required, and stopped where applicable. A source MUST become healthy only after its own current success evidence, and one source's success MUST NOT overwrite another source's failure. The account runtime MAY remain partially useful when one source degrades, but explicit session invalidation MUST stop both sources and require reauthorization.

#### Scenario: Comment reads degrade while direct messages continue
- **WHEN** the comment adapter repeatedly fails schema-valid reads while the direct-message subscription remains acknowledged and receives valid frames
- **THEN** the UI projection reports comments degraded and direct messages healthy rather than collapsing both into one healthy state

#### Scenario: Shared session becomes unauthorized
- **WHEN** either source receives definitive evidence that the shared retained session is unauthorized
- **THEN** both sources stop new work and the account enters reauthorization-required

### Requirement: An unimplemented source is disabled without blocking an independent source
The real runtime SHALL allow an explicitly unimplemented source to remain `disabled`. A disabled source MUST NOT issue platform requests, establish a synthetic baseline, or be reported healthy, and it MUST NOT prevent another configured source from establishing its own baseline and activating its independent runtime. Delivery and generation for the disabled source SHALL remain unavailable.

#### Scenario: Private-message-only real runtime starts
- **WHEN** the real runtime is configured with direct messages enabled and comments disabled
- **THEN** it performs no comment request, exposes comments as disabled, and may activate the account after the direct-message baseline and acknowledged subscription complete
