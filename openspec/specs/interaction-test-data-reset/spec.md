# interaction-test-data-reset Specification

## Purpose
TBD - created by archiving change wechat-channels-test-data-reset. Update Purpose after archive.
## Requirements
### Requirement: Reset remains dev-only and account-channel scoped
The system SHALL enable interaction test-data reset only when Cloud is explicitly identified as `dev` and the reset feature flag is enabled. Each request MUST resolve the current customer-owned env/account authoritatively and MUST select exactly one channel, `comment` or `dm`; it MUST NOT accept an account identifier, all-channel wildcard, or cross-environment scope from the client.

#### Scenario: Non-dev Cloud receives reset request
- **WHEN** a customer calls the reset route on a Cloud deployment that is not explicitly identified as `dev` or has not enabled the reset flag
- **THEN** Cloud rejects the request without deleting Cloud rows or dispatching an Edge command

#### Scenario: Current environment owner resets one channel
- **WHEN** the enabled dev endpoint receives a valid request for `comment` from the owner of the current environment
- **THEN** the operation is scoped to that environment's authoritative account and the comment channel only

### Requirement: Reset clears only replay-blocking inbound state
Cloud SHALL transactionally delete the selected account/env/channel's interaction threads and their cascaded messages/reply jobs, sync batches, and sync cursors. It MUST preserve platform authorization, runtime controls, reply configuration, customer bindings, risk state, offboarding state, and audit records. Edge SHALL delete only the selected channel's sync checkpoints and thread-source cache while preserving encrypted session, reply executions/results, other-channel state, and offboarding state.

#### Scenario: Comment reset preserves DM and control state
- **WHEN** a valid comment reset completes
- **THEN** Cloud and Edge comment replay-blocking state is cleared while DM state, auth, controls, configuration, risk and lifecycle state remain unchanged

### Requirement: Reset is gated before deletion
Before Cloud deletes data it SHALL confirm the selected channel's read control and effective platform read capability, an active matching authorization, `writePaused=true`, and exactly one online Edge advertising `interaction_test_data_reset_v1`. Cloud MUST reject the operation when any selected-channel send attempt exists, regardless of attempt status.

#### Scenario: Edge is offline or too old
- **WHEN** no uniquely targeted online Edge advertises the test-reset capability
- **THEN** Cloud rejects the request before deleting any interaction data

#### Scenario: Channel has send history
- **WHEN** the selected account/env/channel contains a confirmed, failed, ambiguous, created, or dispatched send attempt
- **THEN** Cloud rejects the reset and preserves every Cloud and Edge record

### Requirement: Reset reuses read synchronization without platform writes
After the Cloud transaction commits, Cloud SHALL send `wechat_channels.inbox.sync.request` with reason `test_reset` for the selected channel. Edge SHALL serialize this request on the channel sync lock, clear the channel read state, and then run the normal reader from an empty cursor. The operation MUST NOT call any reply sender or platform mutation endpoint and MUST NOT claim that the platform data was deleted.

#### Scenario: Existing platform sample is replayed
- **WHEN** a valid reset is delivered and the platform reader still returns the old sample
- **THEN** Edge submits it as a normal sync batch and Cloud persists it again as a new inbox record after its prior batch dedupe state was removed

#### Scenario: Platform no longer returns the sample
- **WHEN** reset and reread complete but the platform history endpoint returns no sample
- **THEN** the system reports the actual empty result and does not fabricate a restored comment or DM

### Requirement: Partial completion and audit remain honest
Cloud SHALL write a body-free audit event for reset success or post-delete dispatch failure, including actor, channel and deletion counts only. A request whose Cloud transaction committed but whose Edge dispatch failed MUST return a distinct partial-completion error and MUST NOT be reported as accepted or fully completed.

#### Scenario: Socket closes after Cloud commit
- **WHEN** Cloud clears the selected channel but the targeted WebSocket accepts zero reset commands
- **THEN** Cloud returns a retryable partial-completion error, records the condition without message bodies, and permits a later reset retry

