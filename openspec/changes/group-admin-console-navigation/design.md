## Context

`aidcp-console` currently derives fourteen business links from `APP_ROUTES` and renders all of them in one horizontal pill. CSS attempts to recover space below 1160px by hiding every label, but the flat list still has an unbounded growth model and the icon-only state removes the operator's fastest way to identify destinations. The existing route URLs, boundary-aware active matching, right-side actions, and route/navigation single source must remain intact.

## Goals / Non-Goals

**Goals:**

- Keep a small, stable set of labelled primary groups in one desktop header row.
- Reveal labelled destinations in a compact floating menu without moving page content or consuming a permanent second row.
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

`APP_ROUTES` will add a `navGroup` field, while a small ordered `NAV_GROUPS` catalog will define each group label and icon. The primary group row, each group's floating menu, and the narrow menu will all be derived from these structures. Route elements and URLs remain in the same source.

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

### Use floating destination menus on desktop

The single header row contains the brand, six primary groups, and existing actions. Overview has one destination and remains a direct link. Each multi-destination group is a labelled button with a subtle chevron; pointer hover or activation opens a compact vertical menu anchored below the group. The menu is an overlay and never changes header height or pushes page content.

The current group remains visibly active when its menu is closed, and the current destination is selected inside the menu. Pointer movement between the trigger and menu has a short close grace period. Click/keyboard activation remains available so access does not depend on hover, and navigation closes the menu. A permanent second row was rejected after visual acceptance because it consumed height and read as a competing top bar. A generic overflow "More" menu was rejected because it hides the information architecture and makes destination placement unpredictable.

Operator visual review found the first floating treatment too close to a mobile card: its 204px centered panel, 42px rows, broad selected slab, and heavy shadow overwhelmed the compact header trigger. The desktop flyout therefore uses a fixed 176px panel aligned to the trigger's left edge, a 6px visual gap and panel inset, 38px rows with 2px separation, 10px outer and 7px row radii, and a lighter border/shadow. Hover and selected fills remain distinct but subtle; the selected destination keeps one small check instead of adding another elevated surface. The trigger chevron rotates while its menu is open, and opening a non-current group uses only a light transient background so interaction state does not masquerade as route state.

### Replace icon-only collapse with a grouped narrow menu

Below the narrow breakpoint, the desktop group strip is replaced by one labelled trigger that names the current group and destination. Its menu presents all destinations under their six group headings. Brand and independent header actions remain available.

This preserves recognition and keyboard/menu accessibility. Horizontal scrolling and icon-only navigation were rejected because both make destination discovery worse as the list grows.

### Preserve route semantics and boundary matching

Every current path remains unchanged. Active route calculation continues to require either an exact path or a slash boundary, so `/content-schedule` cannot activate `/content`. Nested paths retain their owning destination and group.

## Risks / Trade-offs

- [Risk] Hover-only menus can flicker or exclude keyboard/touch users. → Keep a short hover grace period and support click plus keyboard activation on the same semantic button.
- [Risk] A floating menu can obscure a small part of page content while open. → Keep it compact, anchored to its owning group, and close it after navigation or dismissal instead of reserving permanent layout space.
- [Risk] A route may be added without group metadata. → Add unit coverage that every visible navigation route belongs to exactly one known group.
- [Risk] The narrow menu can become long over time. → Group headings keep scanning bounded; a future change can add search if the catalog grows substantially beyond the current size.
- [Risk] CSS breakpoints can regress at intermediate widths. → Validate representative desktop, compact desktop, and narrow widths in addition to unit tests and typecheck.

## Migration Plan

1. Add route group metadata and pure active-navigation helpers.
2. Replace the flat header navigation with grouped desktop floating menus and a labelled narrow surface.
3. Add focused tests, typecheck, build, and responsive browser checks.
4. Deploy the rebuilt static assets to `dev` from the clean default checkout.
5. Roll back by restoring the previous console static asset backup if runtime verification fails.

## Open Questions

None.
