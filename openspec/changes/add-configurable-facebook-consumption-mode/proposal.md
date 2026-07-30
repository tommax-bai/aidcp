## Why

Facebook currently has a fixed-cadence rule mode, a separate slow-start lifecycle, and persona-driven scheduled actions, but it has no durable consumption mode whose next action is driven by confirmed platform outcomes. The fixed `5/2` rule constants and the group join-to-first-comment delay are also not product configuration, so operators cannot safely tune the requested `browse → like → join → historical-group comment` cadence from the backend.

## What Changes

- Add an environment-scoped Facebook operation policy with four explicit modes: `persona`, `slow_start`, `rule`, and `consumption`. The policy is revisioned, audited, written with compare-and-swap semantics, and exposes typed mode parameters rather than a generic action graph.
- Make the rule-mode browse threshold and join cadence backend-configurable. Existing enabled rule environments migrate to the current `5 views / 2 rounds` behavior; policy changes start a new revision without reinterpreting old progress.
- Add a durable consumption-mode state machine with configurable `viewsPerLike`, `confirmedLikesPerJoin`, and `confirmedJoinsPerComment` values, initially defaulting to `5/2/2`.
- Count only confirmed, newly produced platform outcomes toward downstream consumption counters. `already_liked`, `already_member`, pending, ambiguous, gated, and failed outcomes do not count as new success and do not create retry debt.
- Separate consumption stages: joining a group never comments in that newly joined group as part of the join action. After the configured number of confirmed new joins, Cloud strictly selects an eligible previously joined group, opens the first commentable item from the top of its discussion stream, and runs the ordinary comment approval/risk pipeline.
- Make the join-to-first-comment wait (currently the 24-hour deployment default) a revisioned backend setting with a default of 24 hours. Consumption selection obeys both this wait and the existing per-group re-comment cooldown, with no relaxed fallback; eligibility is determined only by timestamps, so recently joined groups naturally become eligible if the configured wait has elapsed.
- Restrict independent time-scheduled automatic group joining to `persona` mode. `slow_start`, `rule`, and `consumption` use only their own orchestration and never inherit the persona schedule's join trigger.
- Add Console controls and truthful runtime projections for operation mode, typed cadence values, policy revision, blockers, and group-comment timing. Existing customer rule-toggle callers remain a strictly mapped compatibility surface until their released clients move to the unified policy API.
- Add a customer-scoped unified operation-policy read/write surface and expose consumption mode in the Edge client beside cold-start and rule mode, both while creating an environment and while editing an existing one. The client sends only a mode plus the last confirmed revision; cadence values remain backend-owned.
- Reuse existing Edge atomic actions for browse, like, join, first-commentable-group-post selection, and comment. No Edge policy engine is introduced.

## Capabilities

### New Capabilities

- `facebook-operation-policy`: Environment-scoped, audited and revisioned authority for Facebook operation mode, typed cadence settings, compatibility reads/writes, and Console configuration.
- `facebook-consumption-mode`: Durable confirmed-outcome cadence, exact counter semantics, stage transitions, group selection, and truthful runtime projection for consumption mode.
- `client-facebook-operation-policy`: Customer-owned environment mode projection, CAS mutation, provisioning intent and Edge client presentation without client-side cadence authority.

### Modified Capabilities

- `facebook-rule-mode`: Replace compiled cadence constants with a policy snapshot and revision while preserving durable batching, dedupe, risk, approval, and outcome honesty.
- `facebook-group-comment-coverage`: Make join-to-first-comment wait backend-configurable and require a strict eligible-group path for consumption-mode first-post comments.
- `facebook-group-membership`: Allow independent scheduled automatic joining only while the effective Facebook operation mode is `persona`.
- `content-schedule`: Treat scheduled group joining as persona-mode scheduling rather than an execution source shared by rule, slow-start, and consumption modes, and expose runtime mode truth without creating a second configuration authority.
- `client-facebook-rule-mode-toggle`: Map the released environment-scoped rule toggle onto the unified operation policy without accepting account selectors or silently overriding active slow start.

## Impact

- **Control / contracts**: Adds two capabilities and modifies the six listed capabilities. This change supersedes the fixed-threshold and three-mode portions of the in-progress `environment-level-rule-mode-and-approval` change; implementation must integrate against its environment-keyed storage and preserve its approval-policy work.
- **Cloud / data**: Adds operation-policy and consumption-runtime migrations, configuration stores and APIs, scheduler arbitration, durable counters, immutable policy snapshots, and group-comment policy storage. Runtime ownership remains `account_id + execution_target + policy_revision`; Cloud remains the planner and final risk-state writer.
- **Console**: Adds environment operation-policy editing and group join-to-first-comment timing configuration, using server-provided bounds, expected revisions, write-after-read truth, and explicit error states.
- **Edge**: Adds the thin customer operation-mode selector and provisioning intent in the desktop UI while reusing existing atomic Native commands and confirmed/ambiguous receipts. Edge stores no cadence or runtime counter.
- **Deployment**: Cloud and Console runtime behavior changes require DEV deployment and verification. Edge source is integrated and validated, but no installer/package and no OL deployment are part of this change.
