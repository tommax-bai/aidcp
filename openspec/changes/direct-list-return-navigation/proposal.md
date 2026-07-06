## Why

Repeated `navigation.back` incidents show that browser history is still a fragile way to recover from note detail, notification, and profile excursions. When history points at an expired Xiaohongshu detail route, the browser can surface the "current note cannot be browsed" access modal and the edge overlay monitor treats the session as blocked.

## What Changes

- Prefer direct, forward navigation to the known source list when returning from a note/detail excursion.
- Preserve the existing return contract and `action.completed{action:'back', ok:true}` acknowledgement.
- Keep search-origin returns distinct from feed-origin returns; do not blindly collapse all returns to explore feed.
- Treat the Xiaohongshu `access-modal` / `access-limit-app` page-level note restriction as a recoverable note access condition, not as an account-level captcha incident.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `browse-loop-resilience`: Return-to-list navigation should prefer direct source-list navigation and avoid browser history unless explicitly allowed for a safe, still-open note overlay.
- `captcha-incident-handling`: Xiaohongshu note access-limit modals should not be reported as captcha/unknown account blocking incidents when they are recoverable by returning to the list.

## Impact

- Edge browse session return logic in `aidcp-edge`.
- Edge modal/access-overlay detection around Xiaohongshu note access-limit modals.
- Focused browse-session and overlay tests.
- Control-repo OpenSpec specs and task tracking.
