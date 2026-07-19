## ADDED Requirements

### Requirement: Test reset exposes distinct clear dispatch and completion states
The Video Channels test reset surface SHALL distinguish Cloud data deletion, re-pull command dispatch, and platform re-read completion. A successful API response with `resync=accepted` proves only that Cloud dispatched the request to a currently routable socket; it MUST NOT be presented as proof that Edge started or completed the platform read.

#### Scenario: Re-pull command is dispatched
- **WHEN** Cloud clears the selected channel and returns `resync=accepted`
- **THEN** the client says the request was sent and is waiting for a sync result, without claiming that re-pull has completed

#### Scenario: Re-pull command is not dispatched
- **WHEN** Cloud clears the selected channel and returns `resync=skipped`
- **THEN** the client says the command was not delivered and instructs the operator to retry after the connection is restored, without promising an automatic replay

### Requirement: Reset completion requires newer channel sync evidence
Before dispatching reset, the client SHALL capture the selected channel's current `syncFreshness.receivedAt` baseline. The client MUST report re-pull completion only after a later authorized list or detail response contains target-channel evidence whose `receivedAt` is strictly greater than that baseline. HTTP success, `meta.asOf`, socket connectivity, auth state, and an empty list MUST NOT substitute for this evidence.

#### Scenario: Evidence has not advanced
- **WHEN** reset was accepted but subsequent list responses contain no target-channel evidence newer than the captured baseline
- **THEN** the client remains in a waiting-for-sync-result state

#### Scenario: Evidence advances
- **WHEN** a later target-channel sync batch is committed and customer API returns a `receivedAt` newer than the captured baseline
- **THEN** the client reports that re-pull completed for that channel and clears its pending reset state

#### Scenario: Comment and DM resets overlap
- **WHEN** comment and DM are reset in succession before either channel produces newer evidence
- **THEN** the client tracks both channel baselines independently and completes each channel only from its own newer evidence
