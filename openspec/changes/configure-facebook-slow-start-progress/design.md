## Context

The unified Facebook operation-policy projection already gives Edge the confirmed mode, primary surface, policy revision, and a minimal slow-start lifecycle state. Cloud persists the environment anchor in `client_environments.slow_start_since` and target-local completion in `facebook_environment_slow_start_completion`; the risk controller derives the active day and graduation from those facts plus the global `slowStart.totalDays` policy.

The client therefore needs a bounded editing surface, not another progress store. The write must remain environment-scoped, work while the browser is stopped or the account is unbound, and preserve Cloud ownership/platform/binding checks and non-optimistic write-after-read behavior.

## Goals / Non-Goals

**Goals:**

- Let an operator set the current cold-start day and completed state from the existing Facebook operation-policy row.
- Make the persisted anchor and completion fact drive the same runtime quota and mode arbitration used everywhere else.
- Keep concurrent mode/progress edits revision-safe and return a complete authoritative projection after every accepted write.
- Preserve the ability to clear completion: a graduated environment remains represented as selected `slow_start` in the client until the operator chooses another mode.

**Non-Goals:**

- Changing global cold-start duration or daily caps.
- Adding Edge-local state, protocol-v2 commands, browser actions, or a new database table.
- Packaging/installing an Edge client or changing OL runtime as part of source implementation.

## Decisions

### 1. Add a version-safe dedicated progress projection

The store's authoritative view will carry the facts needed to derive progress, while a new customer route will expose `slowStartProgress: { day, totalDays, completed }` beside the existing minimal operation-policy projection. `day` is null for `off` or `unknown`; otherwise it is clamped to `1..totalDays`. `completed` is true exactly when the authoritative lifecycle is `graduated`, including explicit completion and time-based graduation.

The existing `/facebook-operation-policy` response remains byte-shape compatible because installed clients validate exact object keys. This keeps Edge free of calendar policy, lets it build the day selector from the same global duration used by Cloud, and allows Cloud-first deployment without breaking older clients. Extending the old `slowStart` object or returning only `since` was rejected because the former breaks exact validation and the latter makes Edge duplicate Shanghai-day and graduation calculations.

### 2. Use a dedicated progress write with the operation-policy revision

Edge will read and write a named environment progress route; writes accept exactly `{ expectedRevision, day, completed }`. Cloud will reject extra fields, invalid bounds, unsupported/foreign/conflicted environments, stale revisions, and progress writes when the current slow-start lifecycle is neither active nor graduated.

The existing `policyRevision` is the CAS token because mode selection and progress edits both mutate the effective operation policy and must serialize with each other. A separate progress revision was rejected because it would allow a concurrent switch away from cold start and a progress edit to both succeed.

### 3. Translate day edits into the existing Shanghai-day anchor

For day `D`, Cloud writes `slow_start_since = current Shanghai day start - (D - 1) days`. It then upserts the target-local completion row when `completed=true`, or deletes it when `completed=false`. Both facts, the operation-policy revision, audit record, and mirror version are committed in one transaction.

Writing the full `{day, completed}` tuple on either control change makes clearing completion deterministic: Cloud refreshes the anchor to a still-active day instead of deleting completion while leaving an already-expired anchor that would immediately graduate again.

### 4. Keep graduated cold start selected in the client

The selected client mode maps both `slowStart.state=active` and `slowStart.state=graduated` to `slow_start`. This preserves the requested conditional controls after marking completion and allows the operator to clear completion. Runtime `effectiveMode` remains Cloud-authoritative: graduation stops cold-start quota arbitration even though the configuration selector still identifies the lifecycle selected for the environment.

### 5. Render only confirmed state

The two compact controls are placed immediately after the primary-surface select. They are shown only when both the existing operation-policy projection and the dedicated progress projection are complete and the selected mode is `slow_start`. During a write they are disabled and retain the last confirmed tuple; matching write-after-read progress and policy projections are required before the UI changes. Errors and late responses remain isolated by `envKey`.

## Risks / Trade-offs

- [Changing a day rewrites historical meaning] → Label the field as an operator correction, bound it to the global duration, audit the before/after progress tuple, and avoid silent automatic writes from Edge.
- [Manual completion can relax cold-start quotas immediately] → Require an owned Facebook environment, explicit client action, CAS, Cloud transaction, and authoritative readback; do not infer completion from a local checkbox.
- [Graduated configuration versus effective runtime can be misunderstood] → Keep `completed` and runtime `effectiveMode` separate in the projection and never claim cold-start quotas are active after graduation.
- [Cloud/client version skew] → Keep the old operation-policy response unchanged and deploy the additive route first; the new client disables progress editing when the named IPC or complete progress projection is unavailable.

## Migration Plan

1. Land and validate Cloud projection/write support; no schema migration is required.
2. Deploy the Cloud default branch to DEV after the standard target checks.
3. Land Edge source and focused renderer/contract tests. Do not package or install the client without explicit release authorization.
4. Rollback is code-only: revert the Edge controls and Cloud route/store method. Existing anchors and completion facts remain valid and readable by the prior runtime.

## Open Questions

None.
