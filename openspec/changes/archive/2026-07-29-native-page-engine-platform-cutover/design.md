## Context

The current Native Page Engine is a required long-lived Rust child process for Xiaohongshu only. It owns target selection and CDP after Edge opens a typed session, accepts high-level commands over bounded JSONL IPC, embeds its browser scripts in the native binary, and returns typed results with an explicit effect phase. Facebook still bypasses that boundary: `FacebookBrowseSession`, its executors/readers, and seven exported probe modules contain about 8,400 lines of production-reachable page/CDP logic under `dist`. The production importer follows `export *`, so calibration probes are retained even when no runtime caller uses them.

WeChat Channels is materially different. Its normal operations call authenticated platform APIs and its capability probe tests those APIs; those are not page-understanding rules. The local login sidecar does, however, attach to Chrome, capture a narrowly whitelisted authentication request, read cookies, and evaluate the user agent. That browser-session acquisition boundary is valuable client-side logic and belongs behind Native.

The attacker model is a customer with full control of the installed desktop machine. Native code cannot make the system impossible to reverse engineer: browser DOM, CDP traffic, process inputs/outputs, and final actions remain observable. The target is to remove an `asar`-unpack-and-read path and raise recovery cost to native analysis plus dynamic observation, while keeping runtime truth and maintainability.

## Goals / Non-Goals

**Goals:**

- Make Native the only production owner of Facebook page interpretation, selectors, browser scripts, CDP reads/writes, bounded local recovery, and post-action verification.
- Put production Facebook probes behind the same typed Native command boundary; keep calibration-only probes out of the production graph entirely.
- Put WeChat browser-session acquisition behind Native without moving API business orchestration into Rust.
- Preserve existing Facebook and WeChat product contracts and Cloud protocol without a shadow path or JavaScript fallback.
- Make production-dist and final-package leakage checks fail closed on migrated rule modules, representative markers, development probes, source maps, or incompatible Native artifacts.
- Keep commands/versioning/tests structured enough that future page-rule edits remain localized and reviewable.

**Non-Goals:**

- Prevent a determined local attacker from observing CDP traffic, DOM state, IPC, or executed behavior.
- Encrypt Native IPC as a substitute for client authentication or communication security.
- Move Cloud planning, pacing, risk state, account lifecycle, ordinary API clients, or UI rendering into Rust.
- Change existing Facebook/WeChat capability semantics, quotas, approvals, or user-visible behavior.
- Build or release a desktop installer as part of source implementation.

## Decisions

### 1. One engine process, platform adapters, one session platform

The existing executable remains the single Native Page Engine artifact. `session.open` accepts `xiaohongshu`, `facebook`, or `wechat_channels`, target selection validates the platform host allowlist, and one process session is bound to exactly one platform/task/target. Commands are dispatched to a platform adapter and rejected on a platform mismatch.

This avoids three independently supervised binaries and keeps signing, manifest verification, cancellation, duplicate-command handling, and crash semantics uniform. Separate internal Rust modules and embedded browser routers retain platform isolation.

Alternative considered: a separate Facebook executable. It provides physical code separation but duplicates the security-critical supervisor/protocol lifecycle and increases packaging/signing failure modes without materially changing the local-attacker boundary.

### 2. Typed semantic commands, never arbitrary browser instructions

Edge sends typed, versioned semantic commands whose parameters are business values such as a URL, post identity, text, media path, or requested interaction. It cannot send CSS/XPath selectors, JavaScript source, raw CDP method names, or unbounded output requests. Native maps each command to its platform implementation, owns all CDP dispatch, and bounds every returned string/list/object before IPC serialization.

Facebook commands are grouped by stable responsibilities:

- page/identity/consent/overlay probe and normalization;
- feed, Reels, inline post, and detail reads;
- viewport movement and dwell-supporting page state;
- like/follow/comment/group-join actions and exact post-action verification;
- composer/media/publish steps and submitted/ambiguous reconciliation.

Edge may retain long-running orchestration and Cloud callback translation, but it can only call selector-free Native facade methods. A facade that re-implements page classification or recovery in TypeScript violates the boundary.

Alternative considered: a generic `runtime.evaluate` Native proxy. It would move the socket while leaving recoverable JavaScript and selector inputs in the package, so it is explicitly forbidden.

### 3. Native embeds platform browser routers as encoded build inputs

Complex DOM work remains compact browser JavaScript executed by Native through CDP, because DOM APIs are the browser-native semantic surface. Source routers live only under `native/page-engine`, are transformed to byte arrays at Rust build time, and are absent from `dist`, ASAR, source maps, and final package resources as standalone text files. Rust decodes them in memory only for dispatch.

The goal is packaging-boundary protection, not cryptographic secrecy. The byte transform is deterministic and carries no claim that a local attacker cannot recover it.

Alternative considered: express all DOM traversal through CDP DOM-domain calls in Rust. This creates substantially more protocol traffic and maintenance burden, while a debugger can still recover the same selectors and decisions.

### 4. Probe classification is based on production reachability

Production-required probes become Native semantic commands because they perform page classification, editor/media/composer discovery, submit gating, or post-action verification. Calibration and diagnostic probes remain TypeScript scripts only when they are absent from `dist` and final packages. The Facebook production entry stops wildcard-exporting probe modules.

Build verification computes the production import graph and scans the final ASAR/resources. Both levels maintain an explicit denylist of migrated module paths and stable representative rule markers. Development probe filenames/payloads are denied from the final package regardless of reachability assumptions.

### 5. WeChat Native scope stops at browser-session acquisition

Native enables Network capture, reloads the allowed WeChat Channels target, accepts only the exact `channels.weixin.qq.com/.../auth/auth_data` request shape, reads only matching WeChat cookies and `navigator.userAgent`, and returns a bounded typed session candidate. Edge continues encryption-at-rest, identity checks, API requests, capability probes, circuit breaking, and lease ownership.

Native never returns arbitrary captured requests or browser storage. The existing sidecar teardown remains authoritative: a session is not released until browser/process close is confirmed.

### 6. Direct cutover with honest failures

There is no shadow execution and no runtime feature flag that revives migrated JavaScript. A missing/incompatible/crashed Native process produces an explicit unavailable or ambiguous result according to whether browser input may have been dispatched. Edge never retries an ambiguous write, and process restart creates a new session identity without replay.

Rollback is a previous installer/source revision, not an in-package downgrade path. Real-client acceptance is required before any later installer release but is not inferred from unit tests or a successful package build.

## Risks / Trade-offs

- [Large Facebook surface may regress long-tail layouts] → Port by responsibility with captured fixtures, fake-CDP tests, existing focused acceptance suites, and exact post-action assertions before deleting each JavaScript path.
- [Keeping orchestration in TypeScript can accidentally preserve page intelligence] → Define selector-free facade types, reject arbitrary browser inputs, add source/dist/package marker scans, and review every remaining production-reachable Facebook module.
- [Embedded browser JavaScript remains recoverable from a native binary or at runtime] → Treat this as deliberate cost-raising, keep claims honest, and avoid complexity presented as cryptographic protection.
- [One engine process increases platform adapter blast radius] → Bind every session to one platform, deny mismatched commands, keep platform modules independent, and run cross-platform protocol fixtures.
- [Native Network event capture can miss a request before attachment] → Enable Network before reload, use a bounded acquisition deadline, and return no candidate rather than inventing session material.
- [Native process/IPC changes can misclassify writes] → Preserve command identity, safe points, effect phases, bounded reconciliation, and no automatic replay.
- [Package marker checks can be brittle] → Combine explicit path denial, stable semantic markers, ASAR/resource enumeration, and positive smoke tests rather than relying on minification-sensitive strings alone.

## Migration Plan

1. Extend the manifest, protocol, platform allowlists, typed outputs, and fake-CDP/process fixtures for Facebook and WeChat without routing production traffic.
2. Add a selector-free Facebook Native facade and port read-only identity/page/feed/Reels/detail/probe operations.
3. Port Facebook input operations and their verification: scrolling, like/follow, comment, group join, composer/media, publish, overlay, and consent handling.
4. Switch `FacebookBrowseSession`/handlers to the facade, delete or make unreachable every migrated JavaScript page implementation, and prohibit fallback.
5. Move WeChat browser-session capture behind Native while keeping its API probes and business runtime unchanged.
6. Expand production import pruning and final-package inspection; prove migrated paths/markers and all development probes are absent.
7. Run Rust, focused Edge acceptance, full Edge tests, typecheck, desktop-input verification, and strict OpenSpec validation. Record that no installer was built unless separately requested.
8. Integrate to `master` only after clean rebase and validation. A later release must build/sign/package the eligible revision and complete explicit real Facebook/WeChat client acceptance.

Rollback before release is source revert. Rollback after a later release is distribution of the previous verified installer; the affected page automation remains explicitly unavailable rather than enabling JavaScript fallback.

## Open Questions

- Real Facebook and WeChat acceptance targets require an operator-selected disposable account/environment and are intentionally deferred until source validation is complete and separate interaction authorization is given.
