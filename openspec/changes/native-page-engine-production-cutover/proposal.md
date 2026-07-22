## Why

The shipped Electron client still carries Xiaohongshu page understanding, selectors, CDP actuation, retry, and post-action verification as readable JavaScript. The completed Rust spike proved that a standalone native process can own the real AdsPower CDP connection and return honest semantic state, and the product decision is now to skip shadow execution and cut production Xiaohongshu page automation directly to Native.

## What Changes

- **BREAKING** Route every production Xiaohongshu `page_automation` command through a required Rust Native Page Engine. The shipped client MUST NOT dual-run, compare against, or fall back to the legacy JavaScript Xiaohongshu executor.
- Extend the native engine from a one-shot read-only probe into a supervised, long-lived executor that owns target discovery, CDP attach/reconnect, page understanding, locating, humanized actuation, bounded retry, and post-action verification for the existing Xiaohongshu browse, search, note, interaction, notification, profile, captcha-assistance, legacy plan-step, and both legacy and atomic publish command surfaces.
- Keep Electron/TypeScript responsible for customer/core lifecycle, browser-provider startup, Cloud protocol v2, operation classification, task leases, authorization, and receipt forwarding. Native receives only the selected loopback DevTools endpoint plus high-level, versioned commands; it does not receive arbitrary selectors, JavaScript, raw CDP methods, credentials, prompts, or planning policy.
- Preserve all existing honesty, account-identity, risk, approval, cancellation, attribution, publish-integrity, and recovery contracts. A Native process crash or protocol drift fails the active page task explicitly and never replays an ambiguous write or reroutes it to JavaScript.
- Package architecture-correct Native binaries outside ASAR for supported macOS and Windows targets, verify hashes/architecture/protocol compatibility, sign the nested executable in release builds, and fail packaging/startup when the required artifact is absent or invalid.
- Remove migrated Xiaohongshu selectors, browser scripts, and CDP action implementations from distributable JavaScript. Build-time inspection MUST prove the customer artifact does not contain the forbidden legacy rule modules or representative cleartext rule markers.
- Use installer/package rollback as the production rollback mechanism. No runtime feature flag may re-enable the legacy Xiaohongshu JavaScript executor in a customer build.
- Do not change Cloud planning, protocol v2 message names/payloads, customer authentication, risk ownership, account scheduling, or non-Xiaohongshu platform executors.

## Capabilities

### New Capabilities

- `native-page-engine-production`: Required direct-production Native execution for the complete Xiaohongshu page-command surface, including high-level IPC, CDP lifecycle, safety/honesty semantics, JS-core removal, and release cutover without shadow or fallback.

### Modified Capabilities

- `edge-desktop-packaging`: Official desktop packages must include, verify, and sign the architecture-correct Native Page Engine while excluding migrated Xiaohongshu JavaScript core rules.
- `client-core-browser-executor-separation`: The browser-independent Edge core now supervises a native page executor after page-automation admission while preserving the existing independent core/browser lifecycle.
- `edge-task-execution-coordination`: Page-task ownership, cancellation, deadlines, and ambiguous-write handling must cross the Native IPC boundary without replay or JavaScript fallback.
- `pluggable-browser-provider`: The provider-neutral loopback DevTools handle is handed to Native, which owns downstream Xiaohongshu CDP attachment and recovery without provider-specific page branches.

## Impact

- `aidcp-edge/native/page-engine`: expands into the production Xiaohongshu page executor and owns all migrated page rules and CDP writes.
- `aidcp-edge/src/main.ts`, execution routing, browser/provider integration, publish dispatch, and Native IPC supervision: replace JavaScript Xiaohongshu handlers with high-level Native commands while keeping the Edge/Cloud contract stable.
- `aidcp-edge/src/browse`, Xiaohongshu publish/action modules, and desktop build inputs: migrated rule code is removed from or explicitly excluded from distributable JavaScript; non-Xiaohongshu shared code remains available.
- Desktop CI/release: adds Rust build targets, artifact manifest verification, nested signing/notarization coverage, packaged smoke tests, and post-package leakage scans.
- Tests: adds Rust fixture/integration suites for every migrated command, TypeScript supervision/routing tests, existing Edge acceptance/full-suite coverage, package inspection, and authorized real-machine Xiaohongshu acceptance before release.
- Runtime cost: the Native process becomes a required page executor for Xiaohongshu. Missing/incompatible Native artifacts make Xiaohongshu page automation unavailable with an explicit error rather than silently degrading.
