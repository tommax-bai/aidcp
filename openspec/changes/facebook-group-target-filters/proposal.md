## Why

Facebook group operations now need a manageable target catalog instead of a flat URL pile. Operators also receive group lists as wide spreadsheet exports where region headers span many park columns, so paste import must preserve business metadata while still storing a canonical Facebook group key.

## What Changes

- Add optional metadata to Facebook group targets: region, park, and direction.
- Make park a second-level filter under region; none of region, park, or direction is required for import or filtering.
- Extend the Facebook groups API and console page to filter by region, park, and direction in addition to existing status/enabled filters.
- Support paste-import from both existing URL-only text and the provided wide spreadsheet-like format where region headers sit above repeated `序号 + 园区名` column pairs.
- Canonicalize Facebook group URLs on import by dropping query strings/fragments and storing only the stable group URL; duplicate detection uses the canonical URL.

## Capabilities

### New Capabilities

- `facebook-group-target-catalog`: Defines the operator-managed Facebook group target catalog, metadata import, canonical URL storage, and optional region/park/direction filtering.

### Modified Capabilities

- `console-panel-api`: Extends the existing `/api/facebook/groups` management API with optional metadata filters and metadata-bearing import items.

## Impact

- Affected repos: `aidcp-cloud` for storage/API/import contracts, `aidcp-console` for wide paste parsing and filter controls, `aidcp` for OpenSpec.
- Storage impact: additive nullable columns on `facebook_group_target`; existing rows remain valid with null metadata.
- API impact: additive fields in group target DTOs and optional query parameters; existing URL-only imports remain accepted.
- Operational impact: imported Facebook group URLs are cleaned before storage, reducing duplicate rows caused by tracking/query parameters.
