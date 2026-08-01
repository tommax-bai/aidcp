## Why

The cross-platform runtime currently reuses `profile.open{direct:true}` for two incompatible operations: Xiaohongshu intentionally navigates to the bound account's profile, while Facebook must read the bound identity in place. The Native cutover preserved the shared command name but reintroduced the Xiaohongshu navigation effect in the Facebook adapter, proving that platform admission alone cannot keep command side effects honest as more platforms are added.

## What Changes

- **BREAKING** Replace startup-time self-identity refresh through `profile.open{direct:true}` with two fixed-effect commands: a runtime current-page identity read that forbids navigation, and a bound self-profile identity read that explicitly permits canonical self-profile navigation.
- Keep `profile.open` exclusively for ordinary author-profile browsing and remove its `direct` self-capture mode.
- Add an exhaustive Cloud platform identity-capture strategy so each platform explicitly selects current-page read, self-profile read, or unsupported; new platforms receive no default or fail-open route.
- Return self-identity observations through a dedicated correlated result instead of overloading social `profile.detail`.
- Advertise and validate exact page-command support across Cloud negotiation, the Edge platform driver, and each Native platform adapter; reject a platform-command mismatch before CDP dispatch.
- Restore Feed only for capture strategies that can leave Feed. Facebook in-place capture sends no recovery navigation.

## Capabilities

### New Capabilities

- `platform-page-command-routing`: Defines fixed-effect page commands, exhaustive per-platform command strategies, negotiated command support, and pre-CDP mismatch rejection.

### Modified Capabilities

- `account-identity-resolution`: Self-identity refresh becomes a platform-selected command with a correlated identity observation and platform-specific restore behavior.
- `facebook-identity`: Facebook runtime identity refresh must use the no-navigation current-page command and must never receive the self-profile navigation command.
- `platform-runtime-abstraction`: Platform drivers and Native adapters must declare exact semantic command coverage instead of relying only on an adapter version and a broad product capability.

## Impact

- Control/protocol: `docs/protocol.md` and synchronized Cloud/Edge protocol types gain explicit identity-capture commands, result payloads, and negotiated capability labels.
- Cloud: the platform registry owns the self-identity capture strategy; `NicknameEnricher` and `RoleDispatcher` stop using `profile.open{direct}` and consume correlated identity observations.
- Edge: command routing and Facebook/Xiaohongshu sessions handle the new command/result contract without JavaScript fallback.
- Native Page Engine: typed commands, platform support matrix, manifest command coverage, Facebook/Xiaohongshu execution, and negative CDP-dispatch tests change.
- No Console, database schema, risk quota, publishing, packaging, signing, installer, or production deployment behavior is included.
