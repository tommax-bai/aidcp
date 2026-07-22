## Context

The packaged Edge runtime currently starts compiled JavaScript with Electron's Node mode, obtains an AdsPower/self-provider DevTools endpoint, discovers a page target, and keeps all downstream CDP/page behavior in the JavaScript process. The spike must prove a narrower boundary: the existing provider still owns browser lifecycle, while an independent Rust process receives only the endpoint and platform, selects the page, performs a bounded read-only probe, and returns content-free structured state.

The current executor remains production truth. This change does not alter Cloud protocol v2, customer authentication, operation classification, risk ownership, browser slots, platform writes, or the existing CDP recovery contract. A later production migration would require a separate OpenSpec change and an architecture-correct signed update path.

## Goals / Non-Goals

**Goals:**

- Prove that a standalone Rust executable can discover and attach to the existing dynamic AdsPower DevTools endpoint without owning browser startup.
- Keep target-selection rules, CDP messages, probe JavaScript, and page classification inside the native process.
- Return deterministic, content-free page state for an initial Xiaohongshu read-only vertical slice.
- Make protocol drift, timeout, no-target, CDP, and process-exit failures explicit and machine-readable.
- Provide focused Rust/TypeScript tests and a repeatable host-architecture release build/staging command.

**Non-Goals:**

- Replacing any production JavaScript page reader or action executor.
- Dispatching `Input.*`, navigation, DOM mutation, file upload, comment, like, follow, collect, or publish operations.
- Implementing stealth injection, long-lived production recovery, Cloud routing, authentication, auto-update, anti-debugging, or full binary obfuscation.
- Claiming that a locally built native artifact is distributable, signed, notarized, or resistant to professional dynamic analysis.
- Supporting Facebook, WeChat Channels, Windows, or macOS cross-architecture packaging in the first executable slice.

## Decisions

### D1. Use a standalone Rust sidecar, not a Node native addon

The spike adds `native/page-engine` as a Rust 2024 binary pinned to Rust 1.97.1. Electron/Node launches it as a child and communicates over stdin/stdout. A process boundary avoids Node ABI coupling, keeps the native artifact outside ASAR, permits independent crash handling, and matches the intended future signing/update boundary.

Alternatives considered:

- A `.node` addon would make calls convenient but couples loading to Electron's Node ABI and keeps page-engine failure inside the core process.
- A shared library (`.so`/`.dylib`/`.dll`) creates platform-specific loaders without improving the proof.
- Rewriting browser-provider startup in Rust expands scope before the page/CDP boundary is proven.

### D2. Keep IPC versioned, newline-delimited, and high-level

Protocol v1 uses one JSON object per line. The native process emits a `ready` record, accepts correlated requests, and returns exactly one response for every accepted request. The first method is `probe_page` with `{ host, port, platform, timeoutMs }`; it does not accept selectors, JavaScript, raw CDP methods, arbitrary WebSocket URLs, or credentials. Diagnostics go to stderr so stdout remains parseable.

Stable failure codes include `invalid_request`, `unsupported_protocol`, `endpoint_not_loopback`, `endpoint_unreachable`, `no_matching_target`, `cdp_connect_failed`, `cdp_timeout`, `cdp_error`, `probe_failed`, `engine_timeout`, `engine_exited`, and `invalid_protocol`. Human-readable detail is bounded and MUST NOT include DOM text, cookies, storage, headers, or evaluated source.

Only loopback hosts are accepted in the spike. This preserves the current local AdsPower/self-provider topology and prevents the development probe from becoming a generic remote debugging client.

### D3. Implement a minimal direct CDP client

The crate uses Tokio, `tokio-tungstenite`, Serde, and `serde_json`. It performs a small HTTP GET to `/json`, selects a `type=page` target whose URL is allowed by the Rust platform adapter, opens its `webSocketDebuggerUrl`, correlates request ids, and enforces an overall deadline.

Only `Runtime.enable` and one constant `Runtime.evaluate` probe are allowed. The probe reads browser-owned state and returns a value by copy; no generic `send(method)` surface is exposed to IPC. This intentionally does not import a generated full-CDP abstraction for the first slice.

### D4. Return semantic signals, not DOM or user content

The Xiaohongshu probe returns target id, canonical URL origin/path, document readiness, native page classification, and bounded counts/booleans such as whether feed-card, note-detail, login-wall, or dialog signals exist. It MUST NOT return outerHTML, visible text, account names, note content, cookies, storage, request data, or selector strings. The fixed probe source is build-encoded and restored only inside the native runtime so straightforward binary string scanning does not recover its selectors; this is a static-cost increase, not a claim that runtime memory cannot be dumped.

Page classification and its selectors live in a constant native probe module. The first classifications are `home`, `explore`, `search`, `note_detail`, `profile`, `login`, and `unknown`. Unknown evidence remains `unknown`; the engine does not manufacture a successful known state.

### D5. Keep the spike off the production startup path

The TypeScript side supplies a reusable `NativePageEngineClient` plus an explicit development CLI. Normal `src/main.ts` startup does not launch the native process, and no production browse/publish handler calls it. The CLI requires an explicit binary path and endpoint. This makes accidental customer activation impossible during the spike and preserves the existing JavaScript executor as the sole writer.

### D6. Stage a host-architecture artifact without claiming release readiness

A build script runs `cargo build --release --locked`, copies the resulting binary to a deterministic `build/native-page-engine/<platform>-<arch>/` directory, and records its SHA-256. The binary remains outside ASAR. Focused tests verify staging layout and that ordinary Electron builds do not require the spike artifact.

The spike does not add the binary to normal `extraResources` or trigger CI signing/notarization. Architecture-aware Electron inclusion, nested signing, packaged smoke, and component update are explicit gates for a later production change.

### D7. Test pure behavior before any live browser probe

Rust tests cover IPC parsing, loopback validation, target selection, CDP response correlation, page classification, timeout, and stable error mapping using deterministic fixtures/fake endpoints. TypeScript tests cover process readiness, correlation, malformed output, timeout/kill, and nonzero exit. A live probe is optional and read-only; its output must be manually compared with the visible browser page and recorded as probe evidence, not promoted to an automated production guarantee.

## Risks / Trade-offs

- [A second debugger connection affects the page or races the JavaScript executor] → The spike enables only Runtime and performs one read-only evaluation, runs only through an explicit CLI, and closes immediately after the response.
- [The probe script accidentally mutates page state] → Keep the script constant in Rust, expose no arbitrary evaluation input, test the CDP allowlist, and reject all unrecognized methods.
- [Page classification appears successful on unfamiliar DOM variants] → Return `unknown` unless positive structural evidence is present and include only bounded signal counts for diagnosis.
- [Sensitive page content leaks through IPC/logs] → Return booleans/counts and sanitized URL components only; prohibit DOM/text/cookie/network material in protocol types and test fixtures.
- [Rust/cross-platform build cost grows before feasibility is known] → Pin the toolchain/dependencies and validate only the host architecture in this change; defer the release matrix.
- [A native binary is mistaken for irreversible secrecy] → Report only that source-oriented unpacking is removed for migrated logic; dynamic CDP/IPC/memory observation remains possible.
- [Normal desktop packaging starts depending on an unavailable Rust toolchain] → Keep the native build as an explicit script and do not add it to the default Electron build in the spike.

## Migration Plan

1. Add the native crate, protocol types, deterministic tests, and host build/staging script.
2. Add the TypeScript child-process client and explicit read-only probe CLI with focused tests.
3. Run Rust tests, focused TypeScript tests, typecheck, OpenSpec strict validation, and artifact leakage/layout checks.
4. If an authorized local AdsPower profile is available, run one read-only live probe and compare its page classification with the visible page. Do not execute any interaction.
5. Keep the normal desktop package and production runtime unchanged. Removing the spike files or leaving the CLI unused is the rollback.
6. After evidence review, create a separate change for a production shadow reader, architecture-aware signed packaging, update delivery, and one-platform cutover; do not extend this spike in place.

## Open Questions

- Which exact sanitized page signals provide enough parity evidence across current Xiaohongshu page variants without leaking user content?
- Can CI sign/notarize the nested Rust executable automatically with the current electron-builder flow, or will the release script need an explicit inner-sign step?
- Should a future production engine remain one binary with compiled platform adapters, or load separately signed native platform components for faster updates?
