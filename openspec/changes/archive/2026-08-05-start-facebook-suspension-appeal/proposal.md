## Why

An imported Facebook profile can reach a loaded account-suspension checkpoint whose supported recovery entry is a visible `Appeal` control, but the startup auth reconciler currently reports every checkpoint as unsupported and leaves the environment blocked. The observed page also retains a hidden disabled `Appeal` clone, so a text-only action would be ambiguous and unsafe.

## What Changes

- Add one independent Native Facebook auth signal for the observed account-suspension checkpoint and one matching action that starts the appeal with trusted CDP pointer input.
- Require the exact suspension route and content, exactly one visible enabled topmost `Appeal` target, fresh signal binding, and one-signal-one-action replay protection.
- Wait through bounded loading and confirm only that the original suspension entry page advanced to a distinct loaded Facebook checkpoint step; button disappearance, loading, or an arbitrary navigation is not success.
- Stop after the appeal entry advances and keep the browser available for the operator. Do not fill, choose, confirm, or submit any later appeal step.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-browser-environment`: Extend bounded Facebook startup reconciliation with the observed suspension-appeal entry while preserving fail-closed target and postcondition rules.

## Impact

- `aidcp-edge` Native Page Engine auth router, command/model/capability registries, and the TypeScript startup auth coordinator.
- Focused router, command, coordinator, and parity tests plus Native postcondition documentation.
- No Cloud protocol, Cloud service, Console, database, account-risk writer, deployment target, or installer change.
