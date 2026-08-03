## Context

The slow-start selector row is intentionally visible for an eligible Facebook environment even when slow start is off, because operators must be able to enable it before the browser or account is active. The same row currently contains a static `?` help entry and static curve copy, so row visibility also makes inactive slow-start guidance visible.

The renderer already derives a view from the environment-scoped Cloud response. Its `checked` fact is true only for the last confirmed `active` or `graduated` state; pending feedback is tracked separately and is not authoritative. This provides the required display predicate without adding another API or local state source.

The current help table is hard-coded in Edge markup. Cloud has an editable target-global `slowStart.totalDays` and `slowStart.dailyCaps`, but the customer environment slow-start route exposes only state, total days, and optional current-day quotas. The full configured curve is therefore not available to this renderer today.

## Goals / Non-Goals

**Goals:**

- Keep the selector row available while removing inactive slow-start curve guidance.
- Drive guidance visibility only from the last confirmed Cloud state.
- Preserve honest pending, unknown, error, and cross-environment behavior.

**Non-Goals:**

- Exposing the full global curve through customer-auth or dynamically rebuilding the help table.
- Changing slow-start selection, quota calculation, configuration authority, APIs, or persistence.
- Packaging, installing, or deploying an Edge client.

## Decisions

### 1. Hide both the help entry and the explanatory copy

The `?` entry and the copy describe the same inactive curve behavior, so both are conditional. Hiding only the sentence would still leave an inactive curve explanation reachable and visually imply applicability.

The selector label and radio remain visible. Hiding the whole row was rejected because an off environment must still be able to opt into slow start.

### 2. Use the last confirmed view, not the pending target

Guidance visibility follows `view.checked`, which is derived from a complete Cloud read or write-after-read receipt. While enabling from off is pending, the guidance remains hidden; while disabling from active is pending, it remains visible until Cloud confirms off. This matches the existing non-optimistic contract and avoids making a local click look authoritative.

### 3. Default guidance to hidden and reset it in every unknown path

Both static elements start hidden in markup. A small renderer helper reveals them only from a confirmed active/graduated view and hides them when the row is hidden, loading, or in error. This prevents a previously selected active environment from leaking guidance into a later unknown or off environment.

### 4. Do not claim the help table is backend-linked

This change records but does not conceal the current limitation: the table values are static client content. A later linkage change would need an explicit customer-safe Cloud projection for the whole configured curve, strict Edge decoding, version-skew behavior, and dynamic table rendering. Adding those cross-repo contracts to a conditional-visibility fix was rejected as an unrequested scope expansion.

## Risks / Trade-offs

- [A pending disable still shows the last confirmed guidance] → The pending badge explicitly says Cloud confirmation is outstanding; retaining the confirmed presentation is consistent with the existing non-optimistic selector behavior.
- [The active help table can drift from backend configuration] → Report the boundary explicitly and keep dynamic policy projection as a separate follow-up rather than implying this fix solved it.
- [Focus could remain on a help control that becomes hidden] → Hide the whole help container through the shared `hidden` class so it leaves layout and tab order together.
