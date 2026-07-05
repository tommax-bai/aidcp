## Why

The admin usage page groups model usage by account, role, provider, and model, but image generation currently bypasses the token usage recorder. Operators can see the `publish:ImageGenerator` role and the configured image model in the role/settings pages, yet successful or failed image generation calls never appear on `/usage`.

This makes image-model activity look missing, especially for publish runs that generate images through Wanxiang or Seedream.

## What Changes

- Record image generation attempts into the existing usage store with role `publish:ImageGenerator`, the active image provider, and the active image model.
- Keep token honesty: image providers do not return token counts, so image rows record calls/ok_calls with prompt/completion/total tokens as 0.
- Keep image billing separate from token price refresh: image rows must not become token billing price refresh targets.
- Update console usage labels and copy so image rows are understandable without implying token consumption.
- Add focused cloud and console tests.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `llm-token-usage-stats`: the usage page records image generation model attempts as model-usage call rows, with honest zero-token counts and stable role/provider/model dimensions.

## Impact

- aidcp-cloud: image provider usage instrumentation, token usage target filtering, tests.
- aidcp-console: usage role labels/page wording and tests.
- aidcp control repo: OpenSpec proposal/spec/tasks and validation.
- Production: cloud restart and console static release are required after code changes; no database schema or secret change is expected.
