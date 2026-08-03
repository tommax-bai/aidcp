## Why

The installed desktop client can spawn an environment core and then throw synchronously while projecting its Cloud target, before stdout, IPC, error, exit, and close handlers are attached. The orphaned supervisor handle remains `starting` even after the real core times out and exits, so restarting the client deterministically reproduces the failure and deleting runtime state cannot repair it.

## What Changes

- Project the environment's startup Cloud target from the same frozen target key already injected into that child process.
- Attach child lifecycle and cleanup handling before any fallible post-spawn status publication.
- Convert any synchronous post-spawn setup failure into an honest per-environment launch failure: clear the dead child handle, release launch readiness, preserve sibling launches, and expose a stable reason instead of leaving a ghost `starting` state.
- Add executable regression coverage for successful spawn initialization and post-spawn failure cleanup; source-text assertions alone are insufficient.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-cloud-env-selection`: Require the supervisor's pending target projection to use the exact frozen deployment target injected into the spawned core.
- `edge-multi-environment-supervisor`: Require lifecycle observers to be established before fallible post-spawn work and require synchronous setup failures to be reaped and surfaced without blocking sibling launches.

## Impact

- `aidcp-edge`: Electron supervisor startup ordering and focused lifecycle regression tests.
- `aidcp`: OpenSpec deltas and implementation evidence.
- No protocol, Cloud runtime, database, account data, AdsPower profile data, deployment, packaging, installation, or real-platform action is required.
