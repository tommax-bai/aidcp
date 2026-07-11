## Context

`aidcp-cloud` already stores Facebook group targets in `facebook_group_target` keyed by a canonical group URL. `aidcp-console` currently imports URL-only text and shows flat status/enabled filters. Operators now need business metadata filters, and their source data often comes from pasted spreadsheet grids with merged region headers, repeated `序号 + 园区名` pairs, and trailing direction columns.

## Goals / Non-Goals

**Goals:**
- Store optional `region`, `park`, and `direction` metadata on Facebook group targets.
- Keep URL canonicalization server-owned so duplicate detection is independent of console parsing quality.
- Let the console parse wide pasted spreadsheet data into structured import items.
- Provide optional exact-match filters and filter facets for region, park, and direction.
- Keep URL-only import and existing rows backward compatible.

**Non-Goals:**
- Build a general spreadsheet engine or file upload flow.
- Require every group target to have metadata.
- Infer or validate a fixed master list of Vietnamese parks/directions.
- Change join scheduling, assignment, membership, or comment coverage behavior.

## Decisions

- Store metadata as nullable text columns on `facebook_group_target`.
  - Rationale: metadata is operator-facing classification, not a separate lifecycle object today. Nullable columns keep existing rows and imports valid.
  - Alternative considered: normalized region/park tables. Rejected for v1 because there is no authoritative master-data owner yet and no write UI for taxonomy management.
- Treat `region`, `park`, and `direction` as independent optional filters in the API, while the console presents `park` as dependent on selected `region`.
  - Rationale: backend remains simple and script-friendly; the UI still matches the operator mental model that parks belong under a region.
  - Alternative considered: reject `park` without `region` at the API. Rejected because it is an unnecessary breaking constraint for API users and tests.
- Put wide paste parsing in `aidcp-console`; keep cloud import structured.
  - Rationale: the console has the raw paste context and can show operator-facing preview/errors. Cloud remains the final validator and canonicalizer.
  - Alternative considered: parse wide tables in cloud from `text`. Rejected because it would mix UI paste heuristics into the server API and still need console preview logic later.
- Canonicalize Facebook group URLs by storing only `https://www.facebook.com/groups/<slug-or-id>`.
  - Rationale: Facebook share/query parameters (`?ref`, `?cft`, `?tn`, locale/action_source, fragments) are volatile tracking/context data and cause duplicate targets. The stable group identifier is the path segment immediately after `/groups/`.
  - Alternative considered: preserve the original URL as entered. Rejected because scheduling and duplicate detection need one stable key. The original paste is not needed for execution.
- For existing rows, metadata imports update missing/changed metadata but do not reset membership state.
  - Rationale: re-importing a richer catalog should enrich existing targets instead of being reported only as duplicate work. Membership/assignment tables still reference the same canonical `group_url`.

## Risks / Trade-offs

- [Risk] Wide paste heuristics may misclassify unusual columns. -> Mitigation: only attach metadata when headers are detected; otherwise fall back to URL-only rows.
- [Risk] Region labels from merged Excel cells may appear only once. -> Mitigation: parser carries the last non-empty region header across following columns until a new region header appears.
- [Risk] Direction and park labels may overlap semantically. -> Mitigation: park labels come from `序号 + label` column pairs under a region; trailing non-park URL columns become direction labels.
- [Risk] Re-import updates metadata on existing targets unexpectedly. -> Mitigation: only metadata/name/import batch are updated; enabled, priority, join gating, and membership state are untouched.

## Migration Plan

1. Add nullable columns and indexes to `facebook_group_target`.
2. Extend cloud DTOs, import input validation, list filtering, and facets API.
3. Extend console types, paste parser, import payload, filters, and target table metadata display.
4. Run focused cloud/console tests and typechecks.
5. Deploy to dev only after validation; rollback is safe because old code ignores the additive columns.

## Open Questions

- Whether a future taxonomy management page should own region/park/direction options. V1 derives options from stored target rows.
