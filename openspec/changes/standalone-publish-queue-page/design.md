## Context

The console already receives a truthful eight-stage lifecycle projection from `GET /api/content/queue` and a server-filtered list of not-yet-started publish tasks from `GET /api/delegated-tasks`. Both are currently rendered at the top of `ContentPage`, above the editorial table and approval modal. The grouped console navigation is route-metadata driven, so a new destination must be registered in that source rather than hand-added to one header surface.

The page split must not turn approval into a queue-side mutation or imply that a queued, authorized, submitted, and platform-confirmed item are equivalent. The Content page remains the system's established place for inspecting and changing candidate content.

## Goals / Non-Goals

**Goals:**

- Make publish operations a first-class destination under the Content group.
- Let an operator answer three questions immediately: how many drafts are active, how many are waiting for a human, and how many tasks have not started.
- Preserve the Cloud lifecycle projection, eight-stage evidence, active/recent separation, and legacy fallback without exposing raw snapshots in the operator UI.
- Keep the Content page focused on candidate approval and published history.
- Keep the layout useful from desktop through narrow widths.

**Non-Goals:**

- Change queue ordering, scheduling, orchestration, lifecycle projection, or delegated-task filtering.
- Add queue mutation, cancellation, reprioritization, or inline draft editing.
- Move the content approval modal or duplicate its CAS authorization behavior.
- Change existing `/content`, Cloud API, protocol, persistence, or risk semantics.

## Decisions

### Register a sibling route in the Content navigation group

Add `/publish-queue` immediately after `/content` in `APP_ROUTES`, labelled “发布队列”. This gives the queue its own direct-linkable destination while retaining the shared router/navigation source. Redirecting `/content` or adding a page-local tab was rejected because the user explicitly wants a separate management destination and the grouped header already provides the correct hierarchy.

### Extract the queue surface behind one page-level owner

The standalone page owns `useContentQueue`, the filtered delegated-task query, account-name resolution, lifecycle selection, and legacy fallback. `ContentPage` no longer issues those queue queries or renders the queue card. Queue rendering helpers remain shared within the queue module rather than reimplementing lifecycle inference.

This prevents two mounted surfaces from polling the same operational data and removes queue concerns from the editorial page.

### Use summary-first, detail-second hierarchy

The page begins with a compact title and explanatory copy, followed by three status tiles:

- Active drafts: lifecycle items still generating, waiting for a human, or dispatching.
- Waiting for human: the active subset whose explicit lifecycle status is `waiting_human`.
- Queued tasks: filtered `queued`, `planning`, or `deferred` publish-family tasks that have not entered lifecycle execution.

Below the summary, a single operational card presents the selected active journey and its eight stages. Queued tasks remain a distinct region and are never presented as pipeline stages. Empty and partial-failure states remain explicit.

### Keep approval as a deliberate handoff to Content

When the selected lifecycle item is waiting for human approval, the queue page exposes a link to `/content?status=pending_approval&candidate=<id>` when a candidate id is supported by current data; otherwise it links to `/content?status=pending_approval`. The Content page reads the status filter and remains the sole owner of editing, approval, and rejection.

The first implementation may use the status-only link if the lifecycle payload lacks a reliable candidate identifier. Inventing a candidate mapping from record order or title was rejected as dishonest.

### Group active work by account before task detail

Replace the task-level Select with a horizontal account strip. Each selector item displays only the resolved account name; it does not mix titles or lifecycle status into account navigation. The strip uses native horizontal overflow so desktop trackpads, mouse-wheel shift scrolling, and mobile touch swipes can reach accounts beyond the viewport.

The content region below renders every active journey owned by the selected account, in lifecycle order, rather than hiding sibling tasks behind another selector. The queued-task panel remains a separate single region and MUST NOT be repeated once per active journey.

### Preserve compatibility while removing raw disclosure

The page prefers `lifecycle` when present and retains the existing `runs`/`snapshot` fallback for older Cloud deployments. Raw snapshot fields are implementation diagnostics and are no longer rendered in either path. No summary count may be inferred from raw field presence when explicit lifecycle data exists.

## Risks / Trade-offs

- [Risk] Adding a fourth Content destination increases secondary-navigation width. → Keep the concise “发布队列” label and verify grouped desktop plus narrow-menu layouts.
- [Risk] Operators may expect approval inline on the queue page. → Use clear “去内容页审批” handoff copy and keep authorization in one place.
- [Risk] Queue and Content queries refresh independently after navigation. → Both use existing React Query keys; candidate mutations already invalidate content and queue truth.
- [Risk] Older Cloud responses cannot provide exact waiting-human counts. → Display evidence available from the legacy surface without fabricating lifecycle counts.
- [Risk] One account can have many simultaneous journeys, producing a tall detail region. → Keep each journey visually bounded and stack them directly; do not add a second hidden task selector that would make concurrent work easy to miss.

## Migration Plan

1. Register the route and extract the queue-owned data/rendering surface.
2. Remove queue rendering and polling from `ContentPage`; preserve the existing content route and approval modal.
3. Add route, separation, summary, lifecycle, empty, and responsive tests; run typecheck and production build.
4. Validate OpenSpec, integrate to the console default branch, and deploy static assets to `dev` from the clean canonical checkout.
5. Roll back by restoring the previous console static-asset backup; no Cloud or data rollback is required.

## Open Questions

None.
