## ADDED Requirements

### Requirement: Reels keyboard-probe learning advances only through normal continuation
The Edge Reels key preference SHALL affect only which single key a normally admitted `page.scroll` dispatches. An unconfirmed or identity-unresolved key delivery MAY select the alternate key for the next command, and canonical progress MAY retain the successful key, but neither result SHALL create an immediate retry, bypass dwell or risk admission, consume a view, or disable later commands. Cloud SHALL continue to own whether and when another command is admitted.

#### Scenario: Unconfirmed probe waits for normal admission
- **WHEN** Edge emits `reels_navigation_unconfirmed` after delivering one preferred key
- **THEN** no second key SHALL run in that command and the alternate key SHALL run only if Cloud later admits another scroll normally

#### Scenario: Identity-unresolved probe waits for normal admission
- **WHEN** Edge emits `reels_identity_unresolved` after delivering one preferred key
- **THEN** Edge SHALL emit no card or view and SHALL wait for Cloud's ordinary continuation path before trying the alternate key

#### Scenario: Confirmed key remains a soft preference
- **WHEN** one probe produces a canonical Reel and its key is retained
- **THEN** the retained key SHALL still run only after the next command passes existing session, quota, soft-pause, interaction-hold, dedupe, dwell, cancellation, and deadline gates

#### Scenario: Admission suppression performs no new input
- **WHEN** quota, pause, hold, session end, command dedupe, cancellation, or deadline suppresses the next command
- **THEN** the key preference SHALL create no timer, retry debt, bypass command, or trusted input
