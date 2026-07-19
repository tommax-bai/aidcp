## Why

The desktop client currently exposes five fixed "machine templates" when creating AdsPower environments. Those templates pin too many stable machine attributes, so repeated creations from the same template can produce highly similar profiles. AdsPower already provides fingerprint generation during `user/create`; the client should use that capability as the primary source of per-profile variation.

## What Changes

- Replace the operator-facing machine-template choice with an OS-family choice.
- Build a minimal `fingerprint_config` that constrains only the required OS family and safety policy, then lets AdsPower generate the remaining fingerprint details.
- Keep proxy submission, group resolution, provisioning intents, client ownership assignment, and roster confirmation unchanged.
- Keep a local guardrail that rejects inconsistent OS requests before `user/create`.
- Update Facebook batch creation so each row chooses an OS family independently instead of one of five fixed machine templates.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `adspower-environment-provisioning`: AdsPower environment creation becomes OS-family constrained and AdsPower-first for fingerprint generation.
- `adspower-desktop-env-picker`: the creation UI presents OS families instead of fixed machine templates.

## Impact

- `aidcp-edge` Electron fingerprint construction, creation IPC payload naming, and renderer labels.
- Focused Electron tests covering fingerprint config shape, single creation, Facebook batch planning, and renderer behavior.
- No cloud or console API changes.
