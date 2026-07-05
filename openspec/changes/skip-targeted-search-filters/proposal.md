## Why

Targeted comments locate a known curated note by searching with the note title and then matching the returned `noteId`. The current implementation sends `sort: "comprehensive"` and `timeWindow: "all"` to avoid inheriting the `/comment` defaults, but the edge treats any supplied filter values as a request to open the native search filter panel.

On the XHS AI search page, the default values "comprehensive" and "all" do not reliably produce the same committed-filter signal used by non-default filters. The result is repeated clicks on "comprehensive" / "all" with no useful filtering, extra delay, and misleading downgrade logs. Targeted search does not need this panel at all because exact `noteId` match is the authority.

## What Changes

- Targeted curated-note comments stop sending `sort` and `timeWindow` in `search.execute`.
- The edge filter helper treats explicit default values (`comprehensive` / `all`) as no-op success, so future callers do not accidentally drive native filter clicks for default state.
- `/comment` search remains unchanged: it still sends `most_collected` + `one_day` and uses the native filter flow.

## Impact

- Cloud: `comment-scheduler` targeted path and targeted scheduler tests.
- Edge: `applySearchFilters` default-value semantics and focused tests.
- Specs: `curated-note-actions` targeted search requirement.
