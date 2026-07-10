## Why

The platform settings page was expanded from model configuration into platform credentials, but the current UI still reads like an incremental form: copy mixes API keys, platform credentials, and restart requirements in one alert, while credential rows lack a clear platform/purpose hierarchy. Operators also reported that paired credential inputs can mirror each other, making AccessKey ID/Secret entry unsafe.

## What Changes

- Redesign `/settings` as a clearer platform settings workspace with distinct model/provider and credential sections.
- Normalize operator-facing copy so model keys, cloud billing AccessKeys, encrypted storage, and restart requirements are described consistently.
- Render credential rows with stable per-credential input state and autofill-safe field metadata so editing one credential cannot update another visible input.
- Add a focused console test covering independent AccessKey ID/Secret editing.
- Keep the existing API contract and encrypted credential behavior unchanged.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `model-provider-config`: Settings page presentation and credential editing UX must keep platform credential inputs independent and operator copy consistent with platform configuration.

## Impact

- aidcp-console: `SettingsPage` layout, copy, credential input handling, and focused tests.
- aidcp control repo: OpenSpec change artifacts and validation notes.
- Production: console static release only; cloud API/runtime behavior is unchanged.
