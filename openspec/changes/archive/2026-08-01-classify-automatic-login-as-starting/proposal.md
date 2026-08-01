## Why

An environment can remain in `需要处理` after Facebook credentials become available and the retained authentication coordinator resumes password/TOTP actions automatically. This tells the operator to intervene while the system is already progressing on its own, and a later stopped process can further collapse the authentication fact into `离线`.

## What Changes

- Classify authentication that can continue without operator input as the normal startup lifecycle, shown as `登录中` inside the existing `启动中` group.
- Reserve `需要处理` for explicit manual-input, QR, human-verification, unsupported-checkpoint, or terminal authentication states that cannot make autonomous progress.
- Clear an earlier manual-login projection as soon as the same retained authentication coordinator structurally confirms an actionable automatic login step.
- Preserve the distinction through process supervision so an authentication failure that requires action does not silently fall back to ordinary offline state.
- Keep `运行中` reserved for current executable task evidence; automatic login does not claim that account automation is already ready.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-fleet-console`: Define the mutually exclusive automatic-login startup state and manual-login attention state, including their transition and terminal-failure projection.

## Impact

- Affected repo: `aidcp-edge`.
- Affected areas: Facebook startup authentication coordination, generation-scoped Electron lifecycle IPC, environment status projection, rail/health presentation, and focused tests.
- No Cloud API, protocol v2, database, proxy, credential storage, TOTP generation, browser action policy, packaging, deployment, or live-account action is included.
