## ADDED Requirements

### Requirement: Facebook targeted comments use visible safety quotas without a hidden feature cap

Every automatic Facebook targeted-comment entry point SHALL pass the account's current `RiskController` state and minute/hour/day comment quota. The targeted-comment pipeline MUST NOT apply `AIDCP_FB_COMMENT_DAILY_CAP` or any equivalent hidden feature-local daily veto.

Visible content-schedule enablement and schedule-level planning limits SHALL retain their existing admission role at the schedule entry point. They MUST NOT be reconstructed from `risk_interactions` inside the targeted-comment pipeline. Manual `/comment` override behavior SHALL remain unchanged.

#### Scenario: Automatic targeted comment follows the visible safety policy

- **WHEN** an automatic Facebook targeted comment reaches the write pipeline and the account `RiskController` allows `comment`
- **THEN** the pipeline continues to its existing session, approval, de-duplication, target and submission gates
- **AND** no hidden environment daily cap may stop it

#### Scenario: Safety quota rejects before submission

- **WHEN** the account `RiskController` rejects an automatic Facebook comment for a minute, hour or day quota
- **THEN** Cloud MUST NOT submit the comment and SHALL report the named quota reason without promoting it to success

#### Scenario: Manual override remains explicit

- **WHEN** an authorized operator invokes manual `/comment` through the existing override entry point
- **THEN** the existing manual override semantics remain unchanged
- **AND** removing the hidden Facebook cap MUST NOT add a new manual restriction or bypass a non-quota safety gate that the manual contract retains
