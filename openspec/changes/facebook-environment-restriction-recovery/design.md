## Context

Facebook overlay classification currently returns `captcha` whenever `location.href` contains `/checkpoint`, before checking whether the page actually contains a captcha iframe or human-verification copy. `captcha` is reported immediately and Cloud maps it to a confirmed risk signal, so a generic security checkpoint can persist `restricted` even when no captcha control was observed. The AIDCP persona notice is an Electron-owned Shadow DOM element and does not change the Facebook URL; it is not the trigger.

The Electron companion receives live risk state through `ui.snapshot`, but a stopped environment falls back to a locally initialized `normal` value. Cloud remains the authority and already has `operator_override_recover`, while the customer-auth API already provides the correct environment-ownership and persistent environment-to-account binding boundary.

## Goals / Non-Goals

**Goals:**

- Distinguish a generic Facebook checkpoint from positive captcha evidence without allowing automation to continue on a blocked page.
- Let an authenticated customer see and recover the authoritative `restricted` state for the selected Facebook environment, including while its Edge process is stopped.
- Keep account selection, platform validation, risk mutation, audit reason generation, and paused-edge recovery on Cloud.
- Keep the Electron surface to one compact recovery button plus contextual help.

**Non-Goals:**

- Solving, clicking through, or claiming that Facebook itself has cleared a checkpoint or captcha.
- Allowing customers to recover `warned` or `frozen`, select an `accountId`, choose a risk signal kind, or submit an audit reason.
- Changing protocol message types/payloads, database schema, Feishu alert resolution, or remote captcha-assist UI.
- Building or publishing a desktop installer.

## Decisions

### 1. Classify from positive evidence before route fallback

The Edge classifier SHALL use this order:

1. Captcha iframe/vendor URL or explicit human-verification/captcha semantics → `captcha` immediately.
2. `/login`, `/recover`, or `/two_step_verification` → `login`.
3. A generic `/checkpoint` route or broad `security check` copy without captcha evidence → `unknown`.
4. Existing Facebook throttle copy → `unknown`; otherwise `none`.

This preserves immediate fail-closed behavior for real captcha evidence. A generic checkpoint still stops local work and enters the existing one-cycle persistence gate before Cloud receives `kind:'unknown'`; it is no longer mislabeled as a captcha solely from the route. Treating all checkpoints as `login` was rejected because login states intentionally do not enter the Cloud incident path, which would hide a persistent full-page security block.

### 2. Use dedicated environment-scoped customer-auth routes

Cloud SHALL expose:

- `GET /environments/:envKey/risk-state`
- `POST /environments/:envKey/risk-state/recover`

Both routes authenticate the customer, re-check enabled state and ownership, resolve the persistent environment binding, and verify the bound account is Facebook. Responses expose `envKey`, public risk state timestamps/status, and recovery result only; they never expose `accountId`.

The recovery request accepts an empty object only. Cloud generates a deterministic audit reason from the authenticated user and environment. Dedicated routes were chosen over putting mutable risk state in `/my-environments`: they keep the authorization list small, allow a fresh read for the selected stopped environment, and avoid coupling all-environment list latency to controller reads.

### 3. Add a restricted-only atomic controller operation

`RiskController` SHALL add a serialized helper that:

- requires a non-empty server-generated reason;
- changes `restricted` to `normal` through `operator_override_recover` and persists the resulting state;
- treats an already-`normal` request as an idempotent no-op;
- refuses `warned` and `frozen` without mutation.

After an accepted recovery, Cloud SHALL call the existing `resumeEdgesForAccount` path and return the real number of resumed edges. This mirrors the existing manual resume boundary while keeping the state machine as the single writer. Direct route-side `getState()` followed by `applySignal()` was rejected because the two calls are not one serialized decision and could race another risk transition.

### 4. Render one compact selected-environment action

Electron SHALL add one static row below the existing slow-start row inside “今日进展”:

`[解除受限] [?]`

The explicit `账号受限` label remains in the selected environment's title health result, risk detail, and environment rail; the recovery row does not duplicate it. The row appears only for the selected Facebook environment whose effective authoritative state is `restricted`. Live connected environments use the live Cloud snapshot. Stopped/disconnected environments use a short-lived env-scoped HTTP read cache; HTTP failure does not overwrite the last honest status or invent `normal`.

The button uses the named preload/main IPC boundary and passes only `envKey`. A native confirmation explains that the customer must first confirm Facebook is usable. While the request is pending, the same button is disabled and changes label; success consumes the Cloud write-after receipt immediately, while failure leaves the restricted state visible with an inline error. The `?` panel explains what triggers restriction, that only the current environment is affected, and that a still-present platform block can stop work again.

### 5. Make labels explicit without enlarging the surface

The title health result, risk detail row, and environment rail SHALL say `账号受限` instead of `节奏已调整` / `已调整节奏`. `warned` keeps the existing slowed-pacing language and `frozen` remains a separate stronger state.

The presence headline SHALL also prioritize `restricted` over the generic `session=resting` fallback. A risk-triggered cold standby is not a completed browse round and cannot honestly promise the normal rest-window resume time, so the UI says that automatic operation is paused and points to recovery instead of showing “本轮完成” or an auto-resume countdown.

## Risks / Trade-offs

- [Generic checkpoint becomes `unknown`, so Cloud escalation is delayed by one confirmation interval] → Local automation still stops immediately; only the Cloud report is delayed, filtering transient navigations without weakening true captcha detection.
- [A customer can click recovery before Facebook is usable] → Require explicit confirmation, resume only after a Cloud-accepted write, and keep Edge's local blocker checks intact; the UI never claims the platform restriction itself was solved.
- [A stopped environment has no live snapshot] → Use a fresh ownership-scoped Cloud read and never trust the locally initialized `normal` fallback for recovery visibility.
- [Recovery and a new risk signal can race] → Serialize the restricted-only decision inside the account's existing `RiskController`; a later valid signal remains able to restrict the account again.
- [Cloud deploy alone does not update desktop classification/UI] → Deploy the backward-compatible Cloud routes to `dev`, but report the Edge source-only boundary honestly until a desktop build containing the change is installed.

## Migration Plan

1. Land and deploy the backward-compatible Cloud customer-auth routes to `dev` from the clean `master` checkout.
2. Land Edge classifier and Electron source changes without building an installer.
3. Validate route authorization and controller transitions with synthetic accounts only; do not manufacture a real Facebook checkpoint or mutate a real account merely for proof.
4. Rollback is code-only: revert the Cloud and Edge commits. No schema rollback is required.

## Open Questions

None. The user selected the compact one-button UI and accepted a help popover instead of a larger recovery card.
