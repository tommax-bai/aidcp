## ADDED Requirements

### Requirement: Customer operation-mode access is environment-scoped and cadence-free

Cloud SHALL expose authenticated customer `GET` and `PUT /environments/:envKey/facebook-operation-policy` routes for an environment owned by the current customer. The route MUST validate the authoritative environment platform as Facebook and MUST NOT require a currently bound account or running Edge session. A missing, foreign, retired, unsupported-platform, conflicting or unreadable environment SHALL fail closed without revealing an account identifier.

The customer projection SHALL contain only `envKey` and a `facebookOperationPolicy` object with `baseMode`, `effectiveMode`, `policyRevision`, slow-start state and named blocker. It MUST NOT expose or accept account selectors, execution targets, cadence values, bounds, counters, action targets, audit actors or runtime debt.

The PUT body SHALL accept exactly `expectedRevision` plus `mode=persona|slow_start|rule|consumption`. Cloud SHALL apply the same policy CAS, audit transaction, slow-start lifecycle transition and write-after-read authority used by the internal Panel route while preserving all stored cadence values. A stale revision SHALL return the current authoritative customer projection and MUST NOT merge or overwrite it.

#### Scenario: Owned unbound environment can select consumption

- **WHEN** a customer selects `consumption` for an owned Facebook environment with no bound account and supplies the current revision
- **THEN** Cloud commits the next environment policy revision and returns `baseMode=consumption`
- **AND** the response does not fabricate an execution object, action progress or successful platform work

#### Scenario: Owned unbound environment retains its slow-start selection

- **WHEN** a customer selects `slow_start` for an owned Facebook environment with no bound account and supplies the current revision
- **THEN** Cloud commits the environment slow-start anchor and returns `baseMode=persona`, `slowStart.state=active`, and `effectiveMode=null`
- **AND** clients present slow start as the configured choice without fabricating an account or active execution object

#### Scenario: Customer mode write cannot smuggle cadence

- **WHEN** a customer PUT includes `viewsPerLike`, `accountId`, an execution target or any field other than `expectedRevision` and `mode`
- **THEN** Cloud rejects the entire request before ownership-dependent mutation
- **AND** no policy or audit revision is created

#### Scenario: Stale customer editor receives current truth

- **WHEN** the customer submits revision 4 after another actor committed revision 5
- **THEN** Cloud returns a conflict containing the current cadence-free revision 5 projection
- **AND** no revision 6 is created for the stale request

### Requirement: Facebook provisioning records one mutually exclusive operation intent

The customer environment-provisioning completion request MAY include `facebookOperationMode=persona|slow_start|rule|consumption`. This field is Facebook-only and SHALL be mutually exclusive with released `slowStartEnabled` and `facebookRuleModeEnabled` inputs; mixing new and legacy operation intents SHALL reject the entire completion before environment, ownership, policy, audit or intent state mutation.

When present, environment registration, ownership assignment, slow-start anchor, initial revisioned operation-policy snapshot, initial audit and provisioning completion SHALL commit atomically. `slow_start` SHALL activate the existing lifecycle and persist `persona` as its resumable base; `rule` and `consumption` SHALL persist their matching base mode; all initial cadence values SHALL come from Cloud defaults. The success response SHALL include the committed customer policy projection, and the client MUST NOT claim that the selected mode was configured unless that projection matches.

#### Scenario: Consumption environment is provisioned atomically

- **WHEN** a valid Facebook provisioning intent completes with `facebookOperationMode=consumption`
- **THEN** Cloud creates the environment, ownership and initial consumption base policy in one transaction
- **AND** any policy/audit failure rolls back all of them, leaving the intent unconsumed

#### Scenario: New and legacy intents cannot be mixed

- **WHEN** a completion request includes `facebookOperationMode` together with either legacy operation Boolean
- **THEN** Cloud rejects the request as a conflicting run mode
- **AND** it does not silently choose a priority or partially create the environment

### Requirement: Edge presents consumption without becoming a policy authority

The Edge client SHALL show consumption in both Facebook operation-mode entry points: the environment-creation selector and the existing-environment mode control near cold-start and rule. Visible ordering SHALL be `persona/normal`, `slow_start/cold-start`, `rule`, then `consumption`, so consumption is below cold-start and rule in the client presentation.

Both entry points SHALL use the unified customer operation-policy contract. The existing-environment control MUST render only Cloud-confirmed state, send the last confirmed `policyRevision`, retain the prior state while a write is pending or fails, and apply only the write-after-read response. The client SHALL NOT persist or submit cadence numbers, infer effective mode from local Boolean combinations, or relabel a saved policy as running platform work.

#### Scenario: Existing client selects consumption

- **WHEN** Cloud currently reports persona at revision 8 and the customer selects consumption
- **THEN** Edge sends only `{expectedRevision:8,mode:"consumption"}`
- **AND** it marks consumption selected only after Cloud returns a matching revision 9 projection

#### Scenario: Higher-priority effective mode remains truthful

- **WHEN** Cloud reports an active slow-start effective mode while the stored base projection differs
- **THEN** Edge displays slow-start as effective and the separate base-mode truth without inventing simultaneous enabled modes
- **AND** consumption remains visually after cold-start and rule rather than being presented as the winning mode

#### Scenario: Policy read is unavailable

- **WHEN** the customer route is unavailable, stale or returns an incomplete projection
- **THEN** Edge shows a named unavailable state and disables mutation
- **AND** it MUST NOT guess persona, reuse an old rule Boolean or optimistically enable consumption
