## Why

The current "model config" settings page now owns more than model names: operators also need to manage platform-level provider credentials such as billing AccessKey pairs used by cost refresh. Keeping billing credentials outside the console causes manual price refresh to skip every model day with `missing_credentials`, even when model API keys are already configured.

## What Changes

- Reposition the existing settings page from "model config" to "platform config".
- Keep global text/image provider and model controls in the page, but present them as one section of broader platform configuration.
- Extend platform credentials to include billing AccessKey ID/Secret pairs for Alibaba Cloud billing and Volcengine billing, using the existing encrypted `provider_credentials` store.
- Continue to never return plaintext credentials; show only configured state, masked hint, source, and operator-facing labels.
- Make manual provider/model price refresh use the same platform credential records, so operators can fix `missing_credentials` from the console instead of editing ECS env manually.
- Do not add scheduled billing sync or change token-cost estimation semantics.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `model-provider-config`: settings becomes platform configuration and its credential whitelist/view expands beyond model API keys to platform billing credentials.

## Impact

- aidcp-cloud: credential whitelist, `/api/config/model` view shape, panel config route tests, billing refresh credential lookup path.
- aidcp-console: settings page labels/layout/types and credential editing UI.
- aidcp control repo: OpenSpec delta, tasks, validation notes.
- Production: cloud restart required for newly saved credentials to affect runtime billing refresh, matching existing encrypted credential behavior.
