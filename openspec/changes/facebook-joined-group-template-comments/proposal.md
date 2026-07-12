## Why

Facebook account comment configuration currently mixes account-level search intent with an operator-maintained group/container allowlist. That makes the account setup harder to operate now that joined-group coverage already tracks each account's own joined groups and can select least-recently-commented groups with warmup/cooldown controls.

Operators also need a controlled template-comment mode for accounts whose comments should use preapproved fixed text instead of content-derived LLM generation, while still preserving contact-info injection, human review, and the no-whole-site-search safety model.

## What Changes

- Remove the operator-facing group/container selector from the account "FB configuration" UI; keep account-level search keywords.
- Make normal Facebook comment runs select their search container from the account's joined-group membership ledger, using the existing coverage selection behavior: normal warmup/cooldown first, then the existing relaxed least-recently-commented fallback when no timed-eligible group exists.
- Keep edge execution scoped to a concrete `search.execute.container` group URL. This change MUST NOT introduce Facebook whole-site search.
- Add account-level comment content mode: generated comment or template comment.
- Add multiple per-account comment templates. Template mode chooses one configured template and skips LLM comment generation, while still searching/opening a target post and validating the final body before submit.
- Keep contact comments as separated body + account contact info: template/generated text is `text`; account contact info is injected through the existing contact-info lane and human-review card.
- Preserve backward compatibility for existing stored `containers` data during rollout, but stop requiring or editing it from the account FB configuration screen.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `facebook-scheduled-comment`: Account FB configuration changes from keywords + configured containers to keywords + comment mode + templates; runtime container source changes to the account joined-group ledger for normal Facebook comment runs.
- `facebook-group-comment-coverage`: The joined-group coverage selector becomes the normal Facebook comment container source, including the existing relaxed least-recently-commented fallback when warmup/cooldown do not yield a candidate.

## Impact

- `aidcp-cloud`: Facebook comment config store/schema, panel API DTOs, comment scheduler target selection, template selection, validation/audit behavior, and tests.
- `aidcp-console`: account FB configuration modal, mirrored API types, and UI tests.
- `aidcp-edge`: no expected protocol or execution change if cloud continues to send a concrete group URL in `search.execute.container`.
- Database: additive JSONB columns for comment mode/templates or equivalent self-healing schema additions; legacy `containers` data remains readable for compatibility but no longer drives the normal account configuration UI.
