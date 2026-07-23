## Why

The production desktop package still exposes Facebook page understanding, selectors, probes, CDP actuation, and post-action verification as readable JavaScript, and its aggregate export keeps calibration probes reachable even when the main runtime does not call them directly. Xiaohongshu has already established the required Rust Native Page Engine boundary; the remaining shipped browser-side intelligence must cross the same boundary or the client retains an obvious cleartext recovery path.

## What Changes

- **BREAKING** Route every production Facebook browse, read, search, interaction, group join, comment, publish, overlay, consent, and verification operation through the required Rust Native Page Engine. Customer builds MUST NOT execute or fall back to Facebook page rules from JavaScript.
- Extend the versioned Native protocol and session model to support Facebook while preserving the current Edge/Cloud command contracts, task ownership, bounded cancellation, effect-phase honesty, and platform-specific capability semantics.
- Move production-reachable Facebook probes and page scripts into the Native artifact. Remove calibration-only probe exports from the production import graph and prove that development probe scripts remain outside the package.
- Move the WeChat Channels browser-session capture boundary that reads cookies, user agent, and the whitelisted authentication request context behind Native. Keep its API capability probes and ordinary request orchestration in TypeScript because they do not implement DOM/page understanding.
- Keep Electron/TypeScript responsible for browser-provider launch, Cloud transport, risk admission, planning, scheduling, account lifecycle, and receipt forwarding. Native receives a selected loopback DevTools endpoint plus typed high-level commands; it MUST reject arbitrary selector, JavaScript, raw-CDP, and credential-bearing command surfaces.
- Expand production-dist and final-package inspection to reject migrated Facebook/WeChat browser-rule modules, source maps, representative cleartext markers, accidental development probes, and architecture/protocol-invalid Native artifacts.
- Use installer/package rollback only. Missing, incompatible, or crashed Native execution fails explicitly and never enables a JavaScript fallback or retries an ambiguous write.
- Do not rewrite pure API/business orchestration merely for obfuscation, change customer authentication/client communication, or alter Cloud planning and risk ownership.

## Capabilities

### New Capabilities

- `native-page-engine-platform-coverage`: Required Native ownership of all production Facebook page intelligence and the WeChat Channels browser-session capture boundary, including typed protocol coverage, honest execution, probe treatment, and no-JavaScript-fallback cutover.

### Modified Capabilities

- `edge-desktop-packaging`: Official packages must exclude all migrated cross-platform browser rules and all development probes, and must verify the expanded Native artifact against the final package.
- `client-core-browser-executor-separation`: The browser-independent Edge core must supervise Native sessions for every migrated platform while retaining browser-provider and Cloud lifecycle ownership.
- `edge-task-execution-coordination`: Facebook writes and WeChat session capture must preserve task identity, cancellation, deadline, duplicate-command, and ambiguous-effect guarantees across Native IPC.
- `platform-runtime-abstraction`: Facebook capability declaration and executor assembly must resolve to the Native executor without changing the existing platform capability contract.
- `wechat-local-browser-inspection-control`: Local WeChat browser inspection must obtain its whitelisted session material through Native while preserving lease and teardown truth.

## Impact

- `aidcp-edge/native/page-engine`: gains multi-platform session selection, Facebook command families/page scripts, WeChat session capture, bounded result types, and fixture/process tests.
- `aidcp-edge/src/facebook`, `src/wechat-channels/browser-sidecar.ts`, `src/main.ts`, and Native IPC supervision: become selector-free typed facades or lose production reachability; Cloud-facing contracts remain stable.
- `aidcp-edge/scripts/prune-production-dist.mjs`, desktop build verification, and package inspection: expand from Xiaohongshu-only leakage checks to platform-wide production reachability and final-artifact checks.
- Validation: Rust unit/fixture/fake-CDP/process suites, focused Edge acceptance tests, full Edge tests and typecheck, strict OpenSpec validation, and an explicit real-client Facebook/WeChat acceptance gate before any installer release.
