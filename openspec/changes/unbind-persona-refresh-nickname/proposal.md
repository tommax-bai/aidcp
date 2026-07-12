## Why

Operators need two account-maintenance actions to reflect runtime truth instead of preserving stale configuration. Clearing a persona in the admin console should intentionally unbind the account, and a started XHS/Facebook task should refresh the stored display nickname when the platform account name has changed.

## What Changes

- Admin persona editing treats an empty saved editor as an explicit unbind request: the account returns to `source=none` / "未绑定" and will be blocked by existing persona gates until a valid persona is saved again.
- Cloud persona APIs return the post-unbind truth state instead of rejecting empty persona text as `persona_required`.
- XHS and Facebook startup identity/nickname checks run even when a nickname already exists in the system.
- When the platform-reported nickname is non-empty and differs from the stored nickname, cloud updates the stored nickname to the new verified value.
- Nickname refresh remains display-only: stable account id still owns routing, identity, limits, and task attribution.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `account-persona-config`: Empty persona saves now unbind the account instead of being rejected.
- `account-identity-resolution`: Startup nickname checks refresh display names when verified platform nicknames differ from stored values.
- `facebook-identity`: Facebook startup nickname persistence may update an existing nickname when the verified handshake nickname differs.

## Impact

- Cloud: persona facade/store API behavior, panel persona endpoint, nickname capture/write policy, and related unit tests.
- Console: persona page empty-editor validation and messaging so clear-and-save becomes "解绑" rather than a client-side error.
- Edge: ensure XHS and Facebook startup paths expose verified nicknames on every startup check where the platform can provide one.
- Runtime: existing persona gates continue to block unbound accounts; nickname updates affect only display and human account selection by nickname.
