## ADDED Requirements

### Requirement: Chat generation is isolated behind a platform-neutral boundary
The demo SHALL invoke the existing OpenAI-compatible chat-llm service through a platform-neutral generation port that accepts only sanitized normalized inbound content, configured persona or instruction text, bounded conversation context, and correlation metadata. The chat-llm client MUST NOT receive Douyin cookies, tokens, signatures, raw protocol payloads, browser endpoints, selectors, or platform delivery capabilities. Model output SHALL return to the orchestration layer and MUST NOT directly call a Douyin adapter or mark a reply delivered.

#### Scenario: Direct-message text is sent for generation
- **WHEN** an eligible normalized direct message acquires generation ownership
- **THEN** chat-llm receives sanitized text and bounded context without any Douyin credential or delivery primitive

#### Scenario: Model returns text
- **WHEN** chat-llm returns a valid reply candidate
- **THEN** the orchestration layer validates and persists the candidate before a separate delivery claim can be acquired

### Requirement: Only eligible new text items enter automation
The auto-reply orchestrator SHALL admit only deduplicated text direct messages and comments that were observed after the source baseline, are not self-originated, belong to an authorized account, have an available delivery route for their source, and pass the configured per-account automation policy. Historical baseline records, non-text items, duplicates, already terminal items, and items whose exact target is missing MUST receive an explicit ineligible disposition and MUST NOT call chat-llm.

#### Scenario: Historical comment is present at baseline
- **WHEN** the initial comment baseline includes an otherwise valid text comment
- **THEN** the comment is marked historical and no chat-llm request or delivery is created

#### Scenario: Comment delivery capability is unavailable
- **WHEN** a new text comment belongs to an account whose comment capability is unavailable
- **THEN** it is shown as reply unavailable and does not consume a chat-llm generation request

### Requirement: Generation ownership is durable and account scoped
The orchestrator SHALL atomically acquire one durable generation claim per normalized inbound identity before calling chat-llm. The claim MUST record account, source, inbound identity, automation configuration revision, and generation state. Only the current claim owner MAY persist a candidate or hand it to delivery, and it MUST recheck account authorization, automation state, configuration revision, and exact-target ownership before dispatch. Concurrent callbacks, reconnect replay, and restart recovery MUST NOT create multiple active generations or deliveries for one inbound item.

#### Scenario: Duplicate callbacks race for generation
- **WHEN** two workers attempt to generate a reply for the same normalized inbound identity
- **THEN** exactly one acquires generation ownership and at most one chat-llm request is active

#### Scenario: Configuration changes during generation
- **WHEN** chat-llm returns after the account automation configuration revision has changed
- **THEN** the stale owner cannot dispatch the candidate and the record exposes a superseded or canceled disposition

### Requirement: Stop and resume preserve ownership and history boundaries
The operations API SHALL provide account-scoped stop and resume controls for auto-reply generation. Stop MUST prevent new generation claims immediately and MUST cause every generated-but-not-dispatched owner to recheck and cancel before platform submission; it MUST NOT rewrite a delivery that may already have been submitted. Eligible new items arriving while stopped SHALL remain durably held with that reason. Resume SHALL make held post-baseline items eligible under the current configuration exactly once and MUST NOT replay historical baseline, duplicate, terminal, or submitted_unknown items.

#### Scenario: Automation stops while generation is in flight
- **WHEN** an operator stops an account after chat-llm begins but before delivery dispatch
- **THEN** the generation owner persists no platform submission and records the candidate as canceled or held by the stopped state

#### Scenario: Automation resumes with held new items
- **WHEN** an operator resumes an account that accumulated eligible post-baseline text items while stopped
- **THEN** each still-current held item may acquire generation ownership once while baseline and terminal items remain excluded

### Requirement: Chat-llm credentials and failures remain server-side
The chat-llm endpoint, model selection, timeout, and credentials SHALL be server configuration. Credentials MUST NOT be returned to the operations UI, stored in inbound records, or written to logs or timelines. Timeout, unavailable service, malformed response, empty output, or output exceeding configured bounds SHALL produce an explicit generation failure or held state and MUST NOT invoke platform delivery or fabricate reply text.

#### Scenario: Chat service times out
- **WHEN** chat-llm does not return a valid response within the configured deadline
- **THEN** generation records a sanitized timeout outcome and no Douyin delivery attempt is created

#### Scenario: Model output is empty
- **WHEN** chat-llm returns an empty or schema-invalid candidate
- **THEN** the candidate is rejected with an explicit generation reason and no platform send occurs
