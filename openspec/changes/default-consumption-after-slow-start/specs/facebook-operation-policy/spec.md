## MODIFIED Requirements

### Requirement: Mode and revision transitions preserve irreversible-action truth

A mode change or parameter change SHALL create a new policy revision. Once the new revision commits, Cloud MUST stop admitting new work under the superseded revision. Undispatched old-revision intents SHALL settle with a named `policy_superseded` outcome; already dispatched attempts SHALL retain their original revision and continue only through receipt/reconciliation so an irreversible action is not erased, retried, or relabelled. The new revision MAY begin only after the account's existing single-flight boundary permits it.

The unified projection SHALL accept `slow_start` as an explicit operator selection while keeping the lifecycle authority singular: selecting it SHALL activate the existing environment slow-start authority with a server-generated anchor and set the resumable base mode to `consumption` in the same service transaction. Selecting `persona`, `rule`, or `consumption` SHALL deactivate an active slow start and set that base mode in the same transaction. Existing environments migrated with both active slow start and enabled rule mode SHALL preserve `rule` as the resumable base until an operator makes a new selection. Environments already inside an active slow start whose stored base mode is the previously auto-written `persona` default SHALL be migrated once to `consumption` with a new policy revision and audit record; stored `rule` bases and environments not in an active slow start MUST NOT be touched by that migration. Rule/consumption counters or action debt MUST NOT transfer across a base-mode or slow-start transition.

#### Scenario: Disabling a mode while an action is dispatched

- **WHEN** a rule or consumption action has already been dispatched and an operator changes the environment to persona mode
- **THEN** Cloud stops admitting later stages under the old revision but continues honest receipt reconciliation for the dispatched attempt
- **AND** the new persona revision MUST NOT claim, retry, or count the old attempt as its own

#### Scenario: Transition to slow start is atomic

- **WHEN** an operator changes an eligible Facebook environment from rule or consumption to `slow_start`
- **THEN** the new operation-policy revision and the environment slow-start activation commit atomically
- **AND** no observable committed state permits rule/consumption and slow start to be simultaneously authoritative

#### Scenario: Returning to consumption starts clean

- **WHEN** an environment leaves consumption mode and later enters consumption again
- **THEN** the later policy revision starts all consumption counters at zero
- **AND** no unfulfilled like, join, or comment opportunity from the earlier revision is carried forward as retry debt

#### Scenario: Graduation resumes into consumption by default

- **WHEN** an environment whose slow start was selected or provisioned after this change graduates without any later operator mode selection
- **THEN** its effective mode becomes `consumption` under the stored resumable base
- **AND** consumption counters start from zero under the policy revision in force

#### Scenario: Explicit selections keep overriding the default

- **WHEN** an operator selects `persona` or `rule` for an environment after its slow start graduated
- **THEN** that selection becomes the stored base mode under a new revision
- **AND** nothing re-applies the consumption default without a new slow-start selection
