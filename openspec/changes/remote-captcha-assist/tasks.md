## 1. Protocol and Control Repo Contracts

- [ ] 1.1 Update edge/cloud protocol definitions with `captcha.assist.capture`, `captcha.assist.snapshot`, `captcha.assist.click`, and `captcha.assist.click_result` payloads.
- [ ] 1.2 Update protocol contract tests in edge and cloud so message type enumerations, payload maps, and docs counts stay synchronized.
- [ ] 1.3 Update `docs/protocol.md` with captcha assist message semantics, paused-edge bypass rules, and the rule that `risk.captcha_cleared` remains the only resume signal.
- [ ] 1.4 Validate OpenSpec and protocol docs in the control repo with `openspec validate remote-captcha-assist --strict`.

## 2. Cloud Incident and Feishu Entry

- [ ] 2.1 Add a feature flag for remote captcha assist, defaulting off where runtime config is absent.
- [ ] 2.2 Implement a cloud-side captcha assist incident registry with incident id, edge/account binding, TTL, state, latest snapshot metadata, and audit events.
- [ ] 2.3 Wire `CaptchaCoordinator.onDetected()` to create/update incidents and attach a scoped assist action URL to Feishu captcha/unknown alert cards when assist is enabled.
- [ ] 2.4 Implement signed short-lived captcha-assist tokens or console JWT validation that only grants read/refresh/click access for one incident.
- [ ] 2.5 Add protected cloud assist APIs for incident read, capture refresh, click submit, and status polling.
- [ ] 2.6 Ensure manual alert resolve remains log-only and does not mark assist incidents cleared or resume edge delivery.

## 3. Edge Capture and Click Handling

- [ ] 3.1 Add edge routing for captcha assist capture/click commands while keeping ordinary browse and interaction commands blocked during captcha pause.
- [ ] 3.2 Implement overlay screenshot capture with crop bounds, image size caps, snapshot id, timestamp, and coordinate mapping metadata.
- [ ] 3.3 Implement normalized-coordinate click dispatch into the original browser using CDP input events and existing humanized movement utilities where practical.
- [ ] 3.4 Validate incident/snapshot freshness, current overlay state, coordinate bounds, and target edge identity before any click dispatch.
- [ ] 3.5 After each assist click sequence, run a fresh overlay probe and return `cleared`, `still_blocked`, or an honest failure reason; send `risk.captcha_cleared` only when the overlay is actually gone.

## 4. Console Assist UI

- [ ] 4.1 Add a focused captcha assist page that displays account/edge/machine/risk/url context and the latest screenshot.
- [ ] 4.2 Add click marker capture, undo, refresh screenshot, submit click sequence, status polling, expiry handling, and remote desktop fallback controls.
- [ ] 4.3 Ensure UI copy distinguishes click accepted, still blocked, cleared by edge, expired, edge offline, and stale snapshot states.
- [ ] 4.4 Avoid exposing screenshots outside the protected assist page; do not embed screenshots in Feishu cards or ordinary alert lists.

## 5. Tests and Validation

- [ ] 5.1 Add cloud unit tests for incident creation, Feishu action URL wiring, scoped token authorization, manual alert resolve separation, and status transitions.
- [ ] 5.2 Add edge unit tests for capture metadata, stale snapshot rejection, coordinate mapping, click-result outcomes, and no DOM shortcut clicking.
- [ ] 5.3 Add transport tests proving paused edges still block ordinary commands while allowing captcha assist capture/click and existing `session.end`/UI-safe messages.
- [ ] 5.4 Add console tests for marker submission, stale/expired/error states, and cleared/still-blocked rendering.
- [ ] 5.5 Run relevant validation in sibling repos: cloud tests/typecheck, edge tests/typecheck, console tests/build as touched.
- [ ] 5.6 Deploy to `dev` only after validation, then verify a mock or controlled captcha incident from Feishu card -> assist page -> capture -> click -> still_blocked/cleared path.

## 6. Rollout and Safety Follow-up

- [ ] 6.1 Keep `ol` disabled unless explicitly requested and deployed from a release branch.
- [ ] 6.2 Document operational fallback when assist is unavailable: use remote desktop from the original alert, then wait for edge `risk.captcha_cleared`.
- [ ] 6.3 Review screenshot retention and decide whether MVP in-memory storage is sufficient or an append-only incident table is needed before wider rollout.
