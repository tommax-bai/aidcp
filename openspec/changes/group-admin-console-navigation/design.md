## Context

`aidcp-console` currently derives fourteen business links from `APP_ROUTES` and renders all of them in one horizontal pill. CSS attempts to recover space below 1160px by hiding every label, but the flat list still has an unbounded growth model and the icon-only state removes the operator's fastest way to identify destinations. The existing route URLs, boundary-aware active matching, right-side actions, and route/navigation single source must remain intact.

## Goals / Non-Goals

**Goals:**

- Keep a small, stable set of labelled primary groups in the first header row.
- Keep labelled destinations for the current group visible in a second desktop row.
- Keep every destination reachable by label in a grouped narrow-width menu.
- Derive the desktop and narrow navigation from the same route metadata used by the router.
- Preserve current URLs, direct links, nested-route highlighting, and independent header actions.

**Non-Goals:**

- Redesign page content, page-level tabs, authentication, or authorization.
- Add new routes, redirects, APIs, persistence, or dependencies.
- Replace the top header with a permanent sidebar.
- Remember the last visited child within a group.

## Decisions

### Add explicit navigation group metadata to the route source

`APP_ROUTES` will add a `navGroup` field, while a small ordered `NAV_GROUPS` catalog will define each group label, icon, and default destination. The primary group row, current group's secondary row, and narrow menu will all be derived from these structures. Route elements and URLs remain in the same source.

This keeps the existing single-source invariant and makes future growth an explicit placement decision. Duplicating three hand-maintained navigation arrays was rejected because they would drift from the router.

### Use six stable business groups

The information architecture is:

- Overview: Data
- Accounts: Accounts, WeChat Strategy, Facebook Groups
- Content: Content, Curated, Schedule
- Interaction: Interaction Contacts, Notification Routes
- AI Configuration: Persona, Roles
- System: Safety, Usage, Client Users

Settings remains a dedicated right-side action but carries System group metadata so the header retains useful group context on `/settings`.

### Use a persistent second desktop row

The first row contains the brand, six primary groups, and existing actions. A compact second row contains the current group label and all of its destination links. Both active group and active destination are visually distinct.

An overflow "More" menu was rejected because destinations would move in and out of an unpredictable hidden area and the current item could disappear. A permanent sidebar was rejected because it would materially reduce content width and broaden the change beyond the crowded header.

### Replace icon-only collapse with a grouped narrow menu

Below the narrow breakpoint, the two desktop navigation rows are replaced by one labelled trigger that names the current group and destination. Its menu presents all destinations under their six group headings. Brand and independent header actions remain available.

This preserves recognition and keyboard/menu accessibility. Horizontal scrolling and icon-only navigation were rejected because both make destination discovery worse as the list grows.

### Preserve route semantics and boundary matching

Every current path remains unchanged. Active route calculation continues to require either an exact path or a slash boundary, so `/content-schedule` cannot activate `/content`. Nested paths retain their owning destination and group.

## Risks / Trade-offs

- [Risk] The extra desktop row consumes vertical space. → Keep it compact and sticky with the existing header; the predictable 40px cost is preferable to hidden or ambiguous destinations.
- [Risk] A route may be added without group metadata. → Add unit coverage that every visible navigation route belongs to exactly one known group.
- [Risk] The narrow menu can become long over time. → Group headings keep scanning bounded; a future change can add search if the catalog grows substantially beyond the current size.
- [Risk] CSS breakpoints can regress at intermediate widths. → Validate representative desktop, compact desktop, and narrow widths in addition to unit tests and typecheck.

## Migration Plan

1. Add route group metadata and pure active-navigation helpers.
2. Replace the flat header navigation with grouped desktop and narrow surfaces.
3. Add focused tests, typecheck, build, and responsive browser checks.
4. Deploy the rebuilt static assets to `dev` from the clean default checkout.
5. Roll back by restoring the previous console static asset backup if runtime verification fails.

## Open Questions

None.
