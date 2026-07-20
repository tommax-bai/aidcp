## Why

Facebook Edge currently performs its first identity read immediately after CDP attachment, while an AdsPower tab can still be `about:blank`. The stable numeric id is then recovered from `c_user`, but the nickname scan runs against the blank document and completes before the browse session navigates to Facebook; accounts whose localized self-link `aria-label` is not covered also remain empty, so nickname updates depend on a later `page.cards` fallback that may never fire on newer feed layouts.

## What Changes

- Make the navigation-enabled Facebook startup identity read bootstrap only a non-Facebook blank/unrelated tab to the configured Facebook consumer start page, then wait with a bounded budget for a real Facebook page before collecting identity signals.
- Keep runtime identity checks and Cloud-triggered `profile.open{direct}` reads strictly in-place and navigation-free; the startup bootstrap MUST NOT navigate to `/me` or a profile page.
- Capture both `aria-label` and visible text from profile anchors, and accept visible text only when the anchor is bound to the already-established numeric self id (or the `/me` self-link), so localized layouts such as Vietnamese do not require language-specific suffix parsing.
- Treat startup hello nickname capture as the primary Facebook refresh path once the consumer page is ready; retain the existing honest empty result and later in-place fallback without making nickname refresh depend on feed-card extraction.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-identity`: Add bounded startup page bootstrap/readiness semantics and an id-anchored visible-text nickname source while preserving no-navigation runtime reads and honest empty results.
- `account-identity-resolution`: Clarify that Facebook may complete verified nickname refresh during the startup identity/hello path after browser-page readiness, independently of whether the first feed layout emits cards.

## Impact

- Affected implementation: `aidcp-edge` Facebook identity reader, startup option selection, and direct-profile caller safeguards.
- Affected validation: focused Facebook identity/session tests, Edge acceptance suite, full Edge tests, and typecheck.
- No protocol shape, Cloud persistence schema, account-id semantics, risk state, or installer packaging changes.
