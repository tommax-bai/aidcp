## ADDED Requirements

### Requirement: Facebook automatic comment path must not weaken xhs human approval

Facebook scheduled comments SHALL use a separate platform-specific automatic path gated by deterministic validators and kill switches. Existing xhs comment interaction and manual approval requirements MUST remain intact; changes to shared composer helpers MUST preserve xhs `CommentApprovalGate` behavior and MUST NOT make xhs comments auto-post without approval.

#### Scenario: xhs approval still required
- **WHEN** xhs comment interaction produces a draft after this change
- **THEN** it still waits for the existing human approval gate before edge submit, unless an existing explicit manual path already defines otherwise

#### Scenario: Facebook validator path does not enter xhs manual skip set
- **WHEN** Facebook scheduled comment code runs
- **THEN** it uses its own automatic account tracking and does not add Facebook accounts to xhs manual-comment skip-quota collections

### Requirement: Shared compose extraction preserves approval semantics

If composition and cleanup logic is refactored into shared helpers, the helper SHALL be wrapped by separate xhs `withApproval` and Facebook `withValidators` callers. The helper itself MUST NOT decide that a comment can be posted.

#### Scenario: Helper returns draft only
- **WHEN** shared composition logic succeeds
- **THEN** it returns candidate text to the caller; xhs approval or Facebook validators still determine whether submit is allowed
