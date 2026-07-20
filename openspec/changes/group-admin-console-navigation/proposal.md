## Why

The admin console now exposes fourteen top-level destinations in one horizontal pill, so the header overflows at wide breakpoints and becomes an unreadable icon-only strip at narrower widths. The navigation needs a scalable information architecture that keeps labels and current location understandable as more modules are added.

## What Changes

- Replace the flat top-level destination strip with six stable business groups and a persistent second-level destination row.
- Group the existing destinations as Overview, Accounts, Content, Interaction, AI Configuration, and System without changing any route URL.
- Keep the current group and destination visibly active for direct links and nested routes.
- Provide a labelled grouped navigation menu at narrow widths instead of hiding every destination label.
- Keep download, settings, and user actions independent on the right side of the header.
- Continue deriving routes and both navigation levels from one route metadata source.

## Capabilities

### New Capabilities

- `admin-console-navigation`: Covers grouped desktop navigation, narrow-width access, active-route context, and preservation of existing console URLs.

### Modified Capabilities

None.

## Impact

- `aidcp-console/src/routes.tsx`: route navigation metadata and grouping helpers.
- `aidcp-console/src/pages/AppShell.tsx`: grouped primary, secondary, and narrow navigation surfaces.
- `aidcp-console/src/styles/app.css`: two-level header and responsive layout styles.
- Console navigation tests and static `dev` console assets.
- No API, protocol, persistence, or route URL changes.
