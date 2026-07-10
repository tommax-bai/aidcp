## Why

The Facebook groups page currently exposes one paste box for both simple and structured imports, which makes single-group entry cumbersome and leaves file-based operator workflows unsupported. Operators need an explicit quick-add path and a predictable CSV import path with a downloadable template.

## What Changes

- Replace the shared paste box with two explicit modes: single-group add and CSV file import.
- In single-group mode, accept one Facebook group URL and optional region, park, and direction tags before adding the group.
- In file mode, accept a CSV file, parse metadata-bearing rows, show the selected file and valid-row count, and submit the rows through the existing structured import API.
- Provide a downloadable UTF-8 CSV template with the supported columns.
- Keep region, park, and direction optional, with park presented as a child of region.

## Capabilities

### New Capabilities

- `facebook-group-import-workflow`: Defines the console workflow for single-group addition, CSV upload/import, template download, and operator-facing validation.

### Modified Capabilities

None.

## Impact

- Affected repo: `aidcp-console` for page interaction, CSV parsing, template generation, and focused tests.
- API impact: none; both modes use the existing metadata-bearing `POST /api/facebook/groups/import` contract.
- Dependency impact: no new runtime service; CSV parsing remains browser-side.
- Deployment impact: rebuild and publish console static assets to the default `dev` target after validation.
