## Context

Current captcha handling is intentionally conservative:

- edge detects captcha/unknown overlays, pauses local actions, and sends `risk.captcha_detected`.
- cloud migrates account risk state, pauses command delivery for that edge, and sends a Feishu notify-only alert.
- edge sends `risk.captcha_cleared` only after the DOM overlay is actually gone; cloud then resumes that edge.
- manually resolving an alert only closes the alert row. It does not resume edge delivery or change risk state.

The missing operator experience is the actual handling path. Operators must remote into the machine and click the AdsPower browser directly. The target experience is to let them operate from Feishu/cloud while preserving the original browser session as the only place where the challenge is answered.

## Goals / Non-Goals

**Goals:**

- Provide a cloud-hosted captcha assist page reachable from Feishu alerts.
- Let operators view a short-lived screenshot of the live captcha overlay from the affected edge.
- Let operators submit one or more manual click points that edge dispatches into the original browser session.
- Keep recovery honest: only edge DOM re-probe and `risk.captcha_cleared` may resume normal browsing.
- Keep the incident scoped to one edge/account/session and never broadcast click commands.
- Preserve existing risk semantics: detected still drives `restricted`; cleared does not auto-return to `normal`.

**Non-Goals:**

- Do not automatically solve captcha images or call third-party captcha-solving services.
- Do not open a second cloud browser or replay the account session outside AdsPower.
- Do not store long-lived screenshots or include screenshots in Feishu cards.
- Do not make manual alert resolution equivalent to captcha clearance.
- Do not bypass platform challenge controls by mutating DOM state; assist actions must be normal input events.

## Decisions

### 1. Incident-scoped remote assist instead of cloud browser takeover

Create a `CaptchaAssistIncident` when `CaptchaCoordinator.onDetected()` accepts a captcha/unknown event. It contains:

- `incidentId`
- `edgeId`, `accountId`, `machineLabel`, `firstDetectedUrl`
- `kind`, `riskStatus`, `alertId?`
- `state`: `open | capture_pending | ready | click_pending | still_blocked | cleared | expired | failed`
- `createdAt`, `expiresAt`
- latest `snapshotId`, `imageMime`, `imageData`, `imageWidth`, `imageHeight`, and coordinate metadata

The assist page operates only through this incident. It never creates its own browser context.

Alternative considered: send the operator directly to a remote desktop URL. That is useful as fallback, but it does not improve the normal workflow or allow structured auditing.

### 2. Short-lived screenshot capture via edge command

Add protocol messages for the assist channel:

- `captcha.assist.capture` cloud -> edge
- `captcha.assist.snapshot` edge -> cloud
- `captcha.assist.click` cloud -> edge
- `captcha.assist.click_result` edge -> cloud

These messages are protocol-v2 changes and must be mirrored across edge/cloud protocol definitions, docs, tests, and active command routing.

`captcha.assist.capture` is allowed through the paused-edge transport gate, the same way `session.end` is allowed, because captcha assist is the recovery path. Ordinary browse/interaction commands remain blocked.

The edge side captures a cropped screenshot around the primary blocking overlay when possible. It returns coordinate metadata owned by edge, for example:

- viewport size in CSS pixels
- crop rectangle in CSS pixels
- rendered image dimensions
- device scale factor when relevant
- `snapshotId` and `capturedAt`

Cloud stores only the latest snapshot per incident with a short TTL. If cloud restarts, the incident can be recreated by the next captcha report or the operator can use the existing remote-desktop fallback.

Alternative considered: edge uploads images to object storage. That is heavier and unnecessary for MVP; it can be added later if screenshots become too large for WS frames.

### 3. Operator clicks are normalized and edge-owned

The console assist page displays the image and records a click sequence as normalized coordinates relative to the displayed image/crop, for example `{x: 0.37, y: 0.64}`.

Cloud sends those normalized coordinates plus `incidentId` and `snapshotId` to the edge. Edge validates:

- the command targets its own `edgeId`
- the page is still in captcha/unknown state
- the snapshot is recent enough, or a fresh capture still maps to the same overlay area
- all coordinates are within bounds

Edge maps coordinates to viewport CSS pixels and dispatches real CDP input events with existing humanized mouse movement where practical. It does not call `.click()` on DOM nodes for the captcha challenge.

Alternative considered: cloud maps coordinates to viewport pixels. Rejected because edge owns device scale factor, current viewport, and the fresh DOM state.

### 4. Clearance remains edge-driven

After every assist click sequence, edge waits a bounded settle period and re-runs the overlay monitor fresh probe.

- If the blocking overlay is gone, edge sends `risk.captcha_cleared` and `captcha.assist.click_result{status:'cleared'}`.
- If the overlay remains, edge sends `captcha.assist.click_result{status:'still_blocked'}` and may include a refreshed snapshot.
- If the edge is offline, the snapshot is stale, the page changed, or CDP fails, the result is an honest failure.

Cloud must not call `resumeEdge()` merely because it accepted a click request. The existing `onCleared()` path remains the only normal resume path.

### 5. Feishu card links to a protected assist page

`buildAlertCard` already supports an action button. CaptchaCoordinator should attach an `actionUrl` to captcha/unknown cards when assist is enabled.

The URL should contain either:

- a short-lived, signed `captcha_assist` token scoped to one `incidentId`, or
- a normal console URL that requires JWT login and then opens the incident.

MVP should support signed scoped tokens so mobile Feishu users can open the page without needing broad admin credentials. The token must only allow read/click/refresh for that single incident and must expire quickly.

Feishu remains notify-only. There is no approval signal file and no button that declares the incident solved.

### 6. UI behavior

The assist page is a focused tool, not a dashboard landing page:

- header: account display name, edge/machine, risk state, URL, timer/expiry
- main area: screenshot with click markers
- controls: refresh capture, undo last point, submit clicks, open remote desktop fallback
- status rail: open/ready/clicking/still blocked/cleared/expired/error

When cleared, the page states that the browser resumed only after edge reported clearance. When still blocked, it shows the refreshed screenshot and keeps the incident open.

## Risks / Trade-offs

- Screenshot/click race with dynamic captcha UI -> require `snapshotId`, short freshness windows, and refresh before retry.
- Large image payload over WS -> crop to overlay first, cap dimensions/quality, and reject over-limit frames honestly.
- Operator misclicks -> support undo before submit, show markers, and allow retry only while edge still reports blocked.
- Security exposure from Feishu deep links -> signed scoped token, short TTL, no account-management permissions, audit all actions.
- Assist commands bypass paused-edge transport gate -> whitelist only `captcha.assist.*` capture/click messages and keep browse/interaction commands blocked.
- Cloud restart loses in-memory snapshot -> incident becomes `failed/expired`; operator can refresh if edge is still online or fall back to remote desktop.
- Captcha provider treats remote CDP input as suspicious -> use the same headful browser and humanized input path as existing edge actions; do not inject DOM shortcuts.

## Migration Plan

1. Add OpenSpec contracts and protocol docs first.
2. Implement cloud incident registry, Feishu action URL generation, and protected assist API behind a feature flag such as `AIDCP_CAPTCHA_ASSIST_ENABLED`.
3. Implement edge capture/click handlers and protocol tests while keeping existing remote desktop alert text as fallback.
4. Implement console assist page and focused cloud/edge tests.
5. Deploy to `dev`, trigger a mock captcha incident, verify capture -> click -> still_blocked/cleared paths, and confirm normal browse commands remain paused until `risk.captcha_cleared`.
6. Keep feature disabled for `ol` until explicitly requested.

Rollback is feature-flag off: Feishu cards return to remote-desktop-only handling and existing captcha incident semantics remain unchanged.

## Open Questions

- Should assist screenshots be stored only in memory, or should metadata be persisted in `alerts` / a new append-only incident table for audit?
- What is the maximum acceptable image size over the edge-cloud WS before switching to object storage?
- Should the first version allow arbitrary click sequences only, or also provide an optional 3x3 grid overlay for common image-selection challenges?
