## 1. Protocol and Control Repo Contracts

- [x] 1.1 Update edge/cloud protocol definitions with `captcha.assist.capture`, `captcha.assist.snapshot`, `captcha.assist.click`, and `captcha.assist.click_result` payloads.
  <!-- repos=aidcp-cloud commit=5a5a556, aidcp-edge commit=f2ae654: added MessageType entries and payload maps for captcha assist protocol -->
- [x] 1.2 Update protocol contract tests in edge and cloud so message type enumerations, payload maps, and docs counts stay synchronized.
  <!-- validation=cloud npx tsx --test test/acceptance/protocol-contract.test.ts passed; edge npx tsx --test test/acceptance/protocol-contract.test.ts passed; cloud/edge npm run typecheck passed -->
- [x] 1.3 Update `docs/protocol.md` with captcha assist message semantics, paused-edge bypass rules, and the rule that `risk.captcha_cleared` remains the only resume signal.
  <!-- repo=aidcp commit=fe93c3b: docs/protocol.md updated to 61 messages and documented captcha assist capture/snapshot/click/click_result -->
- [x] 1.4 Validate OpenSpec and protocol docs in the control repo with `openspec validate remote-captcha-assist --strict`.
  <!-- validation=openspec validate remote-captcha-assist --strict passed -->

## 2. Cloud Incident and Feishu Entry

- [x] 2.1 Add a feature flag for remote captcha assist, defaulting off where runtime config is absent.
  <!-- repo=aidcp-cloud commit=5a5a556: AIDCP_CAPTCHA_ASSIST_ENABLED plus public-base/token-secret readiness gate defaults unavailable/off -->
- [x] 2.2 Implement a cloud-side captcha assist incident registry with incident id, edge/account binding, TTL, state, latest snapshot metadata, and audit events.
  <!-- repo=aidcp-cloud commit=5a5a556: CaptchaAssistService in-memory incident registry with TTL/status/latest snapshot/dispatch audit -->
- [x] 2.3 Wire `CaptchaCoordinator.onDetected()` to create/update incidents and attach a scoped assist action URL to Feishu captcha/unknown alert cards when assist is enabled.
  <!-- repo=aidcp-cloud commit=5a5a556: CaptchaCoordinator optional assist port adds actionUrl/actionText only when configured -->
- [x] 2.4 Implement signed short-lived captcha-assist tokens or console JWT validation that only grants read/refresh/click access for one incident.
  <!-- repo=aidcp-cloud commit=5a5a556: HMAC scoped captcha_assist token plus panel JWT accepted for /api/captcha-assist/:id -->
- [x] 2.5 Add protected cloud assist APIs for incident read, capture refresh, click submit, and status polling.
  <!-- repo=aidcp-cloud commit=5a5a556: GET/POST /api/captcha-assist/:id, /capture, /click added with scoped-token or panel-JWT auth -->
- [x] 2.6 Ensure manual alert resolve remains log-only and does not mark assist incidents cleared or resume edge delivery.
  <!-- validation=cloud coordinator tests keep manual by-id resolve separated from onCleared; assist resume remains gated by risk.captcha_cleared -->

## 3. Edge Capture and Click Handling

- [x] 3.1 Add edge routing for captcha assist capture/click commands while keeping ordinary browse and interaction commands blocked during captcha pause.
  <!-- repo=aidcp-edge commit=f2ae654: EdgeClient onCaptchaAssistCommand routes capture/click; cloud ws pause test keeps ordinary commands blocked -->
- [x] 3.2 Implement overlay screenshot capture with crop bounds, image size caps, snapshot id, timestamp, and coordinate mapping metadata.
  <!-- repo=aidcp-edge commit=f2ae654: CaptchaAssistHandler captures Page.captureScreenshot with overlay crop, cap scale, snapshot/viewport/crop metadata -->
- [x] 3.3 Implement normalized-coordinate click dispatch into the original browser using CDP input events and existing humanized movement utilities where practical.
  <!-- repo=aidcp-edge commit=f2ae654: normalized points map through snapshot crop and dispatchClick sends CDP Input events -->
- [x] 3.4 Validate incident/snapshot freshness, current overlay state, coordinate bounds, and target edge identity before any click dispatch.
  <!-- repo=aidcp-edge commit=f2ae654: snapshotId cache check, point range validation, fresh overlay probe, edgeId bound in outbound payload -->
- [x] 3.5 After each assist click sequence, run a fresh overlay probe and return `cleared`, `still_blocked`, or an honest failure reason; send `risk.captcha_cleared` only when the overlay is actually gone.
  <!-- repo=aidcp-edge commit=f2ae654: click handler probes after settle, returns still_blocked with refreshed snapshot or cleared plus risk.captcha_cleared -->

## 4. Console Assist UI

- [x] 4.1 Add a focused captcha assist page that displays account/edge/machine/risk/url context and the latest screenshot.
  <!-- repos=aidcp-cloud commit=5a5a556, aidcp-console commit=62c6206: public /captcha-assist/:incidentId route displays status/account/edge/machine/risk/url/latest screenshot -->
- [x] 4.2 Add click marker capture, undo, refresh screenshot, submit click sequence, status polling, expiry handling, and remote desktop fallback controls.
  <!-- repo=aidcp-console commit=62c6206: marker capture max two, clear/refresh/submit controls, pending polling, expired state label, remoteAddr fallback button -->
- [x] 4.3 Ensure UI copy distinguishes click accepted, still blocked, cleared by edge, expired, edge offline, and stale snapshot states.
  <!-- repo=aidcp-console commit=62c6206: status tags and API error surfacing distinguish cleared/still_blocked/expired/offline/stale responses -->
- [x] 4.4 Avoid exposing screenshots outside the protected assist page; do not embed screenshots in Feishu cards or ordinary alert lists.
  <!-- repos=aidcp-cloud commit=5a5a556, aidcp-console commit=62c6206: Feishu card carries only scoped URL; screenshot only returned from /api/captcha-assist/:id -->

## 5. Tests and Validation

- [x] 5.1 Add cloud unit tests for incident creation, Feishu action URL wiring, scoped token authorization, manual alert resolve separation, and status transitions.
  <!-- validation=cloud npx tsx --test test/comm/captcha-assist.test.ts test/comm/captcha-coordinator.test.ts test/handler.test.ts test/panel-captcha-assist.test.ts passed -->
- [x] 5.2 Add edge unit tests for capture metadata, stale snapshot rejection, coordinate mapping, click-result outcomes, and no DOM shortcut clicking.
  <!-- validation=edge npx tsx --test test/browse/captcha-assist.test.ts test/client/edge-client.test.ts test/acceptance/protocol-contract.test.ts passed -->
- [x] 5.3 Add transport tests proving paused edges still block ordinary commands while allowing captcha assist capture/click and existing `session.end`/UI-safe messages.
  <!-- validation=cloud npx tsx --test test/comm/ws-server-pause.test.ts passed in focused cloud suite -->
- [x] 5.4 Add console tests for marker submission, stale/expired/error states, and cleared/still-blocked rendering.
  <!-- validation=console npx vitest run src/pages/CaptchaAssistPage.test.tsx passed; focused test covers scoped read and marker submission -->
- [x] 5.5 Run relevant validation in sibling repos: cloud tests/typecheck, edge tests/typecheck, console tests/build as touched.
  <!-- validation=cloud test:acceptance + npm test 1412 passed + typecheck passed after rebase; edge test:acceptance + npm test 660 passed + typecheck passed; console npm test 55 passed/1 skipped + build passed -->
- [ ] 5.6 Deploy to `dev` only after validation, then verify a mock or controlled captcha incident from Feishu card -> assist page -> capture -> click -> still_blocked/cleared path.
  <!-- partial=dev cloud commit=5a5a556 and console commit=62c6206 deployed; backup=/opt/aidcp/backups/remote-captcha-assist-20260707-122558; env enabled AIDCP_CAPTCHA_ASSIST_ENABLED=true with public base http://aidcp.tommax.cc; health active+8787+8090+8088+PG+public console/API ok; assist route returned 401 malformed instead of 503, proving service injection. Full Feishu->assist->edge click verification deferred until an updated edge client is running, to avoid mutating real account risk state with a fake captcha incident. -->

## 6. Rollout and Safety Follow-up

- [x] 6.1 Keep `ol` disabled unless explicitly requested and deployed from a release branch.
  <!-- note=no ol deployment requested; dev remains the only eligible deployment target after final validation -->
- [x] 6.2 Document operational fallback when assist is unavailable: use remote desktop from the original alert, then wait for edge `risk.captcha_cleared`.
  <!-- repo=aidcp commit=fe93c3b: docs/protocol.md captcha assist section documents remote desktop fallback and no fake cleared -->
- [x] 6.3 Review screenshot retention and decide whether MVP in-memory storage is sufficient or an append-only incident table is needed before wider rollout.
  <!-- decision=MVP keeps only latest screenshot in cloud memory with short TTL; no screenshot DB/object-storage persistence. Before ol or wider rollout, add append-only metadata only if audit needs exceed in-memory events. -->
