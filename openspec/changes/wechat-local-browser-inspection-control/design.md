## Context

The current interaction workspace renders `auth.browserState` beside the lifecycle controls and only exposes browser control when `auth.status=active`. Clicking the button calls the Cloud customer API, which routes to the unique online Edge and asks the engine-owned WeChat auth session to open or close its browser sidecar.

That route is appropriate for engine-owned API-only foreground/background control, but it is the wrong dependency chain for an operator who only wants to inspect the local AdsPower profile. The Electron main process already owns the trusted customer-visible environment set, the local profile mapping, the bundled AdsPower runtime, and the serialized LocalAPI client.

## Goals / Non-Goals

**Goals**

- Open or reuse the selected local AdsPower profile without requiring Cloud reachability, an online engine, or active WeChat authentication.
- Keep engine lifecycle and WeChat authentication truthful and independent from the manual browser action.
- Make engine connectivity and WeChat authentication visually primary.
- Preserve environment ownership, platform scoping, LocalAPI throttling, kernel readiness, and honest errors.

**Non-Goals**

- Closing the browser from the manual inspection area.
- Claiming that a visible browser is logged in or that authentication passed.
- Starting or attaching the engine after opening the browser.
- Removing the existing Cloud browser-control endpoint or changing the WeChat auth-session sidecar protocol.
- Packaging a desktop installer.

## Decisions

### 1. Add a narrow local-open IPC instead of reusing the Cloud browser endpoint

The renderer sends only `{ envKey }` to `interaction:browser:open-local`. The main process validates the DTO, current customer session, allowed environment set, authoritative `wechat_channels` platform, and a matching local AdsPower handle. It derives the profile id, start URL, API base, API key, launch arguments, and kernel version itself.

The handler calls the bundled AdsPower service/kernel ensure functions with no engine UI handle, then uses the main-process AdsPower LocalAPI client to issue the single allowed `browser/start`. It MUST NOT call `interactionCustomerRequest`, `startEdge`, `queueStartEnv`, `resumeEdge`, or another engine lifecycle function.

### 2. Extend the existing main-process LocalAPI serialization boundary

The existing `ads-local-api.cjs` instance already serializes all Electron-main LocalAPI requests at the AdsPower rate limit. Add one explicit `openProfileForInspection` method to that same client instead of creating a second throttle queue. The method accepts a trusted profile id and trusted start URL, emits fixed safe launch arguments, never accepts arbitrary renderer input, and exposes no stop/close operation.

The existing probe/list operations remain read-only. The new write exception is limited to the named manual-inspection method.

### 3. Opening is independent but later engine startup may adopt the same profile

After a successful local open, the shell marks the local handle as `browserAlreadyRunning`. A later explicit engine start follows the existing running-profile adoption path and MUST NOT intentionally launch a second profile instance. The manual action itself does not start or attach the engine.

### 4. Authentication remains authoritative only from the engine projection

`browser/start` success means only that the local profile was opened or reused. The renderer shows a notice that login state is determined by the separate WeChat authentication status. It does not mutate `state.auth`, synthesize `active`, or poll Cloud for browser confirmation.

### 5. Status hierarchy separates core state from auxiliary state

The overview shows two primary chips:

- Engine: connected, connecting, paused, stopped, or abnormal, derived from local engine and Cloud connectivity state.
- WeChat Channels: authenticated, waiting for login, reauthentication required, verification required, checking, degraded, disabled, or unconfirmed, derived from the interaction auth projection.

Browser state moves to a secondary manual-inspection row beside the always-visible local-open button. Browser wording identifies it as an automation/browser report and never presents an unconfirmed browser state as the primary workspace status.

## Error Handling

- Invalid or out-of-scope environment: fail closed with `INTERACTION_SCOPE_MISMATCH`.
- Missing local AdsPower handle: fail closed; do not fall back to the selected environment.
- Runtime/kernel/LocalAPI failure: return an honest retryable local error and keep engine/auth state unchanged.
- AdsPower success without a valid debug port: treat as failure; do not claim the browser opened.

## Validation

- AdsPower LocalAPI unit tests for fixed `browser/start`, returned debug port, error handling, and shared serialization.
- IPC source-contract tests for named preload exposure, authoritative scope validation, fixed local path, and absence of Cloud/engine calls.
- Interaction workspace tests for primary engine/auth chips, secondary browser placement, button availability while auth/engine are unavailable, and local-only request shape.
- Focused Electron tests plus `npm run typecheck`, followed by OpenSpec strict validation.
