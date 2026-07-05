## Why

The role configuration page is now used to inspect each LLM role's prompt, but several catalogued roles either cannot be previewed or show stale persona wording. This makes operators distrust the role/prompt mapping and can lead them to tune the wrong model category.

## What Changes

- Align role prompt preview with every active catalogued LLM role, including command-style comment-search roles and publish topic roles.
- Correct publish prompt preview persona wording so it matches the production account-persona contract: publish generation uses the selected account persona, while preview uses sample data and must not claim a detached built-in default persona.
- Adjust role catalog category display labels where current labels misrepresent the role responsibility, without changing category keys, runtime dispatch, or prompt behavior.
- Add regression coverage for the newly previewable roles and the corrected publish preview note.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `role-llm-config`: tighten role catalog and prompt preview requirements so all active text LLM catalog entries have faithful read-only preview coverage and publish persona notes match the current account-persona model.

## Impact

- Affected repos: `../aidcp-cloud`, `../aidcp-console`.
- Affected areas: role catalog metadata, prompt preview provider, publish prompt preview builders, admin role category labels, role prompt preview tests.
- No edge protocol, risk-control, database schema, prompt editing, or runtime prompt behavior changes are intended.
