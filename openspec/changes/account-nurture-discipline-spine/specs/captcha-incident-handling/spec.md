## ADDED Requirements

### Requirement: Facebook soft-block throttling signals escalate to an aggressive risk backoff

The edge SHALL recognize Facebook inline throttling / safety-mode overlays and toasts — including "Action Blocked", "we limit how often you can do this", "misusing this feature", "you can't use this feature right now", and comments that are silently hidden seconds after posting, in addition to the existing checkpoint / login / captcha overlays — as throttling signals and report them to the cloud. The cloud SHALL feed each such signal into the existing `applySignal` input and migrate that account's risk state to `restricted` (an aggressive backoff that leaves only browsing enabled). A sequence of N consecutive post-check failures on the same action SHALL likewise be reported as a systemic-throttling signal and drive the account to `restricted`. The state migration MUST remain a single write by the cloud `RiskController`; the transition table MUST NOT be changed and the edge MUST NOT set a final risk state itself. This backoff is a fail-safe direction.

#### Scenario: Facebook soft-block toast drives the account to restricted
- **WHEN** the edge detects a Facebook "Action Blocked" or equivalent throttling toast/overlay and reports it
- **THEN** the cloud migrates that account's risk state to `restricted`
- **AND** interactions are stopped for that account, leaving only browsing enabled

#### Scenario: N consecutive post-check failures escalate to restricted
- **WHEN** the same action fails its post-action verification N consecutive times for one account
- **THEN** the cloud treats it as a systemic-throttling signal and migrates that account to `restricted`

#### Scenario: Silently hidden comment is treated as a throttling signal
- **WHEN** a just-posted Facebook comment is detected as hidden/removed within seconds of submission
- **THEN** the edge reports it as a throttling signal and the cloud migrates the account to `restricted`

#### Scenario: Recovery auto-downgrades on the existing window
- **WHEN** the existing risk recovery window elapses without new throttling signals
- **THEN** the account auto-downgrades out of `restricted` per the existing recovery behavior, unchanged by this change

#### Scenario: Final risk state stays a cloud single write
- **WHEN** the edge reports a throttling signal
- **THEN** only the cloud `RiskController` writes the resulting `restricted` state
- **AND** the edge does not set or assert any final risk state locally
