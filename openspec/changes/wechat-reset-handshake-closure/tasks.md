## 1. Cloud handshake admission

- [x] 1.1 Move Edge WebSocket listening after connection-runtime initialization and add a startup-order regression test.
- [x] 1.2 Register only successful welcome connections, close failed hello sockets, and cover rejected/error hello routing behavior.

## 2. Edge handshake and reset truth

- [x] 2.1 Validate hello responses as a non-empty welcome before committing connection state, with initial-connect and reconnect regression tests.
- [x] 2.2 Track per-channel reset baselines, distinguish dispatched/skipped/completed states, and cover overlapping channel evidence plus honest copy.

## 3. Validation and delivery

- [x] 3.1 Run Cloud and Edge focused tests plus typecheck; run the required acceptance/full safety suites for the touched protocol and interaction paths.
  <!-- Final rebased heads: Cloud 8ccf3e0, focused 8/8, acceptance 59/59, full 2543 pass / 0 fail / 8 gated skips, typecheck passed. Edge 08cc0a6, focused interaction + reconnect 52/52, acceptance 25/25, full 1861/1861, typecheck passed. -->
- [x] 3.2 Run `openspec validate wechat-reset-handshake-closure --strict`, record concise repo/commit/validation/deployment evidence, and keep unrelated worktree changes untouched.
  <!-- Strict validation passed before and after implementation. The unrelated canonical `publish-risk-quota-denial-message` directory remained untracked and untouched. -->
- [x] 3.3 Rebase, fast-forward merge and push control/Cloud/Edge default branches without force; deploy Cloud to `dev` after target preflight and verify service, listeners, health, logs, PostgreSQL, Feishu, and unrelated services.
  <!-- Defaults pushed without force: Cloud master 8ccf3e0, Edge master 08cc0a6, control main 737755b. DEV target preflight passed; backup cloud.20260719-171235.tgz plus env copy created; Cloud restarted active with 8787/8090/8091/8088 listeners, four HTTP 200 checks, PostgreSQL SELECT 1, Feishu Dev.A/onReady, and all four pre-existing isales services still active. Startup logs prove runtime registry ready before WebSocket listen. -->
- [x] 3.4 Inspect the local unpackaged Edge runtime; restart it only if present and safe, then verify a clean welcome/sync path without automatically resetting Cloud or platform data.
  <!-- No unpackaged Edge runtime was present. A packaged /Applications/AIDCP.app process was running, so it was not restarted because it cannot consume source-only changes. Its child re-established an ESTABLISHED TCP connection to DEV :8787 after Cloud restart; Cloud logged no handler_error/rejection. No test reset or platform write was triggered. -->
