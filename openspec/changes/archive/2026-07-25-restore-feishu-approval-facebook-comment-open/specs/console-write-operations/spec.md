## ADDED Requirements

### Requirement: Feishu approval ingress is wired to the durable approval authority in every production composition

Every Cloud service composition that instantiates the Feishu approval receiver SHALL inject the same durable, first-writer-wins approval write authority used by the other approval ingresses. The receiver MUST NOT write PostgreSQL directly, create a separate local-file authority, or report a decision as accepted when the authority is unavailable. A missing write authority MUST remain a visible unavailable response, and production composition tests MUST prevent that state from being shipped.

#### Scenario: Feishu card decision reaches the durable approval record

- **WHEN** an operator approves or rejects a valid pending request from a Feishu approval card
- **THEN** the receiver calls the shared durable approval write authority with that request id, decision, actor, channel, and payload
- **AND** the result remains subject to the same first-writer-wins and execution-target semantics as Web and client approval

#### Scenario: Service composition cannot silently omit authorization ownership

- **WHEN** a Cloud service mode instantiates the Feishu approval receiver
- **THEN** its production composition supplies the durable approval write port
- **AND** a composition regression fails if that port is removed

#### Scenario: Missing write authority fails visibly without fallback

- **WHEN** an isolated or invalid receiver composition handles an approval callback without a write authority
- **THEN** it returns a distinguishable authorization-service-unavailable response
- **AND** it MUST NOT write a local signal, mutate approval state, or report success
