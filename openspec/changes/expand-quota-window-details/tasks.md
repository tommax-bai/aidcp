## 1. Specification

- [x] Add OpenSpec delta for expandable complete quota-window details.
- [x] Validate the OpenSpec change with `openspec validate expand-quota-window-details --strict`.

## 2. Cloud

- [x] Include complete session-window totals for view, like, collect, comment, follow, and publish when an active session context exists.
- [x] Keep session quotas honest: only actions with real session caps carry quotas.
- [x] Include timing metadata for minute/hour/day windows so Electron can expire stale rolling-window status.
- [x] Add or update cloud tests for complete session-window payload behavior.

## 3. Edge And Electron

- [x] Keep the collapsed daily summary focused on account daily totals.
- [x] Make the daily summary card expandable/collapsible.
- [x] Render complete per-window detail rows for session, minute, hour, and day with all six actions.
- [x] Expire stale minute/hour window saturation locally when no fresh cloud snapshot arrives.
- [x] Add or update edge/Electron tests for collapsed and expanded rendering.

## 4. Documentation, Validation, Release

- [x] Update protocol documentation.
- [x] Run relevant cloud and edge tests/typechecks.
- [ ] Commit and push control/cloud/edge changes.
- [ ] Deploy cloud runtime if server behavior changed and verify production health.
- [ ] Rebuild/publish the Windows Electron installer.
