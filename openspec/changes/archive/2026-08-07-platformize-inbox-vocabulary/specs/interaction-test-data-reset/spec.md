## MODIFIED Requirements

### Requirement: Reset reuses read synchronization without platform writes
After the Cloud transaction commits, Cloud SHALL send `wechat_channels.inbox.sync.request` with reason `test_reset` for the selected channel. Edge SHALL serialize this request on the channel sync lock, clear the channel read state, and then run the normal reader from an empty cursor. The operation MUST NOT call any reply sender or platform mutation endpoint and MUST NOT claim that the platform data was deleted.

#### Scenario: Existing platform sample is replayed
- **WHEN** a valid reset is delivered and the platform reader still returns the old sample
- **THEN** Edge submits it as a normal sync batch and Cloud persists it again as a new inbox record after its prior batch dedupe state was removed

#### Scenario: Platform no longer returns the sample
- **WHEN** reset and reread complete but the platform history endpoint returns no sample
- **THEN** the system reports the actual empty result and does not fabricate a restored comment or DM
