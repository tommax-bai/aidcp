## Context

The requested deliverable is a new standalone repository, `douyin-ai-demo`, that demonstrates the same operator-visible product loop as the existing WeChat Channels demo: authorize multiple accounts, receive direct messages and comments, generate replies through `chat-llm`, deliver replies when the configured platform capability permits it, and expose the result honestly in a small web UI.

The available evidence does not justify treating any community repository as a production dependency. Several repositories demonstrate Douyin web SSO, account-level IM WebSockets, comment reads, and comment writes, but some have no clear license and all private-web contracts can drift. In particular, the current evidence does **not** prove that pure-HTTP QR authorization is reliable enough for this demo. Authentication will therefore use a short-lived **headed Chromium** session. After successful authorization and a read-only identity probe, encrypted session material is retained and Chromium is closed. A browser is not kept alive for normal direct-message receive/send or comment reads.

Official comment reply and direct-message APIs have account, application, and permission restrictions that cannot be assumed for an independent demo. Comment delivery must expose the capability actually configured for each account instead of silently changing mechanisms. Source validation in this change is fixture-based and local; deployment and real-account acceptance are separate, explicitly authorized activities.

The repository is independent from AIDCP Edge, Cloud, Console, databases, and deployment units. It may reuse product concepts, but it does not import their runtime packages or write to their state.

## Goals / Non-Goals

**Goals:**

- Provide a standalone TypeScript service and operations UI for multiple Douyin identities under one operator.
- Use short-lived headed Chromium for QR authorization and reauthorization, then retain the minimum encrypted web session required for API/WS operation.
- Maintain one account-level direct-message WebSocket runtime per active identity and an independent incremental comment reader.
- Normalize and durably deduplicate inbound direct messages and comments, establishing a historical baseline before automatic replies are eligible.
- Generate replies behind an OpenAI-compatible `chat-llm` adapter that has no access to platform credentials or transport implementations.
- Route exact-target comment replies through exactly one configured mode: `official_api`, `chromium_worker`, or `unavailable`.
- Treat only an explicit, target-matching platform receipt or verified postcondition as `confirmed`; preserve ambiguous post-dispatch results as terminal `submitted_unknown` without automatic retry.
- Make the deterministic fixture adapter the default and guarantee that the default configuration performs no real login, read, or write.
- Protect all operator APIs and sensitive projections with an operator token and store retained platform state encrypted in SQLite.

**Non-Goals:**

- Claiming that browserless QR authorization has been proven, or implementing pure-HTTP QR login as the default path.
- Treating undocumented Douyin web protocols as stable or official APIs.
- Copying source from repositories without a compatible license.
- Keeping Chromium running continuously for direct-message or comment reads.
- Falling back automatically from an official API to Chromium, or retrying an ambiguous write through another transport.
- Supporting media replies, proactive outbound marketing, bulk actions, historical-message auto-replies, or accounts other than those explicitly authorized by the operator.
- Sharing runtime state or credentials with AIDCP services.
- Deploying `private_web`, using a real Douyin account, or asserting real-platform acceptance as part of this change. A separately authorized DEV deployment MAY expose only the offline Fixture with its platform boundary visible.

## Decisions

### 1. Build one standalone service with explicit ports

The new repository will use Node.js 24, TypeScript, Fastify, SQLite, a WebSocket client, Playwright, and a small static operations UI. The process is split internally into the following ports:

- `AuthAdapter`: authorize, capture identity-bound session material, validate, reauthorize, and logout;
- `InboundAdapter`: maintain the direct-message stream and read comment increments;
- `ReplyAdapter`: deliver an exact-target direct message or comment reply and return a typed receipt;
- `ChatLlmAdapter`: generate reply text from normalized, non-secret input;
- repositories and coordinators for account state, inbound deduplication, work ownership, and delivery outcomes.

`fixture` and experimental real-platform implementations satisfy the same ports. Transport payloads remain inside adapters and cannot leak into the domain model or UI. This structure allows deterministic source validation while containing private-protocol drift.

Alternative considered: fork or embed CreatorHub or another community project. This is rejected because license status and implementation boundaries vary, and importing one would couple the demo to unverified private contracts. Compatible MIT-licensed projects may inform behavior, but implementation must be original and provenance documented.

### 2. Require an operator token at every management boundary

The service accepts a single opaque operator token through process configuration. It is never stored in SQLite or emitted to logs. Every account, QR, automation, timeline, and mutation endpoint requires `Authorization: Bearer <token>` and compares the supplied value in constant time. Browser UI code keeps the token in memory for the active page only; it is not placed in URLs or persisted to local storage. WebSocket or event-stream upgrades must authenticate before subscription and are scoped to the same operator.

The UI cannot display raw cookies, tokens, QR payloads, signing inputs, or full protocol evidence. Operational errors are mapped to bounded error codes and redacted summaries.

Alternative considered: bind only to localhost without authentication. This is insufficient for Docker or a remotely proxied demo and makes an accidental bind-address change dangerous.

### 3. Use short-lived headed Chromium for QR authorization

Creating or reauthorizing an account starts one visible Chromium worker for that pending account. The worker navigates to the Douyin login surface, presents the platform QR page, observes the platform-owned scan/confirmation flow, and captures only the session material required by the selected adapter. Authorization is complete only after the adapter resolves a stable Douyin identity and passes a read-only identity/session probe. The transaction then:

1. binds the platform identity to one local account record;
2. encrypts and persists the retained session;
3. starts the account runtime; and
4. closes the authorization browser and its temporary profile.

Only one authorization or reauthorization worker may own an account at a time. If the resolved identity is already bound, the new pending record is rejected rather than creating two runtimes. Platform `auth_required` transitions the account to visible reauthorization-required state, closes source runtimes, and blocks new sends. A timeout or ambiguous send is not interpreted as logout.

Pure-HTTP SSO QR login remains a possible isolated research task, not an implementation assumption. The community evidence is useful for identifying protocol shape but does not prove reliable production authorization, request-context capture, identity binding, or risk behavior.

Alternative considered: pure-HTTP QR authorization with no Chromium at all. It is rejected for this change because it lacks direct evidence and would turn an undocumented authentication contract into a critical dependency.

### 4. Encrypt account session state inside SQLite

SQLite is the sole durable store for accounts, encrypted sessions, source cursors, inbound items, generation ownership, and delivery attempts. It runs with foreign keys enabled and WAL mode. A schema migration table versions all changes.

Platform session material is serialized separately from ordinary account metadata and encrypted using AES-256-GCM with a random nonce per write. The master key is supplied outside the database through process configuration. Authenticated additional data includes the local account ID, platform identity, adapter kind, and encryption schema version so ciphertext cannot be moved between records unnoticed. Plaintext exists only for the bounded adapter call and is never logged. Startup fails closed when encrypted real-account rows exist but the key is absent or invalid; fixture rows require no platform secret.

Logout first stops the account runtimes, then deletes encrypted session material and marks the account logged out while retaining non-secret audit history. Database backups remain sensitive because ciphertext and operational metadata are present; key rotation is implemented as an explicit decrypt-and-re-encrypt transaction, not dual-key fallback.

Alternative considered: Playwright persistent-profile directories as the source of truth. They are harder to encrypt, back up, migrate, and bind to an identity, and tend to retain more browser data than required.

### 5. Give each active account one direct-message WebSocket owner

An active real account owns exactly one direct-message WebSocket runtime. It creates the handshake from that account's retained session, validates message schemas before normalization, emits source-health state, and reconnects only under the bounded transport policy for that same account. It never shares cookies, cursors, or connections between identities.

On first activation, the runtime records a direct-message baseline before marking later text messages eligible for automation. Stable platform conversation/message identity is required for ingestion. The durable uniqueness key is `(account_id, source, platform_event_id)`; duplicate frames and reconnect replay update source observations but do not create new reply work. Unrecognized schemas stop the source visibly instead of guessing fields.

Direct-message sends use the account's web IM reply adapter and exact conversation/message target. Delivery does not require a continuously running browser. Only a target-matching platform acknowledgement is `confirmed`; connection loss or an unreadable response after dispatch becomes `submitted_unknown`.

Alternative considered: poll direct messages. Polling is retained only as a possible bounded recovery/read probe if direct evidence later requires it; it is not the primary source because the demonstrated platform mechanism is an account-level IM WebSocket.

### 6. Read comments incrementally without a persistent browser

The account runtime periodically reads comments through the selected experimental web read adapter, using the encrypted session and a validated request context. It first stores a high-water baseline for existing comments. Only observations beyond that baseline can become automatic-reply candidates. Pagination is bounded, and every response must pass adapter-specific schema and identity checks before the cursor advances.

Comments are deduplicated by stable comment identity and retain the exact video/comment/account target needed for a reply. Cursor changes and item inserts commit in one SQLite transaction so a crash cannot advance past an unstored item. `auth_required`, schema drift, rate limiting, and transport health are distinct source states; none are projected as an empty successful poll.

Alternative considered: scrape comments continuously in Chromium. It increases resource cost and couples reads to page layout when the current evidence supports a session-based web read path. Chromium remains available only for the configured write capability.

### 7. Select one explicit comment-write capability per account

Each account projects one of these modes and its current readiness:

- `official_api`: enabled only when operator-provided application credentials, required permission, authorized account identity, and own-video target constraints validate. The official adapter sends once and confirms only the documented target-matching receipt.
- `chromium_worker`: starts one account-scoped **headed** Chromium worker only for an eligible exact comment reply. The worker loads the retained identity, resolves a fresh target, dispatches through native user-like input, and verifies a platform response or fresh postcondition before closing. An account mutex prevents concurrent browser writes.
- `unavailable`: reads and AI drafts may continue, but comment delivery is blocked with an explicit reason.

Mode selection is configuration, not a fallback order. Failure or ambiguity in `official_api` never launches Chromium, and failure or ambiguity in Chromium never changes to another mechanism. This prevents duplicate comments and keeps capability claims honest.

Alternative considered: always use Chromium because it covers more accounts. It is rejected because official capability, when actually granted, has a clearer contract, while some installations deliberately require comment writes to remain unavailable.

### 8. Make delivery outcomes terminal and honest

Every delivery attempt has a unique local attempt ID and one immutable target. The coordinator acquires ownership before dispatch and records `dispatch_started_at` transactionally. Terminal outcomes are:

- `confirmed`: explicit target-matching receipt or verified fresh postcondition;
- `rejected`: explicit platform refusal before or after dispatch;
- `failed_not_submitted`: transport or validation failure proven to occur before dispatch;
- `submitted_unknown`: dispatch may have occurred, but confirmation cannot be established;
- `blocked`: capability, authorization, policy, or operator state prevents dispatch.

`submitted_unknown` is terminal but unconfirmed. It releases the worker lease, suppresses automatic redrive for that inbound item, is not counted as success, and requires an operator to inspect the platform before any separately authorized follow-up. Process restart resumes only work proven not to have crossed the dispatch boundary.

Alternative considered: retry timeouts automatically. It is rejected because retries can duplicate irreversible direct-message or comment writes.

### 9. Isolate `chat-llm` from platform credentials and delivery

The `ChatLlmAdapter` is OpenAI-compatible and receives a normalized request containing source kind, sanitized inbound text, bounded conversation context, reply policy, and generation ID. It never receives platform cookies, access tokens, signing inputs, or transport clients, and it cannot send a reply itself. Model configuration is supplied separately from Douyin adapter configuration.

Automation claims one eligible new text item with a lease and generation revision. After generation, the coordinator rechecks account activity, source eligibility, target identity, generation ownership, and delivery capability before creating a delivery attempt. Stop prevents new claims; an in-progress generation may be stored as a draft but cannot bypass the final ownership check. Non-text, historical-baseline, duplicate, already-terminal, and operator-suppressed items are not auto-replied.

Alternative considered: call `chat-llm` directly from protocol callbacks. That makes reconnection/replay capable of triggering duplicate generations and couples model latency to source health.

### 10. Default to a deterministic fixture with no real platform writes

`fixture` is the default adapter and the only mode used by the standard test and demonstration commands. It provides deterministic QR states, account identities, direct-message frames, comment pages, model responses, and each delivery receipt class. It performs no network request to Douyin and launches no browser.

Selecting an experimental real adapter is an explicit startup choice. Real writes additionally remain disabled unless the operator starts the service with the documented real-write enablement and configures the applicable account reply capability. The startup summary and UI must show `fixture`, `real read-only`, or `real writes enabled`; the state cannot be inferred from a successful health check. Tests assert that default configuration cannot construct a real reply adapter.

Alternative considered: make the real adapter default when credentials exist. This risks an imported environment variable turning a source-validation run into a platform action.

### 11. Deploy a separately authorized Fixture without sharing AIDCP runtime

The follow-up DEV deployment uses an independent system user, release directory, Node.js 24 runtime, environment file, SQLite database, loopback port, systemd unit, and exact Nginx path prefix. It reuses only the existing DEV TLS hostname and MUST NOT replace the host root route, expose the application port publicly, import AIDCP state, or enable a real Douyin adapter. The public page and readiness response continue to identify Fixture mode and `REAL_WRITES_ENABLED=false`.

The deployment release and sensitive configuration are backed up before the Nginx change. A failed service, route, readiness, origin, SSE, persistence, or existing-service check requires restoring the prior Nginx file and stopping the new unit; it does not justify touching the video demo, AIDCP, or isales services.

### 12. Project state through a compact operations UI

The UI exposes account identity, authorization/reauthorization state, direct-message WS health, comment-read health and cursor time, configured comment capability, automation stop/run state, inbound timeline, generated draft, and terminal delivery outcome. It uses domain projections rather than raw adapter responses. `submitted_unknown`, `auth_required`, schema drift, and `unavailable` remain distinct visible states.

Mutations require exact account and inbound-item identifiers plus the current revision. Stale UI actions receive a conflict instead of applying to a changed target. No UI status such as “handed to worker,” Chromium launched, WebSocket connected, or generation completed is displayed as delivery success.

## Risks / Trade-offs

- [Undocumented web protocols drift or trigger platform risk controls] → Keep them behind schema-checked experimental adapters, stop the affected source visibly, retain headed Chromium only for bounded authorization/comment writes, and document that source validation is not real-platform acceptance.
- [A retained session is stolen from SQLite or logs] → Encrypt session rows with externally supplied key material and record-bound AAD, redact protocol evidence, require the operator token, and minimize captured browser state.
- [Multiple accounts become cross-wired] → Bind encrypted sessions, WebSockets, cursors, targets, and worker locks to a resolved platform identity; reject duplicate identity bindings.
- [Reconnect or process restart causes duplicate replies] → Use durable platform-event uniqueness, transactional claims, a recorded dispatch boundary, and terminal `submitted_unknown` suppression.
- [Comment capability is overstated] → Expose `official_api`, `chromium_worker`, and `unavailable` explicitly; do not auto-fallback or treat a Chromium launch as success.
- [Official permissions are unavailable for the test account] → Keep `unavailable` a first-class mode and allow fixture/read-only demonstrations without pretending a write path exists.
- [Headed Chromium is inconvenient in server containers] → Treat authorization and Chromium comment writes as local/operator-attended capabilities; do not claim the initial source build is a headless server deployment.
- [LLM latency or unsafe content blocks source processing] → Persist normalized input before generation, separate source ingestion from generation workers, bound prompt/context size, and require a final ownership check before delivery.
- [Encryption key loss makes retained sessions unrecoverable] → Fail closed and require reauthorization; do not add a plaintext or silent fallback.
- [Fixture confidence is confused with production confidence] → Label adapter mode everywhere and maintain a separate, opt-in real-account acceptance checklist.

## Migration Plan

This is a greenfield repository, so there is no existing production state to migrate.

1. Create `/Users/baitianxing/codes/douyin-ai-demo` as an independent Git repository with its own OpenSpec, dependency lockfile, license/provenance record, and fixture-only skeleton.
2. Implement SQLite migrations, encrypted-session storage, operator authentication, domain state machines, and fixture adapters first.
3. Implement the operations UI and verify the multi-account baseline, deduplication, stop/resume, generation ownership, and all delivery outcomes entirely against fixtures.
4. Add `chat-llm` through its adapter and test it with a local deterministic fake before any external model call.
5. Add experimental Douyin authentication, direct-message WS, comment read, direct-message send, official comment, and bounded Chromium comment adapters behind explicit configuration. No unlicensed source is copied.
6. Run focused tests, full tests, typecheck, build, dependency/license checks, and strict OpenSpec validation. These gates prove source consistency only.
7. Stop after producing the local repository and documented acceptance runbook. A later deployment requires separate authorization naming the environment and public boundary; real QR login or platform writes additionally require a named account and allowed actions.

Rollback during development is deletion or disabling of the newly added adapter behind its port while retaining fixture mode and compatible schema migrations. Once real-account testing is separately authorized, rollback must first stop account runtimes and Chromium workers; ambiguous attempts remain `submitted_unknown` and are never replayed as part of rollback.

## Open Questions

- Which official Douyin application, account type, and permissions, if any, will be available for a later `official_api` acceptance run? This does not block fixture implementation; absent proof, the mode remains `unavailable`.
- Which exact private-web request fields and WebSocket schema are currently required by Douyin? They must be captured through an authorized read-only compatibility probe before the real adapter is declared ready and must not be derived by copying unlicensed code.
- Fixture deployment target is resolved as DEV under `https://dev.yytt.com.cn/douyin/`; it has no attended-browser capability. Any future real-mode deployment still requires a separately reviewed desktop/browser arrangement.
- Which real account and bounded DM/comment targets may be used for acceptance? No account or real write is authorized by this proposal.
