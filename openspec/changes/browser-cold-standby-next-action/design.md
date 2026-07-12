## Context

The edge desktop shell can keep AdsPower/Chrome open while cloud-side risk gates intentionally delay the next automated action. That is correct behavior for quota and active-window safety, but it consumes local CPU and memory during waits that may last tens of minutes.

The system already has two useful boundaries:

- Cloud owns risk, quota, active-window, and orchestration timing decisions.
- Edge owns browser lifecycle and can stop/restart an environment, but should not invent eligibility decisions.

This change adds a narrow "cold standby" path between those boundaries. Cloud may publish a deterministic long-wait hint through the existing UI snapshot stream. Edge treats the hint as advisory, applies a local switch and safety checks, closes the browser during the wait, then wakes shortly before the forecasted eligible time.

## Goals

- Reduce idle browser resource usage during long waits.
- Keep the cloud-to-edge connection and operator visibility intact.
- Default the feature on, while leaving an immediate runtime escape hatch.
- Avoid guessed recovery for hard blockers such as captcha, login, manual intervention, unknown scheduler state, or occupied environments.

## Non-Goals

- Do not change risk quotas or action pacing policy.
- Do not move planning, risk, or eligibility decisions into edge.
- Do not force desktop package release as part of this change.
- Do not cold-standby during publish/action execution where closing the browser could corrupt in-flight work.

## Design

### Cloud wait hint

Cloud exposes an optional `browserStandby` object on `ui.snapshot`. The first implementation derives it from deterministic risk/quota release data for automated browsing work, especially view quota waits. The payload is absent or ineligible when the wait cannot be proven finite.

The hint includes:

- `enabled`: cloud-side switch after env/config resolution.
- `eligible`: whether the current wait is safe to use for cold standby.
- `reason`: machine-readable reason such as `view_quota`, `short_wait`, `disabled`, or `no_wait`.
- `waitMs`: milliseconds until the next eligible time from the hint generation moment.
- `wakeAt`: epoch milliseconds for the eligible time.
- `generatedAt`: epoch milliseconds used for the calculation.
- `source`: which deterministic source produced the hint, initially `risk`.
- `minWaitMs`: the cloud threshold for publishing an eligible hint.
- `warmupMs`: suggested edge warmup before `wakeAt`.

Cloud does not publish an eligible hint for captcha, login, manual intervention, unknown wait causes, external occupancy, or incomplete state. Those states remain normal warnings/presence events.

### Edge cold standby controller

Edge receives the snapshot through the existing `[ui-event]` pipeline. The Electron supervisor records the latest hint and only enters cold standby if all local checks pass:

- The local feature switch is enabled. Default is enabled.
- The hint is eligible, finite, and long enough after applying the local threshold.
- The environment has a running core/browser session and is not already closing, paused, removed, occupied, blocked, or auth-gated.
- There is no known in-flight action/publish risk.

When checks pass, edge closes the browser immediately and keeps a wake timer for `wakeAt - warmupMs`. At wake time it restarts/resumes the environment through the existing lifecycle path. Manual pause/close/remove cancels the standby timer.

### Switches

There are two layers:

- Cloud switch: `AIDCP_BROWSER_COLD_STANDBY` defaults enabled. It controls whether cloud publishes eligible hints.
- Edge switch: desktop settings default enabled and may be disabled with `AIDCP_BROWSER_COLD_STANDBY=0/false/off/no`. Edge also has local threshold and warmup values so a stale cloud hint cannot force an aggressive local close.

### Observability

Edge status exposes `browserStandby` with the current mode (`scheduled`, `sleeping`, `waking`, `disabled`, or `skipped`) and wake timing. Renderer copy remains concise; operator-facing logs explain why a hint was skipped when local checks reject it.

## Risks

- Closing immediately after a snapshot could interrupt work if local state is stale. Mitigation: edge checks current session state and known pending lifecycle flags before closing.
- A stale hint could wake late or early. Mitigation: include `generatedAt`, recalculate relative timing locally, and wake with a warmup buffer.
- Default-on behavior may surprise operators. Mitigation: clear local/env switch and visible status when cold standby is active.

## Validation

- Unit-test cloud hint builder for disabled, short wait, finite quota wait, and no-wait cases.
- Unit-test UI event sanitization and protocol contract for the optional payload.
- Unit-test edge hint normalization / local decision logic.
- Run focused cloud and edge test suites plus OpenSpec validation.
