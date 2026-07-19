## 1. Isolated implementation setup

- [x] 1.1 Create the matching `aidcp-edge` worktree and `codex/wechat-auth-liveness-honesty` branch from current `origin/master`; install a physical worktree-local dependency tree with `npm ci --prefer-offline`. <!-- /Users/baitianxing/codes/aidcp-edge.wt/wechat-auth-liveness-honesty; npm ci installed 365 packages with a physical local node_modules -->

## 2. Verified control-plane liveness

- [x] 2.1 Add a single-flight, bounded video-channel control-plane heartbeat that logs success only after a matching existing `ping` / `pong` round trip and stops with the runtime lifecycle. <!-- aidcp-edge: src/wechat-channels/control-plane-heartbeat.ts -->
- [x] 2.2 Wire the verified heartbeat into the video-channel runtime independently of browser/auth/business-sync state without changing auth or capability truth. <!-- aidcp-edge: runtime starts after Cloud hello and stops before client shutdown; auth/capabilities untouched -->
- [x] 2.3 Add focused tests for successful proof, failure/timeout silence, overlap suppression, lifecycle stop, and benign desktop log classification. <!-- 51 focused tests passed including control-plane-heartbeat and core-log-severity -->

## 3. Honest browser-auth failure state

- [x] 3.1 Roll `sidecar.open()` failure back from `browser_opening` to `reauth_required` for an expired stored session or `browser_login_required` for first login, preserving `WECHAT_AUTH_REQUIRED` and the existing recovery action. <!-- aidcp-edge: auth-session.ts; both branches covered by focused tests -->
- [x] 3.2 Add whitelist-only browser-sidecar diagnostics for provider/operation/kind and safe HTTP/provider codes; never log raw response text, credentials, session material, or query strings. <!-- aidcp-edge: safeBrowserSidecarDiagnostic emits only fixed fields and safe tokens -->
- [x] 3.3 Add focused auth and sidecar tests proving failure no longer remains `authenticating`, the runtime reports `WECHAT_AUTH_REQUIRED`, and sensitive error text is not emitted. <!-- auth-session focused suite passed; typecheck passed -->

## 4. Validation and integration

- [x] 4.1 Run focused video-channel, Electron fleet/log-severity, and runtime tests, then `npm run test:acceptance`, full `npm test`, `npm run typecheck`, and `npm run build:dist` in the Edge worktree. <!-- focused 51/51; acceptance 25 passed + 1 gated skip; full dot-reporter suite exit 0; typecheck/build:dist exit 0; git diff --check clean -->
- [x] 4.2 Record Edge commit SHA and validation evidence in this checklist, run `openspec validate wechat-auth-liveness-honesty --strict`, and commit the control artifacts. <!-- aidcp-edge d94717e; validation: focused 51/51, acceptance 25 passed + 1 gated skip, full suite exit 0, typecheck/build:dist/diff-check clean -->
- [x] 4.3 Rebase and fast-forward land the Edge change onto current `origin/master`, push without force, synchronize the canonical checkout, and rebuild canonical `dist` without packaging an installer. <!-- aidcp-edge d94717e pushed origin/master; canonical master fast-forwarded to the same SHA; npm run build:dist exit 0; no installer built -->
- [x] 4.4 Confirm the `dev` target boundary and document that no ECS service deploy is required because Cloud/protocol code is unchanged; report whether the already-running desktop process was restarted or remains pending safe operator restart. <!-- scripts/deploy-target dev --check passed; no SSH/rsync/ECS restart because this is Edge-only with no protocol change; Electron PID 94944 started 2026-07-19 19:02:40 before the canonical rebuild and was deliberately left running to avoid disrupting other environments, so runtime pickup remains pending a safe desktop restart -->
