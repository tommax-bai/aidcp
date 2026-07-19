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
  <!-- Initial evidence was insufficient: an ESTABLISHED TCP socket did not prove valid welcome. At 17:19 the unpackaged Edge exposed `handler_error: no_persona` for video account k1eoujd8. This task is superseded by section 4 remediation and must not be cited as successful Video Channels welcome proof. -->

## 4. Business-gate-independent handshake remediation

- [x] 4.1 Audit every Cloud pre-welcome call for business gates, eager persona reads, replacement side effects, and non-fatal dependency failures; record which failures remain intentional handshake rejection.
  <!-- Confirmed accidental escalations: pre-welcome RoleDispatcher setup, eager CommentLikeAppraiser persona read, pre-welcome same-edge displacement, EventBus async rejection leakage, and uncaught hello-snapshot rejection. Intentional fail-closed admission remains limited to missing/retired accountId, missing edgeId, unsupported/mismatched platform, or unavailable identity/risk dependencies required to route safely. -->
- [x] 4.2 Move dispatcher activation and same-edge replacement to the post-welcome lifecycle, skip browse dispatcher construction for Video Channels, make dispatcher-dependent registry operations fail closed when no dispatcher is active, and contain post-welcome async business/snapshot rejections.
  <!-- Cloud: ConnectionRuntimeRegistry now admits transport first and commits replacement/business activation only from onEdgeRegistered after welcome. Video Channels remains transport-only; failed optional dispatcher activation, async EventBus handlers, and hello snapshot backfill are contained without closing the socket. -->
- [x] 4.3 Remove constructor-time persona evaluation from comment-like setup and cover comment-like-enabled XHS/FB no-persona plus Video Channels no-persona behavior.
  <!-- Cloud: CommentLikeAppraiser resolves persona-derived probability lazily at action time. Regression coverage proves AIDCP_COMMENT_LIKE=true cannot read a missing persona while constructing the dispatcher and covers transport-only Video Channels no-persona admission. -->

## 5. Remediation validation and delivery

- [x] 5.1 Run Cloud focused handshake/persona/reconnect tests, required acceptance/full safety suites, typecheck, and `openspec validate wechat-reset-handshake-closure --strict`.
  <!-- Rebased Cloud head 5ca6ab8: focused handshake/persona/reconnect/EventBus/startup suites 54/54, acceptance 59/59, full 2557 pass / 0 fail / 8 gated skips, typecheck passed. Strict OpenSpec validation passed before delivery and after evidence update. -->
- [x] 5.2 Rebase, commit, push, fast-forward Cloud/control defaults, deploy Cloud to `dev`, and verify service/listeners/health/PostgreSQL/Feishu/unrelated-service boundaries.
  <!-- Cloud master fast-forwarded and pushed at 5ca6ab8. DEV target preflight passed; backup cloud.20260719-175259.tgz plus env copy created; only aidcp-cloud.service restarted. Service is active with 8787/8090/8091/8088 listeners, panel health/version and console HTTP 200, PostgreSQL SELECT 1, Feishu Dev.A activate_status=2 plus WSClient onReady, and all four pre-existing isales services still active. -->
- [x] 5.3 Verify a real unpackaged Video Channels Edge receives a non-empty welcome without persona and remains connected; confirm no platform reset/write was triggered and record honest live evidence.
  <!-- Local unpackaged Edge env ads-k1eoujd8 (account k1eoujd8, no persona) received sessionId=sess-1 at 18:04:32. Cloud logged platform=wechat_channels transport-only. After bounded observation the child and TCP remained alive with no WS close/reconnect/no_persona/start failure. No reset or platform write was invoked; only startup auth/readiness probing ran, which separately remained fail-closed at INTERACTION_INTERNAL_ERROR. The previously running ads-k1e0awu5 environment was restored after UI verification and both connections were ESTABLISHED. -->
