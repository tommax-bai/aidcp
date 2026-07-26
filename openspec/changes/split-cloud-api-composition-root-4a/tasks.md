## 1. Admission and final census

- [ ] 1.1 Run `scripts/task-preflight`; create isolated control, Cloud, kernel, transport, API, automation, and content worktrees/branches for this change, preserving canonical defaults and unrelated files.
- [ ] 1.2 Re-run the design D1 census against the implementation base SHA and `boundaries/module-ownership.json`; prove the final 19-group/45-slot surface in all three directions, remove methods whose consumers moved to API, and keep `claimExecutionTarget`, chat resolve/bind, 4b mirrors, 3b approval, and unlisted content methods out.
- [ ] 1.3 Capture baseline Cloud focused/acceptance/full/typecheck/boundary results and API/automation/content hand-written-root failures separately; record package pins, source-sync and DEV monolith topology without claiming independent boot.

## 2. Kernel contracts and wire discipline

- [ ] 2.1 Add pure kernel contracts for AccountRoster, AccountOwnership and AccountRuntime authority, preserving ownership three-state results and replacing synchronous nickname get-then-set with owner-side idempotent `recordNickname`; do not expose unused `claimExecutionTarget`.
- [ ] 2.2 Add the ten-method automation PublishLog port and two Edge publish command DTOs; retain content-version CAS and keep all 3b approval revision types/routes untouched.
- [ ] 2.3 Add pure InteractionAuth, InteractionApiWrites and ReplyConfig resolver contracts; remove caller `Queryable`/PG types from purge methods and preserve real row counts plus audit inserted/duplicate.
- [ ] 2.4 Add AccountPersona, EnvironmentHandshake, CommentApprovalPolicy, NotificationContacts, FirstPostProgress and AutomationConfigCommands contracts plus the three API-owned offboard ledger primitives `reconcileActiveOffboardSnapshot`, `claimPendingMaterializations`, and `recordMaterializationReceipt`.
- [ ] 2.5 Add one exhaustive structured notification `deliver` command/result union; keep `resolveCardChatId`, `resolveAccountChatId`, and `bindBotChat` API-local, and prove the kernel layer imports no Feishu SDK, SQL, HTTP, or owner implementation.
- [ ] 2.6 Define the 4a envelope, version/error unions, target validation inputs and read/write unknown-result distinctions; keep `AIDCP_API_INTERNAL_TOKEN`, `AIDCP_AUTOMATION_INTERNAL_TOKEN`, and `AIDCP_CONTENT_INTERNAL_TOKEN` separate from each other and from the existing 3b approval token.
- [ ] 2.7 Add the one-method `EdgeResumeCommandPort` request/receipt/error contract with stable commandId, real resumed count, same-process owner dedupe and explicit result-unknown semantics; bind it to the exact `AIDCP_AUTOMATION_INTERNAL_TOKEN`.
- [ ] 2.8 Add narrow `FacebookScopeCommandPort` contracts for `importTargets` and `replaceTargetScopes` with stable commandId, owner receipt/dedupe, target/version validation, and result-unknown semantics.
- [ ] 2.9 Reuse or narrow the pure `PersonaGeneratorPort.generate` contract for API→content calls, retaining idempotency key/diversity seed and a generation-result-unknown outcome without exposing generic LLM authority.

## 3. API owner adapters and internal server

- [ ] 3.1 Implement API-local AccountRoster/Ownership/Runtime adapters over the existing account owner store, with target checks, three-state ownership, idempotent nickname observation and no automation pool.
- [ ] 3.2 Implement the PublishLog and Edge publish command adapters over the API owner log/handlers; preserve all ten methods, content-version conflicts, legitimate nulls and write-after-ack-loss unknown results.
- [ ] 3.3 Implement InteractionAuth/ApiWrites/ReplyConfig adapters using only the API pool; make purge methods open owner transactions, keep audit `eventId` idempotency and return exact row/result truth.
- [ ] 3.4 Implement persona authority, environment registration, approval policy, notification contacts, first-post progress, asynchronous config command, and the three offboard ledger adapters; trigger persona auto-fill only after owner-side environment registration succeeds.
- [ ] 3.5 Implement the structured notification adapter using API-owned chat routing, account display truth, card builders and messenger; preserve approval-card failure, warn-and-continue notification and `delivery_result_unknown` distinctions.
- [ ] 3.6 Implement versioned route/client modules for every admitted group, all using bearer authentication and local-target verification before owner handlers; missing token/URL/target must not fall back to a local API store or pool.
- [ ] 3.7 Register 4a routes capability-by-capability on the API internal server so one optional owner capability cannot disable unrelated routes; add source guards proving no public panel/customer route exposes them.
- [ ] 3.8 Wire the API command face to call `accountState.resume` first and the remote Edge resume client second; return active+failed/unknown partial truth without rollback or optimistic resumed count.
- [ ] 3.9 Wire API panel Facebook mutations through the remote automation command client and `AccountPersona.generate` through the remote content generator client; never hold an API owner transaction across either call, auto-retry unknown writes/generation, or reuse the 3b token.

## 4. Automation clients and paired outbound owners

- [ ] 4.1 Wire AccountRoster/Ownership/Runtime clients into automation projection, risk ownership, connection runtime and account command consumers; remove direct `AccountStore`/API-pool construction while leaving 4b synchronous mirrors explicit.
- [ ] 4.2 Wire PublishLog and Edge publish command clients into dispatcher, usage snapshot, delegated executor and Edge WS handlers; continue using 3b approval authority/decision/trigger without duplicate routes or state.
- [ ] 4.3 Wire InteractionAuth/ApiWrites/ReplyConfig clients; preserve auth fail-closed, outbox cursor stop/replay, audit event idempotency and real purge counts without passing an automation PG client across HTTP.
- [ ] 4.4 Wire persona, environment, policy, notification-contact, first-post, and asynchronous config clients only at confirmed automation consumers; move offboard orchestration into automation so it reads local `activeWechatOffboards`, reconciles/claims via API, calls local `materializeEnvironmentOffboard`, and writes a CAS receipt without holding a transaction across the network.
- [ ] 4.5 Wire only the structured notification `deliver` client and remove automation imports/construction of Feishu SDK, API card builders, BotChatStore, and API messenger; add an exhaustive kind guard and no chat resolve/bind client.
- [ ] 4.6 Extend the automation-owned `FacebookGroupOpsPort` with `importTargets` and `replaceTargetScopes`, register both as versioned/target-bound routes protected by `AIDCP_AUTOMATION_INTERNAL_TOKEN`, and use one refresh-before-reject helper backed by AccountRoster before the owner write transaction.
- [ ] 4.7 Register the versioned/target-bound `AIDCP_AUTOMATION_INTERNAL_TOKEN` Edge resume route on the automation internal server and wire it only to the installed local `WsServer`; dedupe equivalent commandId receipts and never translate a missing server/timeout into resumed=0.
- [ ] 4.8 Add composition-root source tests proving independent automation has no API pool/store imports, Edge resume remains a command, and remaining unresolved read-only/synchronous dependencies are enumerated only as 4b blockers.
- [ ] 4.9 Register the versioned/target-bound `AIDCP_CONTENT_INTERNAL_TOKEN` persona generation route on the content internal server, backed only by the content-owned `PersonaGenerator`; keep persistence and account validation in API.

## 5. Fact-source verification

- [ ] 5.1 Add direct HTTP tests for all 19 D1 groups/45 slots in automation→API, API→automation, and API→content directions: success, legitimate empty/null, owner rejection, malformed response, wrong version, wrong target, wrong bearer, timeout/unavailable, and side-effect result unknown.
- [ ] 5.2 Add focused AccountRoster/projection/Facebook tests for nonempty refresh freshness, empty/error no-advance, import/replace parity, transaction ordering, no partial target/scope write, wrong bearer/target, duplicate/colliding commandId, and post-write ack loss.
- [ ] 5.3 Add publish/interaction/offboard tests for content-version CAS, 3b revision non-regression, audit replay dedupe, owner-local purge transactions, complete-snapshot gating, atomic admission claim, local materialization, CAS/idempotent receipt, `binding_missing`, ack loss, and no false terminal outcome or cross-network transaction.
- [ ] 5.4 Add notification tests for every structured kind, unknown kind rejection, no-chat business error, API-side card construction, warn-and-continue call sites and post-send response loss.
- [ ] 5.5 Add Edge resume route/client tests for version/target/Bearer, true resumed count, duplicate commandId receipt, collision rejection, no-server/timeout result unknown, no auto-retry, API account-state-first ordering and 3b restricted-recovery non-bypass.
- [ ] 5.6 Add PersonaGenerator route/client tests for valid generation, wrong bearer/target/version, content-owner invocation, no API-local generator/LLM construction, post-generation ack loss, same-process receipt reuse, no auto-regeneration, and API-only persist.
- [ ] 5.7 In `aidcp-cloud`, run focused suites, `npm run test:acceptance`, full `npm test`, `npm run typecheck`, boundary/ownership census and `git diff --check`; require zero new cross-owner reads/writes and no API pool in automation mode.

## 6. Shared packages and extracted repositories

- [ ] 6.1 Publish only pure D1 contracts to `aidcp-kernel`; run build/typecheck, export probes and focused tests, then integrate/push the exact default-branch SHA.
- [ ] 6.2 Add only admitted 4a route/client modules and the paired Facebook extension to `TRANSPORT_MEMBERS`; publish `aidcp-transport`, run build/typecheck/round-trip/export probes, and integrate/push the exact SHA.
- [ ] 6.3 Sync API owner adapters/server wiring plus automation/content clients into `aidcp-api`, update exact kernel/transport pins, run focused/strict-slice/full-where-available/typecheck gates and report remaining 4b hand-written-root failures honestly before integrating/pushing.
- [ ] 6.4 Sync automation-owned client/root wiring into `aidcp-automation` while retaining its local `src/transport` source and avoiding a second transport package instance; run focused/strict-slice/full-where-available/typecheck gates and report remaining 4b blockers before integrating/pushing.
- [ ] 6.5 Sync the content-owned PersonaGenerator route/server wiring into `aidcp-content`, update exact kernel/transport pins, run focused/full-where-available/typecheck and security gates, then integrate/push its exact SHA.
- [ ] 6.6 Run final `scripts/sync-split-repos` source/pin/migration census from the landed Cloud SHA; require zero managed drift and record expected hand-written-root differences without auto-overwriting them.

## 7. DEV monolith and closeout

- [ ] 7.1 Rebase/integrate/push Cloud only after all source/package gates pass; read deployment guidance, run `scripts/deploy-target dev --check`, back up and deploy the clean eligible default checkout, and restart only the documented DEV Cloud unit.
- [ ] 7.2 Verify DEV monolith deploy SHA, service/restart count, 8787/8090 health, PostgreSQL/owner schema gates, Feishu state, writer lock and logs; confirm independent api/automation/content listeners remain closed and do not call this three-process verification.
- [ ] 7.3 Update §10 with the final 19-group/45-slot post-3b inventory, delivered repo SHAs/tests/DEV evidence, Facebook and Edge command receipts, automation-owned offboard orchestration, deliver-only notification exit, local-only unused methods, content-owned persona generation, removed stale “11” count, and explicit remaining 4b/independent-runtime boundary.
- [ ] 7.4 Run `openspec validate split-cloud-api-composition-root-4a --strict` and `git diff --check`; update each completed task with repo SHA, validation/deployment/deviation evidence, integrate/push control `main`, and leave archive for a separately confirmed closeout.
