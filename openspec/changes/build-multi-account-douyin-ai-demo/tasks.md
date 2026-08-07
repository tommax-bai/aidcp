## 1. Standalone repository and runtime foundation

- [x] 1.1 Initialize `/Users/baitianxing/codes/douyin-ai-demo` with `main`, an isolated `codex/build-multi-account-douyin-ai-demo` worktree, and no AIDCP runtime dependency.
- [x] 1.2 Add Node.js 24, strict TypeScript, Fastify, SQLite, Playwright, lint, test, build, Docker, environment, and MIT license metadata.
- [x] 1.3 Define platform-neutral account, source, inbound, exact-target, generation, delivery, and UI projection types.
- [x] 1.4 Add validated configuration with offline fixture defaults, explicit real mode, explicit real-write gate, operator token, and redacted startup summary.

## 2. Durable state and security

- [x] 2.1 Create the SQLite WAL schema for accounts, independent source state, encrypted credentials/login/cursors/content, inbound deduplication, and durable reply jobs.
- [x] 2.2 Add AES-256-GCM envelopes with record-bound AAD and HMAC identity/event indexes so credentials and customer content are not stored in plaintext.
- [x] 2.3 Implement atomic baseline page ingestion, cursor advancement, one-reply-per-item admission, and account/session generation ownership.
- [x] 2.4 Implement restart recovery so pre-dispatch generation can be reclaimed while any possibly dispatched send becomes terminal `submitted_unknown`.
- [x] 2.5 Implement logout and pending-account cleanup without erasing sanitized terminal timeline evidence.

## 3. Offline fixture and chat-llm boundary

- [x] 3.1 Implement a deterministic fixture authorization, direct-message stream, comment reader, exact-target sender, and operator-triggered inbound injection without Douyin network access.
- [x] 3.2 Implement fixture, unavailable, and OpenAI-compatible `chat-llm` adapters that receive only sanitized normalized content.
- [x] 3.3 Add tests proving fixture mode performs no external platform action and model failures cannot dispatch a reply.

## 4. Experimental Douyin adapters

- [x] 4.1 Implement a bounded headed-Chromium authorization adapter that closes on success, expiry, cancellation, mismatch, or failure and never claims pure-HTTP QR production readiness.
- [x] 4.2 Implement the account-level direct-message WebSocket port with acknowledged readiness, exact event parsing, durable deduplication, bounded reconnect state, and no persistent Chromium dependency.
- [x] 4.3 Implement fail-closed incremental comment reads with stable event/video/comment identities and schema-drift reporting.
- [x] 4.4 Implement exact-target direct-message delivery behind the explicit real-write gate with typed accepted/rejected/unknown outcomes.
- [x] 4.5 Implement official comment reply admission from documented permission, token, ownership, request, and response fields without fallback.
- [x] 4.6 Implement the bounded per-account Chromium comment worker interface so one eligible write owns one headed browser lifecycle and exact-target postcondition.
- [x] 4.7 Expose `official_api`, `chromium_worker`, and `unavailable` capability honestly; unverified protocol paths must fail closed rather than simulate success.

## 5. Application runtime and web interface

- [x] 5.1 Implement authentication, baseline, direct-message stream, comment poll, generation, delivery, reconnect, and cleanup coordination with one runtime and platform-I/O lock per account.
- [x] 5.2 Implement operator-token-protected health/readiness, account, login, automation, logout, fixture injection, snapshot, and event-stream routes with origin and cache controls.
- [x] 5.3 Build the static responsive operations UI for account selection, QR state, source health, platform mode, real-write state, comment capability, timeline, and stop/resume/logout actions.
- [x] 5.4 Project `confirmed`, `rejected`, `failed_not_submitted`, `submitted_unknown`, and `blocked` distinctly; expose no retry control for unknown writes.
- [x] 5.5 Add monotonic snapshot revisions and authenticated SSE with bounded authoritative polling fallback.

## 6. Tests, documentation, and delivery evidence

- [x] 6.1 Add repository, crypto, fixture, model, coordinator, API authorization, baseline/deduplication, stop-generation, exact-target, recovery, source-isolation, and UI-copy tests.
- [x] 6.2 Add README, architecture, license provenance, configuration, local/Docker operation, and explicit private-protocol/official-permission limits.
- [x] 6.3 Add a live-validation checklist that separates source checks from named-account read-only probes and separately authorized one-target write/readback acceptance.
- [x] 6.4 Add isolated systemd and reverse-proxy examples without assigning a production hostname or touching AIDCP/isales services.
- [x] 6.5 Run `npm run check`, high-severity dependency audit, Docker build when available, and `openspec validate build-multi-account-douyin-ai-demo --strict`.
- [x] 6.6 Commit the standalone repository, fast-forward it to local `main`, and record the repository SHA and validation evidence here; do not create a remote or deploy without an explicit owner, visibility, hostname, and target.
- [x] 6.7 After explicit DEV authorization, deploy only the offline Fixture as an isolated service at an HTTPS subpath, verify authentication, Origin enforcement, SSE, restart persistence, and existing-service isolation, and record rollback evidence.

## 7. Requested real private-message, comment, and Doubao follow-up

- [x] 7.1 Align the real login lifecycle with the WeChat Channels demo boundary: render an exact Douyin QR in the operator UI, run Chrome only for bounded headless authorization/context capture on DEV, verify a stable identity/read probe, encrypt the retained session, and confirm browser/profile cleanup.
- [x] 7.2 Implement an independently authored current Douyin DM protocol adapter for history baseline, authenticated schema proof, account-level WebSocket ownership, any observed heartbeat/ACK behavior, schema-checked normalization, reconnect, and exact conversation targets without copying unlicensed protocol source or inventing an ACK command.
- [x] 7.3 Implement exact-conversation DM delivery with a durable client identity and typed accepted/rejected/failed-not-submitted/submitted-unknown outcomes; keep real writes behind both startup and account gates.
- [x] 7.4 Add explicit Volcengine Ark/Doubao configuration and response validation, reuse only server-side credentials, and expose a non-secret provider/model label in readiness and the UI.
- [x] 7.5 Make runtime readiness and UI controls capability-driven, enable real QR only when its components are wired, and expose independent private-message and comment read/reply state without fake success.
- [x] 7.6 Add sanitized golden protocol tests plus an end-to-end fake composition test covering QR authentication, DM baseline/schema proof, comment baseline, deduplication, Doubao generation, exact DM and comment receipts, and no retry after an unknown result.
- [x] 7.7 Run full source validation, integrate the clean standalone repository to `main`, back up the current DEV Fixture, and deploy the experimental real-capability service with `REAL_WRITES_ENABLED=true`, no pre-authorized account, and account-level automation off by default.
- [ ] 7.8 With an operator-named Douyin test account, complete QR and read-only identity, DM history/stream, comment history, and restart acceptance; only then accept one operator-named test conversation and one exact test comment for single write/readback checks before enabling broader automation.

## Validation evidence

- Standalone source: `/Users/baitianxing/codes/douyin-ai-demo.wt/build-multi-account-douyin-ai-demo` on `codex/build-multi-account-douyin-ai-demo`; commit `e37e4db5a466ff430cb0c4605f4b61d10099f871` was fast-forwarded to the independent repository's local `main`. No standalone remote was created. DEV now runs that same commit; the previous Fixture release `edc87ec4cd0b3d3fbd00f7257231b670a49e898d` remains available for rollback.
- `npm run check`: passed on 2026-08-07 with 10 test files and 87 tests, followed by a successful TypeScript build.
- `npm audit --omit=dev --audit-level=high`: passed with 0 vulnerabilities.
- Fixture HTTP smoke: `health=200`, `ready=200`, unauthorized snapshot `401`, stale mutation `409`, simulated login and two-source baseline healthy, one held/resumed DM and one comment reached Fixture `confirmed` exactly once.
- Docker image build: not run because the current host has no `docker` executable; Compose, Dockerfile, paths, and permissions were source-reviewed without claiming runtime proof.
- DEV Fixture deployment: `https://dev.yytt.com.cn/douyin/`, `douyin-ai-demo.service`, Node.js `v24.19.0`, loopback `127.0.0.1:4320`, release `/opt/douyin-ai-demo/releases/edc87ec`, and backup `/opt/douyin-ai-demo/backups/20260807-151956-before-public`.
- Deployment checks: public shell/assets/health/readiness `200`; unauthenticated API `401`; wrong Origin mutation `403`; authenticated Fixture account reached `active`; comment and DM baselines were healthy; one DM reached Fixture `confirmed`; authenticated SSE published a snapshot; state and timeline survived a service restart; service and Nginx remained active with zero unexpected restarts or warning/error logs.
- Browser validation: deployed static resources resolved under `/douyin/`, the operator gate and Fixture copy rendered without horizontal overflow, and browser warning/error logs were empty. The existing video demo root, AIDCP services, isales services, and their routes were not restarted or replaced.
- `openspec validate build-multi-account-douyin-ai-demo --strict`: passed. No real Douyin account, standalone remote repository, or platform write was used.
- Real-capability source validation on 2026-08-07: `npm run check` passed with 14 test files and 153 tests, including clean-room DM codec/transport, Chromium comment runtime cleanup quarantine, Doubao validation, and the dual-source composition test; `npm audit --omit=dev --audit-level=high` reported 0 vulnerabilities.
- A no-account probe captured the exact current Creator login QR element with headless system Chrome and confirmed temporary browser/Profile cleanup. This proves the QR entry and cleanup boundary only; task 7.8 remains the named-account runtime and write/readback acceptance gate.
- DEV real-capability preflight on Node.js `v24.19.0` and Chrome `147.0.7727.55`: server `npm ci` and build passed; the npm mirror lacked an audit endpoint, so the same lockfile was audited against the official npm registry with 0 vulnerabilities; `better-sqlite3` loaded; a server-side Doubao Ark generation probe returned a valid completed response; and the service user captured the current official QR and confirmed browser/Profile cleanup without a real account.
- DEV deployment: release `/opt/douyin-ai-demo/releases/e37e4db`, valid online SQLite/environment/unit backup `/opt/douyin-ai-demo/backups/20260807-173417-before-e37e4db-real`, `REAL_WRITES_ENABLED=true`, `private_web`, `chromium_worker`, and `doubao_ark`. The system `sqlite3` CLI could not parse the existing STRICT schema, so the successful online backup used the release's `better-sqlite3`; the earlier partial directory is labeled `20260807-173312-before-e37e4db-real-incomplete-sqlite-cli` and is explicitly not a rollback source.
- Post-cutover checks: public shell, assets, root route, health, and readiness returned `200`; unauthenticated snapshot returned `401`; authenticated snapshot, wrong-Origin `403`, and SSE passed; the real-mode account list was empty; the service was active/enabled on loopback `4320` with zero restarts, warning logs, or residual Chrome processes. `aidcp-api`, `aidcp-automation`, `aidcp-content`, `isales-api`, and `wechat-channels-ai-demo` remained active and were not restarted.
