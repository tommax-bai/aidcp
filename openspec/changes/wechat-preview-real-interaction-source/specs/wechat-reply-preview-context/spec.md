## ADDED Requirements

### Requirement: Reply preview SHALL support stored real inbound context

The system SHALL let an authorized operator select a recent stored WeChat Channels inbound interaction and SHALL populate the reply preview's channel, message type, user message, user name, and video title from that selected context. When at least one eligible context exists, Console SHALL select the newest context by default; it SHALL also retain an explicit manual simulation mode.

#### Scenario: Latest real comment supplies its video title

- **WHEN** an account has a recent stored comment interaction whose thread has a non-empty source title and the operator opens reply preview
- **THEN** Console selects that interaction by default and displays its inbound text, participant name, and source title as the preview inputs
- **AND** running preview sends that source title as `videoTitle` instead of `null`
- **AND** the rendered `{{video_title}}` uses the stored source title rather than the configured missing-value fallback

#### Scenario: Operator switches to manual simulation

- **WHEN** the operator selects manual simulation after a real context was loaded
- **THEN** Console SHALL allow independently editable simulated inputs
- **AND** the preview request SHALL use exactly the values visible in the manual form

#### Scenario: No stored context remains safely previewable

- **WHEN** the account has no eligible stored inbound interaction or no authoritative environment binding
- **THEN** the context endpoint returns an empty list without triggering Edge synchronization
- **AND** Console keeps manual simulation available and explains that no real interaction is available

### Requirement: Preview context reads SHALL remain scoped and side-effect free

Cloud SHALL resolve preview contexts only within the requested account and its authoritative interaction environment. Reading or selecting a context MUST NOT create or update an interaction, reply job, send attempt, sync request, audit send event, or Edge command. The projection MUST NOT expose platform external identifiers, outbound text, attachment bodies, or send-attempt data.

#### Scenario: Cross-account context identifier is not exposed

- **WHEN** an operator requests preview contexts for account A
- **THEN** every returned thread and inbound message belongs to account A and its authoritative environment
- **AND** no context belonging to account B is returned

#### Scenario: Context selection has no operational side effect

- **WHEN** an operator loads and selects a real preview context
- **THEN** Cloud performs only bounded reads
- **AND** no Edge command, synchronization request, reply job, or send attempt is created

### Requirement: DM preview context SHALL retain full-text permission gating

Cloud SHALL require both `interaction.config.preview` and `interaction.dm.view_full` before returning real DM preview context. Comment preview context SHALL require `interaction.config.preview` only.

#### Scenario: Preview-only operator cannot read DM text

- **WHEN** an operator has `interaction.config.preview` but lacks `interaction.dm.view_full` and requests DM preview contexts
- **THEN** Cloud returns `INTERACTION_PERMISSION_DENIED`
- **AND** no DM participant name or message text is returned
