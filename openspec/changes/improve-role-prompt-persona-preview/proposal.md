## Why

The role prompt viewer currently renders faithful prompt templates, but the persona source can be easy to miss and one browse role (`精选准入·正文评估`) loses persona highlighting because its `personaSegments()` text no longer matches its actual prompt. Operators can mistake sample runtime inputs for an unreal prompt, or miss whether the preview is using a selected account persona.

## What Changes

- Fix `精选准入·正文评估` persona source segmentation so the highlighted persona span matches the exact prompt text rendered by the role.
- Make the role prompt preview surface the selected persona source more prominently in the role model configuration page.
- Make preview notes honest for no-account and selected-account cases: sample runtime inputs remain sample, while persona source is either sample persona, selected account persona, or explicit fallback.
- Add regression coverage for curated note evaluator segmentation and persona-source notes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `role-llm-config`: tighten prompt preview persona-source clarity and faithful persona segmentation requirements.

## Impact

- Affected repos: `../aidcp-cloud`, `../aidcp-console`.
- Affected areas: browse role prompt preview segmentation, role prompt preview provider notes, admin role model configuration prompt modal, prompt preview tests.
- No database schema, edge protocol, runtime prompt behavior, model dispatch, risk-control, or prompt editing support changes are intended.
