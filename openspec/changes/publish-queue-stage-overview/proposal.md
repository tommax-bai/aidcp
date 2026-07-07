## Why

The management console's in-flight publish queue currently exposes the raw pipeline snapshot as dense key/value detail. When several rewrite-triggered drafts are flowing through the global generation lane, operators cannot quickly see which stage has completed, what is still running, or which draft/source is being processed.

## What Changes

- Replace the raw-first queue snapshot view with a compact stage overview for the active publish generation lane.
- Surface the operator-facing essentials first: queue status, active account/source/title when available, completed/current/pending stages, and concise per-stage facts.
- Keep raw snapshot details available in a secondary disclosure for troubleshooting; do not hide unknown future fields.
- Do not change the `/api/content/queue` response contract or publish pipeline behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `console-panel-api`: the console presentation of `GET /api/content/queue` SHALL summarize in-flight publish snapshots by stage while preserving raw details for diagnostics.

## Impact

- Affected repo: `aidcp-console`.
- Affected files: content page rendering, content page tests, and supporting CSS.
- No cloud API, database, protocol, edge, or publish runtime behavior changes.
