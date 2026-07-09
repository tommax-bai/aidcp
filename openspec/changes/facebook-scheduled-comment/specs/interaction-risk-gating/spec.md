## ADDED Requirements

### Requirement: Facebook automatic comments are pre-gated and counted only after verified success

Facebook scheduled comment attempts SHALL call the cloud risk gate before dispatch and again before submit when practical. Success counting SHALL happen only after server-confirmed verification returns `ok:true`. Failed, skipped, shadow, validator-rejected, login-blocked, checkpointed, or ambiguous attempts MUST NOT call `record('comment')` as success.

#### Scenario: Quota denial prevents dispatch
- **WHEN** `canDo('comment')` denies a Facebook scheduled comment attempt
- **THEN** the trigger does not dispatch the edge comment work and records/returns a quota-denied non-success outcome

#### Scenario: Only verified success records risk
- **WHEN** Facebook edge execution returns verified `ok:true`
- **THEN** cloud records one `comment` interaction for that account; any non-success return records no successful interaction

### Requirement: Facebook automatic comments must not use manual-comment quota bypass

Facebook scheduled comment accounts SHALL NOT be placed into xhs/manual comment collections that skip risk recording or quotas. Automatic Facebook comments have no human-in-loop approval at submit time and MUST use the normal automatic interaction safety gates.

#### Scenario: Manual bypass is not used
- **WHEN** a Facebook scheduled comment succeeds
- **THEN** it is counted through the automatic `interaction.occurred -> RiskController.record('comment')` path and is not skipped due to a manual-comment account set
