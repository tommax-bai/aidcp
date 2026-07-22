## Why

The shipped Electron application currently keeps page understanding, locating, and CDP behavior in readable JavaScript, so unpacking the desktop artifact exposes the implementation directly to source-oriented AI tools. Before committing to a full rewrite, AIDCP needs a bounded, read-only proof that a signed Rust sidecar can own the browser-facing CDP session and return useful page state without changing production automation behavior.

## What Changes

- Add an opt-in Rust Native Page Engine spike that receives an existing AdsPower/self-provider CDP endpoint and independently discovers a page target.
- Define a versioned local IPC contract that sends only endpoint/probe inputs and returns structured page-state evidence; selectors, browser scripts, and raw CDP messages remain inside the native process.
- Limit the spike to read-only CDP operations. It MUST NOT dispatch `Input.*`, mutate the DOM, submit content, or become a production action writer.
- Add deterministic fixture/protocol tests plus a development probe entrypoint so the native result can be compared with the existing JavaScript path.
- Establish a build and desktop-resource staging path for the host-architecture native binary while keeping the normal packaged client unchanged unless the explicit probe build is requested.
- Preserve the current JavaScript executor as the sole production page-action implementation during the spike; no Cloud protocol, customer authentication, scheduling, risk, or platform-write semantics change.

## Capabilities

### New Capabilities

- `native-page-engine`: Opt-in, read-only native CDP attachment, structured page-state probing, local IPC honesty, and bounded desktop staging for the Rust feasibility spike.

### Modified Capabilities

None. The spike is opt-in and does not change baseline production requirements.

## Impact

- `aidcp-edge`: new Rust crate/binary, TypeScript IPC client and development probe, focused tests, build scripts, and optional desktop resource staging.
- Tooling: introduces a pinned Rust toolchain and Cargo dependency/build cache requirements for native-spike builds.
- Packaging: native artifacts are outside ASAR and require architecture-correct staging and signing before any distributable package can enable the spike.
- Runtime boundaries: browser provider ownership and Cloud connectivity remain in the existing Edge process; the Rust process owns only its read-only probe CDP connection.
- No deployment, installer publication, customer rollout, real interaction, or production executor cutover is included.
