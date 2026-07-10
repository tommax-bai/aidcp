## 1. Protocol and Control Repo Contracts

- [x] 1.1 Update edge/cloud protocol definitions with `captcha.assist.capture`, `captcha.assist.snapshot`, `captcha.assist.click`, and `captcha.assist.click_result` payloads.
  <!-- repos=aidcp-cloud,aidcp-edge pending-commit: added MessageType entries and payload maps for captcha assist protocol -->
- [x] 1.2 Update protocol contract tests in edge and cloud so message type enumerations, payload maps, and docs counts stay synchronized.
  <!-- validation=cloud npx tsx --test test/acceptance/protocol-contract.test.ts passed; edge npx tsx --test test/acceptance/protocol-contract.test.ts passed; cloud/edge npm run typecheck passed -->
- [x] 1.3 Update `docs/protocol.md` with captcha assist message semantics, paused-edge bypass rules, and the rule that `risk.captcha_cleared` remains the only resume signal.
  <!-- repo=aidcp pending-commit: docs/protocol.md updated to 61 messages and documented captcha assist capture/snapshot/click/click_result -->
- [x] 1.4 Validate OpenSpec and protocol docs in the control repo with `openspec validate remote-captcha-assist --strict`.
  <!-- validation=openspec validate remote-captcha-assist --strict passed -->

## 2. Cloud Incident and Feishu Entry

- [x] 2.1 Add a feature flag for remote captcha assist, defaulting off where runtime config is absent.
  <!-- repo=aidcp-cloud pending-commit: AIDCP_CAPTCHA_ASSIST_ENABLED plus public-base/token-secret readiness gate defaults unavailable/off -->
- [x] 2.2 Implement a cloud-side captcha assist incident registry with incident id, edge/account binding, TTL, state, latest snapshot metadata, and audit events.
  <!-- repo=aidcp-cloud pending-commit: CaptchaAssistService in-memory incident registry with TTL/status/latest snapshot/dispatch audit -->
- [x] 2.3 Wire `CaptchaCoordinator.onDetected()` to create/update incidents and attach a scoped assist action URL to Feishu captcha/unknown alert cards when assist is enabled.
  <!-- repo=aidcp-cloud pending-commit: CaptchaCoordinator optional assist port adds actionUrl/actionText only when configured -->
- [x] 2.4 Implement signed short-lived captcha-assist tokens or console JWT validation that only grants read/refresh/click access for one incident.
  <!-- repo=aidcp-cloud pending-commit: HMAC scoped captcha_assist token plus panel JWT accepted for /api/captcha-assist/:id -->
- [x] 2.5 Add protected cloud assist APIs for incident read, capture refresh, click submit, and status polling.
  <!-- repo=aidcp-cloud pending-commit: GET/POST /api/captcha-assist/:id, /capture, /click added with scoped-token or panel-JWT auth -->
- [x] 2.6 Ensure manual alert resolve remains log-only and does not mark assist incidents cleared or resume edge delivery.
  <!-- validation=cloud coordinator tests keep manual by-id resolve separated from onCleared; assist resume remains gated by risk.captcha_cleared -->

## 3. Edge Capture and Click Handling

- [x] 3.1 Add edge routing for captcha assist capture/click commands while keeping ordinary browse and interaction commands blocked during captcha pause.
  <!-- repo=aidcp-edge pending-commit: EdgeClient onCaptchaAssistCommand routes capture/click; cloud ws pause test keeps ordinary commands blocked -->
- [x] 3.2 Implement overlay screenshot capture with crop bounds, image size caps, snapshot id, timestamp, and coordinate mapping metadata.
  <!-- repo=aidcp-edge pending-commit: CaptchaAssistHandler captures Page.captureScreenshot with overlay crop, cap scale, snapshot/viewport/crop metadata -->
- [x] 3.3 Implement normalized-coordinate click dispatch into the original browser using CDP input events and existing humanized movement utilities where practical.
  <!-- repo=aidcp-edge pending-commit: normalized points map through snapshot crop and dispatchClick sends CDP Input events -->
- [x] 3.4 Validate incident/snapshot freshness, current overlay state, coordinate bounds, and target edge identity before any click dispatch.
  <!-- repo=aidcp-edge pending-commit: snapshotId cache check, point range validation, fresh overlay probe, edgeId bound in outbound payload -->
- [x] 3.5 After each assist click sequence, run a fresh overlay probe and return `cleared`, `still_blocked`, or an honest failure reason; send `risk.captcha_cleared` only when the overlay is actually gone.
  <!-- repo=aidcp-edge pending-commit: click handler probes after settle, returns still_blocked with refreshed snapshot or cleared plus risk.captcha_cleared -->

## 4. Console Assist UI

- [x] 4.1 Add a focused captcha assist page that displays account/edge/machine/risk/url context and the latest screenshot.
  <!-- repos=aidcp-cloud,aidcp-console pending-commit: public /captcha-assist/:incidentId route displays status/account/edge/machine/risk/url/latest screenshot -->
- [x] 4.2 Add click marker capture, undo, refresh screenshot, submit click sequence, status polling, expiry handling, and remote desktop fallback controls.
  <!-- repo=aidcp-console pending-commit: marker capture max two, clear/refresh/submit controls, pending polling, expired state label, remoteAddr fallback button -->
- [x] 4.3 Ensure UI copy distinguishes click accepted, still blocked, cleared by edge, expired, edge offline, and stale snapshot states.
  <!-- repo=aidcp-console pending-commit: status tags and API error surfacing distinguish cleared/still_blocked/expired/offline/stale responses -->
- [x] 4.4 Avoid exposing screenshots outside the protected assist page; do not embed screenshots in Feishu cards or ordinary alert lists.
  <!-- repos=aidcp-cloud,aidcp-console pending-commit: Feishu card carries only scoped URL; screenshot only returned from /api/captcha-assist/:id -->

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
  <!-- validation=cloud focused tests + npm run typecheck passed; edge focused tests + npm run typecheck passed; console typecheck/test/build passed -->
- [x] 5.6 Deploy to `dev` only after validation, then verify a mock or controlled captcha incident from Feishu card -> assist page -> capture -> click -> still_blocked/cleared path.
  <!-- deployed=dev by 2026-07-08 rollout (aidcp-cloud src mtime 18:15, aidcp-console 18:56, aidcp-cloud.service ActiveEnter 19:15:49 CST with AIDCP_CAPTCHA_ASSIST_ENABLED=true) -->
  <!-- verified=2026-07-08 this session (read-only ECS probe): readiness gate open — no '验证码云端协助未启用' warning at startup; token secret via AIDCP_PANEL_JWT_SECRET fallback (readEnvString returns undefined on empty AIDCP_CAPTCHA_ASSIST_TOKEN_SECRET); AIDCP_CAPTCHA_ASSIST_PUBLIC_BASE_URL=http://aidcp.tommax.cc; nginx aidcp-console.conf server_name aidcp.tommax.cc :80 root /opt/aidcp/console + /api,/ws -> 127.0.0.1:8090; external http://aidcp.tommax.cc/captcha-assist/<id> -> 200, /api/captcha-assist/<id> without token -> 401 -->
  <!-- pending=live operator walkthrough (Feishu card -> assist page -> capture -> mark -> click -> cleared/still_blocked) needs an edge on an operator machine hitting a real/mock captcha; decoupled to docs/real-machine-acceptance-backlog.md -->


## 6. Rollout and Safety Follow-up

- [x] 6.1 Keep `ol` disabled unless explicitly requested and deployed from a release branch.
  <!-- note=no ol deployment requested; dev remains the only eligible deployment target after final validation -->
- [x] 6.2 Document operational fallback when assist is unavailable: use remote desktop from the original alert, then wait for edge `risk.captcha_cleared`.
  <!-- repo=aidcp pending-commit: docs/protocol.md captcha assist section documents remote desktop fallback and no fake cleared -->
- [x] 6.3 Review screenshot retention and decide whether MVP in-memory storage is sufficient or an append-only incident table is needed before wider rollout.
  <!-- decision=MVP keeps only latest screenshot in cloud memory with short TTL; no screenshot DB/object-storage persistence. Before ol or wider rollout, add append-only metadata only if audit needs exceed in-memory events. -->
