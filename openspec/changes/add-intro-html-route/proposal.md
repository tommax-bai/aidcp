## Why

The deployed console serves `/intro.html` as the same static HTML bundle as the
main app, but React Router has no matching route for that path. Operators who
open the legacy intro URL therefore see an application-level 404 even though
the console service and static assets are healthy.

## What Changes

- Add `/intro.html` as a supported console SPA entry alias.
- Preserve normal authentication behavior: unauthenticated users are sent to
  `/login`, and authenticated users land in the standard console shell.
- Keep the existing root, login, and business routes unchanged.

## Capabilities

### New Capabilities

- `console-static-entry-routing`: supported static entry URLs for the
  `aidcp-console` SPA and their authenticated/unauthenticated behavior.

### Modified Capabilities

- None.

## Impact

- aidcp-console: React Router route table and focused route regression coverage.
- aidcp control repo: OpenSpec change artifacts and validation notes.
- Production: console static release only; cloud API/runtime behavior is unchanged.
