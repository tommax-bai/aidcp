## Context

`/settings` now covers both model/provider configuration and platform credentials. The current console implementation keeps the old single-card form shape and uses one high-level alert for several different concepts: model changes, encrypted credential storage, plaintext safety, and cloud restart timing. Credential rows are technically data-driven, but they do not present AccessKey ID/Secret as a paired platform credential workflow, and browser autofill can treat repeated password fields as related credentials.

The cloud API already returns enough metadata for a better UI: provider, field, label, providerLabel, group, groupLabel, secretKind, restartRequired, configured state, source, and masked hint. This change should consume that metadata more carefully without changing the API.

## Goals / Non-Goals

**Goals:**

- Make settings read as a platform configuration page with clear sections and consistent operator copy.
- Keep model/provider controls visually separate from credential maintenance.
- Render platform credentials as stable, independent editable rows, especially AccessKey ID/Secret pairs.
- Reduce password-manager ambiguity by using per-credential `name` and `autoComplete` metadata instead of repeated generic password fields.
- Add a focused regression test for independent credential input state.

**Non-Goals:**

- Do not change `GET /api/config/model`, `PUT /api/config/model`, or `PUT /api/config/credential`.
- Do not change encryption, masking, restart semantics, or credential whitelist behavior.
- Do not add credential deletion or scheduled billing sync.
- Do not deploy cloud runtime changes.

## Decisions

### D1: Keep API shape unchanged and redesign only the console view

The existing API already exposes the metadata needed for platform labels and credential grouping. Changing the API would increase drift risk across cloud and console without solving the reported UI bug.

Alternative considered: add a nested credential group DTO. Rejected because the console can derive grouping locally and this issue is presentation-only.

### D2: Use a stable credential id for input state and form metadata

Each input will be keyed by `provider::field`, and the same id will be used in DOM `name`/`id` attributes. This keeps React state independent and gives browser autofill a unique field identity.

Alternative considered: keep `provider/field`. It is logically unique, but using a dedicated helper and DOM metadata makes the independence explicit and testable.

### D3: Present credentials as purpose-grouped rows with precise copy

Model API keys and billing AccessKeys will remain in separate groups. Rows will display provider label, credential label, current source, masked hint, and restart impact. Placeholders and save buttons will avoid vague "key" wording where the field is specifically an AccessKey ID or AccessKey Secret.

Alternative considered: split each platform into a custom two-column AccessKey pair component. Rejected for now because the API is field-oriented and a reusable row keeps model keys and billing keys consistent while preserving independent inputs.

## Risks / Trade-offs

- [Risk] Browser password managers may still offer autofill UI on secret inputs. → Mitigation: use unique `name`/`id` values and field-specific `autoComplete` tokens; test React-level independence.
- [Risk] More structured UI can become visually heavy. → Mitigation: use restrained section headers and compact rows, matching the existing Ant Design-based console language.
- [Risk] Copy can overstate runtime effect. → Mitigation: retain the honest distinction between saved encrypted credentials and cloud restart-required runtime use.

## Migration Plan

Ship as a console-only static release. Rollback is replacing the console bundle with the previous deployed console backup; cloud runtime and database state are unaffected.
